using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace WebWalls;

/// <summary>One borderless window per monitor, glued behind the desktop icons, running a WebView2.</summary>
internal sealed class WallpaperWindow : Form
{
    private const string Host = "wall.webwalls";

    // Injected into every wallpaper: lets us pause / cap FPS on ANY HTML file without it knowing.
    private const string Shim = """
        (() => {
          if (window.__webwalls) return;
          const raf = window.requestAnimationFrame.bind(window);
          let queue = new Map(), nextId = 0, last = 0;
          const st = { paused: false, fps: 0, scale: 1 };
          // Render-resolution control: pages size their canvas from devicePixelRatio, so scaling it down
          // makes them draw fewer pixels (the browser stretches the result to fill the screen).
          const dprDesc = Object.getOwnPropertyDescriptor(window, 'devicePixelRatio') ||
                          Object.getOwnPropertyDescriptor(Window.prototype, 'devicePixelRatio');
          const realDpr = () => { try { return (dprDesc && dprDesc.get ? dprDesc.get.call(window) : 1) || 1; } catch (e) { return 1; } };
          try { Object.defineProperty(window, 'devicePixelRatio', { configurable: true, get: () => realDpr() * st.scale }); } catch (e) {}
          function pump(t) {
            raf(pump);
            if (st.paused) return;
            if (st.fps > 0 && t - last < 1000 / st.fps - 1) return;
            last = t;
            const cbs = queue; queue = new Map();
            cbs.forEach(cb => { try { cb(t); } catch (e) { console.error(e); } });
          }
          raf(pump);
          window.requestAnimationFrame = cb => { queue.set(++nextId, cb); return nextId; };
          window.cancelAnimationFrame = id => { queue.delete(id); };
          st.set = (paused, fps, scale) => {
            st.paused = paused; st.fps = fps;
            const s = scale > 0 ? scale : 1;
            if (Math.abs(s - st.scale) > 0.001) { st.scale = s; window.dispatchEvent(new Event('resize')); }
            document.documentElement.classList.toggle('webwalls-paused', paused);
            document.querySelectorAll('video,audio').forEach(v => paused ? v.pause() : v.play().catch(() => {}));
            try { document.getAnimations().forEach(a => paused ? a.pause() : a.play()); } catch (e) {}
            window.dispatchEvent(new CustomEvent('webwalls', { detail: { paused, fps, scale: st.scale } }));
          };
          window.__webwalls = st;
        })();
        """;

    private static Task<CoreWebView2Environment>? _env;

    private readonly WebView2 _web = new();
    private readonly Rectangle _bounds;
    private string? _path;
    private bool _paused, _deepPaused, _muted = true;
    private int _fps;
    private double _scale = 1;

    public Screen Screen { get; }

    private readonly string _screenInfo;

    public WallpaperWindow(Screen screen, int index, int count)
    {
        Screen = screen;
        var b = screen.Bounds;
        double aspect = (double)b.Width / Math.Max(1, b.Height);
        // 32:9 super-ultrawides (5120x1440, 3840x1080) are ~3.56; 21:9 is ~2.37.
        string shape = aspect >= 3.0 ? "superultrawide" : aspect >= 2.1 ? "ultrawide" : aspect < 1.0 ? "portrait" : "wide";
        // Tells the wallpaper what kind of screen it's on (optional for wallpaper makers to use):
        //   window.__webwalls.screen = { index, count, width, height, aspect, shape, primary }
        //   + a class on <html>: ww-superultrawide (+ ww-ultrawide) / ww-ultrawide / ww-wide / ww-portrait
        _screenInfo = "(() => { const s = { index: " + index + ", count: " + count +
            ", width: " + b.Width + ", height: " + b.Height +
            ", aspect: " + aspect.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture) +
            ", shape: '" + shape + "', primary: " + (screen.Primary ? "true" : "false") + " };" +
            " if (window.__webwalls) window.__webwalls.screen = s;" +
            " const tag = () => { const h = document.documentElement; if (!h) return; h.classList.add('ww-' + s.shape); if (s.shape === 'superultrawide') h.classList.add('ww-ultrawide'); };" +
            " tag(); addEventListener('DOMContentLoaded', tag); })();";
        _bounds = screen.Bounds;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        Bounds = _bounds;
        BackColor = Color.Black;
        Text = "web.walls";

        _web.Dock = DockStyle.Fill;
        _web.DefaultBackgroundColor = Color.Black;
        Controls.Add(_web);
    }

    protected override CreateParams CreateParams
    {
        get
        {
            var cp = base.CreateParams;
            cp.ExStyle |= (int)(Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE);
            return cp;
        }
    }

    protected override bool ShowWithoutActivation => true;

    public async Task StartAsync()
    {
        Show();
        DesktopHost.Attach(Handle, _bounds);

        _env ??= CoreWebView2Environment.CreateAsync(
            null,
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "WebWalls", "WebView2"),
            new CoreWebView2EnvironmentOptions("--autoplay-policy=no-user-gesture-required --disable-features=msSmartScreenProtection"));

        await _web.EnsureCoreWebView2Async(await _env);
        var core = _web.CoreWebView2;
        core.Settings.AreDefaultContextMenusEnabled = false;
        core.Settings.AreDevToolsEnabled = false;
        core.Settings.IsStatusBarEnabled = false;
        core.Settings.IsZoomControlEnabled = false;
        core.Settings.AreBrowserAcceleratorKeysEnabled = false;
        core.IsMuted = _muted;
        core.NewWindowRequested += (_, e) => e.Handled = true; // no popups on the desktop, ever
        core.NavigationCompleted += async (_, _) => await PushStateAsync();
        await core.AddScriptToExecuteOnDocumentCreatedAsync(Shim);
        await core.AddScriptToExecuteOnDocumentCreatedAsync(_screenInfo);

        if (_path != null) Navigate(_path);
    }

    /// <summary>Re-glue after Explorer restarts or the screen layout changes.</summary>
    public void Reattach() => DesktopHost.Attach(Handle, _bounds);

    public void LoadWallpaper(string path)
    {
        _path = path;
        if (_web.CoreWebView2 != null) Navigate(path);
    }

    public void Reload() => _web.CoreWebView2?.Reload();

    private void Navigate(string path)
    {
        var core = _web.CoreWebView2;
        string full = Path.GetFullPath(path);
        string dir = Path.GetDirectoryName(full)!;
        // Serve the wallpaper's folder over a fake https host so relative images/scripts/videos just work.
        try { core.ClearVirtualHostNameToFolderMapping(Host); } catch { }
        core.SetVirtualHostNameToFolderMapping(Host, dir, CoreWebView2HostResourceAccessKind.Allow);
        core.Navigate($"https://{Host}/{Uri.EscapeDataString(Path.GetFileName(full))}");
    }

    public void SetMuted(bool muted)
    {
        _muted = muted;
        if (_web.CoreWebView2 != null) _web.CoreWebView2.IsMuted = muted;
    }

    /// <summary>
    /// paused = freeze the animation. deep = also hide + suspend the browser (frees GPU/CPU; used while gaming
    /// or on battery-pause, when nobody's looking at the desktop anyway).
    /// </summary>
    public async Task SetStateAsync(bool paused, bool deep, int fps, double scale)
    {
        _paused = paused;
        _fps = fps;
        _scale = scale;
        if (_web.CoreWebView2 == null) return;

        if (deep && !_deepPaused)
        {
            _deepPaused = true;
            await PushStateAsync();
            await FreezeFrameAsync();   // show the last frame instead of black while the browser sleeps
            _web.Visible = false;
            try { await _web.CoreWebView2.TrySuspendAsync(); } catch { }
        }
        else if (!deep && _deepPaused)
        {
            _deepPaused = false;
            try { _web.CoreWebView2.Resume(); } catch { }
            _web.Visible = true;
            ClearFreezeFrame();
            await PushStateAsync();
        }
        else if (!_deepPaused)
        {
            await PushStateAsync();
        }
    }

    /// <summary>Snapshot the wallpaper onto the window itself, so hiding the browser leaves a still picture, not black.</summary>
    private async Task FreezeFrameAsync()
    {
        try
        {
            using var ms = new MemoryStream();
            await _web.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Jpeg, ms);
            ms.Position = 0;
            using var img = Image.FromStream(ms);
            var old = BackgroundImage;
            BackgroundImage = new Bitmap(img);
            BackgroundImageLayout = ImageLayout.Stretch;
            old?.Dispose();
        }
        catch { /* worst case it's black, like before */ }
    }

    private void ClearFreezeFrame()
    {
        var old = BackgroundImage;
        BackgroundImage = null;
        old?.Dispose();
    }

    private async Task PushStateAsync()
    {
        if (_web.CoreWebView2 == null) return;
        string p = _paused ? "true" : "false";
        string s = _scale.ToString("0.###", System.Globalization.CultureInfo.InvariantCulture);
        try { await _web.CoreWebView2.ExecuteScriptAsync($"window.__webwalls && window.__webwalls.set({p}, {_fps}, {s})"); }
        catch { }
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing) _web.Dispose();
        base.Dispose(disposing);
    }
}

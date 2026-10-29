using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using Microsoft.Win32;

namespace WebWalls;

/// <summary>Lives in the system tray, owns the wallpaper windows, decides when to pause.</summary>
internal sealed class TrayApp : ApplicationContext
{
    private readonly Settings _settings = Settings.Load();
    private readonly NotifyIcon _tray = new();
    private readonly List<WallpaperWindow> _windows = new();
    private readonly System.Windows.Forms.Timer _watchdog = new() { Interval = 1500 };
    // Self-healing: re-glue anything Windows knocked loose, reload anything that died.
    private readonly System.Windows.Forms.Timer _health = new() { Interval = 5000 };
    private int _healthTicks;
    // Plugging in a monitor or rotating the laptop fires a burst of display events: wait for it to settle.
    private readonly System.Windows.Forms.Timer _displayDebounce = new() { Interval = 1200 };
    private string _layoutSig = "";
    private bool _rebuilding, _pendingRebuild;
    private readonly Control _ui = new();
    private readonly ShellWatcher _shell;
    private readonly EventWaitHandle _quitEvent = new(false, EventResetMode.AutoReset, Program.QuitEventName);

    private bool _manualPause;
    private bool _manualGaming;
    private GameInfo? _game;
    private string _gameKey = "";
    private int _gameStreak;
    private string? _lastSig;

    public TrayApp()
    {
        _ = _ui.Handle; // force a real window handle so BeginInvoke works
        Gallery.Unpack();
        StartMenu.Ensure();   // shows up under All apps with the neon W

        _tray.Icon = LoadIcon();
        _tray.Text = "web.walls";
        _tray.Visible = true;
        _tray.ContextMenuStrip = new ContextMenuStrip();
        _tray.ContextMenuStrip.Opening += (_, _) => BuildMenu();
        _tray.DoubleClick += (_, _) => TogglePause();
        BuildMenu();

        // Explorer restarted -> our windows went down with it. Give it a sec, then rebuild.
        _shell = new ShellWatcher(() => _ui.BeginInvoke(new Action(async () =>
        {
            await Task.Delay(1500);
            await RebuildWindowsAsync();
        })));
        SystemEvents.DisplaySettingsChanged += (_, _) => _ui.BeginInvoke(new Action(() =>
        {
            _displayDebounce.Stop();
            _displayDebounce.Start();
        }));
        _displayDebounce.Tick += async (_, _) =>
        {
            _displayDebounce.Stop();
            if (_pendingRebuild || LayoutSig() != _layoutSig) { _pendingRebuild = false; await RebuildWindowsAsync(); }   // monitor added/removed/rotated/resized
            else foreach (var w in _windows) w.Reattach();                // same layout, just re-glue
        };
        // Start with Windows: the app's own setting is the boss. Every launch, put the startup entry back if
        // something removed it (an old installer choice, a cleanup tool, Task Manager) and point it at this exe.
        EnsureStartup();
        SystemEvents.PowerModeChanged += (_, e) => _ui.BeginInvoke(new Action(async () =>
        {
            await EvaluateAsync(force: true);
            if (e.Mode == PowerModes.Resume) await HealSoonAsync("woke from sleep");
        }));
        // Theme / wallpaper / Spotlight changes make Windows rebuild the desktop layers.
        SystemEvents.UserPreferenceChanged += (_, e) =>
        {
            if (e.Category is UserPreferenceCategory.Desktop or UserPreferenceCategory.VisualStyle)
                _ui.BeginInvoke(new Action(async () => await HealSoonAsync("theme/wallpaper changed")));
        };
        SystemEvents.SessionSwitch += (_, e) =>
        {
            if (e.Reason is SessionSwitchReason.SessionUnlock or SessionSwitchReason.ConsoleConnect or SessionSwitchReason.RemoteConnect)
                _ui.BeginInvoke(new Action(async () => await HealSoonAsync("unlocked")));
        };
        _health.Tick += async (_, _) => await HealthTickAsync();
        _health.Start();

        // Installer / uninstaller asks us to leave ("WebWalls.exe --quit").
        ThreadPool.RegisterWaitForSingleObject(_quitEvent, (_, _) => _ui.BeginInvoke(new Action(ExitApp)), null, -1, true);

        _watchdog.Tick += async (_, _) => await EvaluateAsync();
        _watchdog.Start();

        _ui.BeginInvoke(new Action(async () =>
        {
            await RebuildWindowsAsync();
            _settings.Save();   // writes StartWithWindows=true into older settings files
            if (_settings.CurrentWallpaper == null)
                _tray.ShowBalloonTip(4000, "web.walls is running",
                    "Right-click the tray icon to pick a wallpaper.", ToolTipIcon.Info);
        }));
    }

    // ---------------------------------------------------------------- windows

    /// <summary>Fingerprint of the monitor layout: which screens, where, how big, which way up.</summary>
    private static string LayoutSig() =>
        string.Join("|", Screen.AllScreens.Select(s => $"{s.DeviceName}:{s.Bounds}:{s.Primary}"));

    /// <summary>Screens in a stable left-to-right, top-to-bottom order so "Display 1/2" match how they sit on the desk.</summary>
    private static Screen[] OrderedScreens() =>
        Screen.AllScreens.OrderBy(s => s.Bounds.Left).ThenBy(s => s.Bounds.Top).ToArray();

    private bool IsShown(Screen s) =>
        !_settings.HiddenScreens.Contains(s.DeviceName, StringComparer.OrdinalIgnoreCase);

    private async Task RebuildWindowsAsync()
    {
        if (_rebuilding) { _pendingRebuild = true; _displayDebounce.Stop(); _displayDebounce.Start(); return; }   // try again once this one's done
        _rebuilding = true;
        try { await RebuildWindowsCoreAsync(); }
        finally { _rebuilding = false; }
    }

    private async Task RebuildWindowsCoreAsync()
    {
        foreach (var w in _windows) { try { w.Close(); w.Dispose(); } catch { } }
        _windows.Clear();
        _lastSig = null;
        _layoutSig = LayoutSig();

        string? path = CurrentPath();
        if (path == null) return;

        var screens = OrderedScreens();
        // Same wallpaper on every screen; each screen gets its own copy sized to its own shape
        // (ultrawide, 16:9, portrait...), so scenes reflow instead of stretching across the gap.
        for (int i = 0; i < screens.Length; i++)
        {
            var screen = screens[i];
            if (!IsShown(screen)) continue;
            var w = new WallpaperWindow(screen, i, screens.Length);
            w.BrowserDied += OnBrowserDied;
            w.SetMuted(_settings.Muted);
            w.LoadWallpaper(path);
            _windows.Add(w);
            try
            {
                await w.StartAsync();
            }
            catch (Microsoft.Web.WebView2.Core.WebView2RuntimeNotFoundException)
            {
                MessageBox.Show("The Microsoft Edge WebView2 Runtime is missing.\n\nGrab it from:\nhttps://go.microsoft.com/fwlink/p/?LinkId=2124703",
                    "web.walls", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                ExitApp();
                return;
            }
        }
        await EvaluateAsync(force: true);
    }

    private string? CurrentPath()
    {
        var p = _settings.CurrentWallpaper;
        if (p != null && File.Exists(p)) return p;
        var first = Gallery.BuiltIns().FirstOrDefault();
        if (first == null) return null;
        _settings.CurrentWallpaper = first.Path;
        _settings.Save();
        return first.Path;
    }

    private async Task SetWallpaperAsync(string path)
    {
        _settings.CurrentWallpaper = path;
        _settings.Save();
        if (_windows.Count == 0) { await RebuildWindowsAsync(); return; }
        foreach (var w in _windows) w.LoadWallpaper(path);
        _lastSig = null;
        await EvaluateAsync(force: true);
    }

    // ---------------------------------------------------------------- self-healing

    private async Task HealSoonAsync(string why)
    {
        // Windows takes a moment to finish rebuilding the desktop; check a few times as it settles.
        foreach (int ms in new[] { 700, 2000, 5000 })
        {
            await Task.Delay(ms);
            HealAttachment(why);
        }
    }

    private void HealAttachment(string why)
    {
        if (_rebuilding) return;
        foreach (var w in _windows.ToList())
        {
            string? what = w.EnsureAttached();
            if (what != null) Diary.Log($"{w.Screen.DeviceName}: re-glued behind icons ({what}; {why})");
        }
    }

    private async Task HealthTickAsync()
    {
        if (_rebuilding || _windows.Count == 0) return;
        HealAttachment("check");
        // Page heartbeat every ~20 s.
        if (++_healthTicks % 4 != 0) return;
        foreach (var w in _windows.ToList()) await w.CheckHealthAsync();
    }

    private void OnBrowserDied(WallpaperWindow w, string why)
    {
        Diary.Log($"{w.Screen.DeviceName}: browser died ({why}), rebuilding");
        _ = RebuildWindowsAsync();
    }

    // ---------------------------------------------------------------- pause brain

    private async Task EvaluateAsync(bool force = false)
    {
        bool onBattery = SystemInformation.PowerStatus.PowerLineStatus == PowerLineStatus.Offline;

        // Who's gaming, and on which screen? (needs ~3s of agreement before switching, so it never flickers)
        GameInfo? raw = _settings.PauseWhenFullscreen ? GameDetector.Detect(_settings.GameExes) : null;
        if (raw == null && _manualGaming) raw = new GameInfo(Rectangle.Empty, false, null);
        string key = raw == null ? "" : $"{raw.Monitor}|{raw.Covers}|{raw.Exe}";
        if (key == _gameKey) _gameStreak++; else { _gameKey = key; _gameStreak = 1; }
        if (_gameStreak >= 2) _game = raw;

        bool batteryPause = onBattery && _settings.OnBattery == BatteryMode.Pause;
        int baseFps = _settings.FpsCap;
        if (onBattery && _settings.OnBattery == BatteryMode.Cap30) baseFps = baseFps == 0 ? 30 : Math.Min(baseFps, 30);
        double baseScale = _settings.RenderScale is > 0.1 and <= 1 ? _settings.RenderScale : 1;

        var plan = new List<(WallpaperWindow w, bool paused, bool deep, int fps, double scale)>();
        foreach (var w in _windows)
        {
            bool deep = batteryPause;                 // nobody's looking -> fully suspend
            bool paused = deep || _manualPause;       // manual pause just freezes the frame
            int fps = baseFps;
            double scale = baseScale;

            if (_game != null)
            {
                bool gameScreen = _game.Covers && w.Screen.Bounds == _game.Monitor;
                if (gameScreen) { deep = true; paused = true; }   // hidden behind the game: sleep it completely
                else switch (_settings.WhileGaming)
                {
                    case GamingMode.Lighter:
                        fps = fps == 0 ? 30 : Math.Min(fps, 30);
                        scale = Math.Min(scale, 0.5);
                        break;
                    case GamingMode.Freeze:
                        paused = true;
                        break;
                }
            }
            plan.Add((w, paused, deep, fps, scale));
        }

        string sig = string.Join(";", plan.Select(p => $"{p.paused}{p.deep}{p.fps}{p.scale}"));
        if (!force && sig == _lastSig) return;
        _lastSig = sig;

        foreach (var p in plan) await p.w.SetStateAsync(p.paused, p.deep, p.fps, p.scale);

        string fpsText = baseFps == 0 ? "unlimited" : baseFps + " fps";
        string text = _game != null ? $"web.walls (gaming{(_game.Exe != null ? ": " + Path.GetFileNameWithoutExtension(_game.Exe) : "")})"
            : batteryPause ? "web.walls (paused on battery)"
            : _manualPause ? "web.walls (paused)"
            : $"web.walls ({fpsText})";
        _tray.Text = text.Length > 63 ? text[..63] : text;   // tray tooltips max out at 63 chars
    }

    private void TogglePause()
    {
        _manualPause = !_manualPause;
        _ = EvaluateAsync(force: true);
    }

    // ---------------------------------------------------------------- tray menu

    private void BuildMenu()
    {
        var menu = _tray.ContextMenuStrip!;
        menu.Items.Clear();

        menu.Items.Add(new ToolStripMenuItem("web.walls") { Enabled = false, Font = new Font(menu.Font, FontStyle.Bold) });
        menu.Items.Add(new ToolStripSeparator());

        // Wallpapers
        var walls = new ToolStripMenuItem("Wallpapers");
        foreach (var item in Gallery.BuiltIns())
            walls.DropDownItems.Add(WallItem(item.Name, item.Path));

        var custom = _settings.CustomWallpapers.Where(File.Exists).ToList();
        if (custom.Count > 0)
        {
            walls.DropDownItems.Add(new ToolStripSeparator());
            walls.DropDownItems.Add(new ToolStripMenuItem("My wallpapers") { Enabled = false });
            foreach (var p in custom) walls.DropDownItems.Add(WallItem(Gallery.NameOf(p), p));
        }
        walls.DropDownItems.Add(new ToolStripSeparator());
        walls.DropDownItems.Add("Load my own HTML…", null, (_, _) => LoadCustom());
        if (custom.Count > 0)
            walls.DropDownItems.Add("Forget my wallpapers", null, (_, _) => { _settings.CustomWallpapers.Clear(); _settings.Save(); });
        walls.DropDownItems.Add("Open gallery folder", null, (_, _) =>
            System.Diagnostics.Process.Start("explorer.exe", Gallery.Folder));
        menu.Items.Add(walls);

        menu.Items.Add(BuildDisplaysMenu());
        menu.Items.Add(new ToolStripMenuItem(_manualPause ? "Resume" : "Pause", null, (_, _) => TogglePause()));
        menu.Items.Add("Reload wallpaper", null, (_, _) => { foreach (var w in _windows) w.Reload(); });
        menu.Items.Add("Show fix log", null, (_, _) =>
        {
            string log = Path.Combine(Settings.Folder, "events.log");
            if (!File.Exists(log)) { Directory.CreateDirectory(Settings.Folder); File.WriteAllText(log, "Nothing fixed yet.\n"); }
            System.Diagnostics.Process.Start("notepad.exe", log);
        });
        menu.Items.Add(new ToolStripSeparator());

        // Performance
        var perf = new ToolStripMenuItem("Performance");
        var fpsMenu = new ToolStripMenuItem("Frame rate");
        foreach (var (label, val) in new[] { ("Unlimited (match screen)", 0), ("240 FPS", 240), ("144 FPS", 144), ("120 FPS", 120), ("60 FPS", 60), ("30 FPS", 30), ("15 FPS (potato mode)", 15) })
            fpsMenu.DropDownItems.Add(Check(label, _settings.FpsCap == val, () => _settings.FpsCap = val));
        perf.DropDownItems.Add(fpsMenu);

        var battMenu = new ToolStripMenuItem("On battery");
        battMenu.DropDownItems.Add(Check("Keep going full send", _settings.OnBattery == BatteryMode.KeepGoing, () => _settings.OnBattery = BatteryMode.KeepGoing));
        battMenu.DropDownItems.Add(Check("Cap at 30 FPS", _settings.OnBattery == BatteryMode.Cap30, () => _settings.OnBattery = BatteryMode.Cap30));
        battMenu.DropDownItems.Add(Check("Pause", _settings.OnBattery == BatteryMode.Pause, () => _settings.OnBattery = BatteryMode.Pause));
        perf.DropDownItems.Add(battMenu);

        var quality = new ToolStripMenuItem("Quality");
        foreach (var (label, val) in new[] { ("Full (sharpest)", 1.0), ("Balanced (75% resolution)", 0.75), ("Performance (half resolution)", 0.5) })
            quality.DropDownItems.Add(Check(label, Math.Abs(_settings.RenderScale - val) < 0.01, () => _settings.RenderScale = val));
        perf.DropDownItems.Add(quality);

        perf.DropDownItems.Add(new ToolStripSeparator());
        perf.DropDownItems.Add(BuildGamingMenu());
        perf.DropDownItems.Add(Check("Mute wallpaper sound", _settings.Muted, () =>
        {
            _settings.Muted = !_settings.Muted;
            foreach (var w in _windows) w.SetMuted(_settings.Muted);
        }));
        menu.Items.Add(perf);

        menu.Items.Add(Check("Start with Windows", _settings.StartWithWindows, () =>
        {
            _settings.StartWithWindows = !_settings.StartWithWindows;
            EnsureStartup();
        }));
        menu.Items.Add(new ToolStripSeparator());
        menu.Items.Add("Quit", null, (_, _) => ExitApp());
    }

    /// <summary>Gaming ▸ how screens behave while you play, plus teaching web.walls which apps are games.</summary>
    private ToolStripMenuItem BuildGamingMenu()
    {
        var g = new ToolStripMenuItem(_game != null ? "Gaming (game detected)" : "Gaming");
        g.DropDownItems.Add(Check("Detect games automatically", _settings.PauseWhenFullscreen,
            () => _settings.PauseWhenFullscreen = !_settings.PauseWhenFullscreen));
        g.DropDownItems.Add(Check("Gaming mode on right now (manual)", _manualGaming, () => _manualGaming = !_manualGaming));
        g.DropDownItems.Add(new ToolStripSeparator());
        g.DropDownItems.Add(new ToolStripMenuItem("The game's screen always sleeps. Other screens:") { Enabled = false });
        g.DropDownItems.Add(Check("Lighter: 30 FPS, half resolution", _settings.WhileGaming == GamingMode.Lighter, () => _settings.WhileGaming = GamingMode.Lighter));
        g.DropDownItems.Add(Check("Freeze (still frame)", _settings.WhileGaming == GamingMode.Freeze, () => _settings.WhileGaming = GamingMode.Freeze));
        g.DropDownItems.Add(Check("Full quality", _settings.WhileGaming == GamingMode.Full, () => _settings.WhileGaming = GamingMode.Full));
        g.DropDownItems.Add(new ToolStripSeparator());

        string? last = GameDetector.LastForeignExe;
        if (last != null && !_settings.GameExes.Contains(last, StringComparer.OrdinalIgnoreCase))
            g.DropDownItems.Add(new ToolStripMenuItem($"Treat \"{last}\" as a game", null, (_, _) =>
            {
                _settings.GameExes.Add(last);
                _settings.Save();
            }));
        foreach (var exe in _settings.GameExes.ToList())
            g.DropDownItems.Add(new ToolStripMenuItem($"{exe}  (click to forget)", null, (_, _) =>
            {
                _settings.GameExes.RemoveAll(e => string.Equals(e, exe, StringComparison.OrdinalIgnoreCase));
                _settings.Save();
            }) { Checked = true });
        return g;
    }

    /// <summary>Displays ▸ tick which monitors get the wallpaper (all of them by default).</summary>
    private ToolStripMenuItem BuildDisplaysMenu()
    {
        var screens = OrderedScreens();
        var menu = new ToolStripMenuItem($"Displays ({screens.Count(IsShown)} of {screens.Length} on)");
        for (int i = 0; i < screens.Length; i++)
        {
            var s = screens[i];
            var b = s.Bounds;
            double aspect = (double)b.Width / Math.Max(1, b.Height);
            string shape = aspect >= 2.1 ? ", ultrawide" : aspect < 1.0 ? ", portrait" : "";
            string label = $"Display {i + 1}: {b.Width}×{b.Height}{shape}{(s.Primary ? " (main)" : "")}";
            bool shown = IsShown(s);
            string dev = s.DeviceName;
            menu.DropDownItems.Add(new ToolStripMenuItem(label, null, async (_, _) =>
            {
                if (shown) _settings.HiddenScreens.Add(dev);
                else _settings.HiddenScreens.RemoveAll(d => string.Equals(d, dev, StringComparison.OrdinalIgnoreCase));
                _settings.Save();
                await RebuildWindowsAsync();
            }) { Checked = shown });
        }
        menu.DropDownItems.Add(new ToolStripSeparator());
        menu.DropDownItems.Add("Show on all displays", null, async (_, _) =>
        {
            _settings.HiddenScreens.Clear();
            _settings.Save();
            await RebuildWindowsAsync();
        });
        return menu;
    }

    private ToolStripMenuItem WallItem(string name, string path)
    {
        bool current = string.Equals(_settings.CurrentWallpaper, path, StringComparison.OrdinalIgnoreCase);
        return new ToolStripMenuItem(name, null, async (_, _) => await SetWallpaperAsync(path)) { Checked = current };
    }

    private ToolStripMenuItem Check(string label, bool isChecked, Action apply) =>
        new(label, null, (_, _) =>
        {
            apply();
            _settings.Save();
            _ = EvaluateAsync(force: true);
        }) { Checked = isChecked };

    private async void LoadCustom()
    {
        using var dlg = new OpenFileDialog
        {
            Title = "Pick an HTML wallpaper",
            Filter = "HTML wallpapers (*.html;*.htm)|*.html;*.htm",
        };
        if (dlg.ShowDialog() != DialogResult.OK) return;
        string path = dlg.FileName;
        if (!_settings.CustomWallpapers.Contains(path, StringComparer.OrdinalIgnoreCase))
            _settings.CustomWallpapers.Add(path);
        await SetWallpaperAsync(path);
    }

    // ---------------------------------------------------------------- startup + exit

    private const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";

    // Task Manager's Startup tab on/off switch lives here (first byte 2 = on, 3 = off).
    private const string ApprovedKey = @"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run";

    private void EnsureStartup()
    {
        try
        {
            using var run = Registry.CurrentUser.CreateSubKey(RunKey);
            using var ok = Registry.CurrentUser.CreateSubKey(ApprovedKey);
            if (_settings.StartWithWindows)
            {
                string want = $"\"{Environment.ProcessPath}\"";
                if (!string.Equals(run.GetValue("WebWalls") as string, want, StringComparison.OrdinalIgnoreCase))
                {
                    run.SetValue("WebWalls", want);
                    Diary.Log("start with Windows: startup entry was missing or stale, put it back");
                }
                if (ok.GetValue("WebWalls") is byte[] b && b.Length > 0 && b[0] % 2 == 1)   // switched off in Task Manager
                {
                    ok.SetValue("WebWalls", new byte[12] { 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }, RegistryValueKind.Binary);
                    Diary.Log("start with Windows: was switched off in Task Manager, switched it back on");
                }
            }
            else
            {
                run.DeleteValue("WebWalls", false);
            }
        }
        catch (Exception ex) { Diary.Log("start with Windows: couldn't set it (" + ex.Message + ")"); }
    }

    private void ExitApp()
    {
        _watchdog.Stop();
        _displayDebounce.Stop();
        foreach (var w in _windows) { w.Close(); w.Dispose(); }
        _windows.Clear();
        _shell.DestroyHandle();
        _tray.Visible = false;
        _tray.Dispose();
        DesktopHost.RestoreStockWallpaper();
        ExitThread();
    }

    // ---------------------------------------------------------------- icon

    /// <summary>Same neon W as the exe icon, at the right size for this screen's tray.</summary>
    private static Icon LoadIcon()
    {
        try
        {
            using var s = typeof(TrayApp).Assembly.GetManifestResourceStream("app.ico");
            if (s != null) return new Icon(s, SystemInformation.SmallIconSize);
        }
        catch { }
        return MakeIcon();
    }

    private static Icon MakeIcon()
    {
        using var bmp = new Bitmap(32, 32);
        using (var g = Graphics.FromImage(bmp))
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Color.Transparent);
            using var bg = new LinearGradientBrush(new Rectangle(0, 0, 32, 32), Color.FromArgb(255, 20, 10, 40), Color.FromArgb(255, 40, 0, 60), 45f);
            g.FillEllipse(bg, 1, 1, 30, 30);
            using var pen = new LinearGradientBrush(new Rectangle(0, 0, 32, 32), Color.FromArgb(255, 0, 255, 230), Color.FromArgb(255, 255, 40, 200), 0f);
            using var p = new Pen(pen, 3.2f) { LineJoin = LineJoin.Round, StartCap = LineCap.Round, EndCap = LineCap.Round };
            g.DrawLines(p, new[] { new PointF(6, 9), new PointF(11, 23), new PointF(16, 13), new PointF(21, 23), new PointF(26, 9) });
        }
        return Icon.FromHandle(bmp.GetHicon());
    }

    /// <summary>Hears "TaskbarCreated", which fires when Explorer restarts and nukes our desktop layer.</summary>
    private sealed class ShellWatcher : NativeWindow
    {
        private readonly uint _taskbarCreated = Native.RegisterWindowMessage("TaskbarCreated");
        private readonly Action _onRestart;

        public ShellWatcher(Action onRestart)
        {
            _onRestart = onRestart;
            CreateHandle(new CreateParams { Caption = "webwalls-shell-watcher" });
        }

        protected override void WndProc(ref Message m)
        {
            if ((uint)m.Msg == _taskbarCreated) _onRestart();
            base.WndProc(ref m);
        }
    }
}

using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32;

namespace WebWalls;

/// <summary>What the detector saw this tick.</summary>
/// <param name="Monitor">Screen bounds the game sits on (physical pixels), or null if no game.</param>
/// <param name="Covers">True if the game fills (most of) that screen, so its wallpaper can't be seen anyway.</param>
/// <param name="Exe">File name of the game, for the tray tooltip.</param>
internal sealed record GameInfo(Rectangle Monitor, bool Covers, string? Exe);

/// <summary>
/// Spots games, including windowed / maximized ones. A window counts as a game when:
///  - it's real fullscreen (no title bar, covers its screen), or Windows says a D3D fullscreen game is running; or
///  - it's the foreground app and its exe is a known game: installed by Steam / Epic / GOG / Xbox / EA / Ubisoft /
///    Riot / Battle.net, flagged as a game by Windows Game Bar, or marked as a game by you from the tray.
/// A maximized browser has a title bar and isn't a known game, so it never trips this (no flicker).
/// </summary>
internal static class GameDetector
{
    private static readonly string[] StoreFolders =
    {
        @"\steamapps\common\", @"\epic games\", @"\gog galaxy\games\", @"\gog games\", @"\xboxgames\",
        @"\ea games\", @"\electronic arts\", @"\ubisoft game launcher\games\", @"\riot games\",
        @"\battle.net\", @"\blizzard\", @"\rockstar games\", @"\itch\apps\",
    };

    // Launchers / stores themselves aren't games, even though they live in game folders.
    private static readonly HashSet<string> NotGames = new(StringComparer.OrdinalIgnoreCase)
    {
        "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe", "galaxyclient.exe", "eadesktop.exe",
        "upc.exe", "ubisoftconnect.exe", "riotclientux.exe", "riotclientservices.exe", "battle.net.exe",
        "xboxpcapp.exe", "gamebar.exe", "explorer.exe", "msedge.exe", "chrome.exe", "firefox.exe",
        "msedgewebview2.exe", "claude.exe", "webwalls.exe", "windowsterminal.exe", "applicationframehost.exe",
        "discord.exe", "code.exe", "brave.exe", "opera.exe", "spotify.exe", "slack.exe", "teams.exe", "ms-teams.exe",
    };

    private static HashSet<string> _gameBarExes = new(StringComparer.OrdinalIgnoreCase);
    private static DateTime _gameBarLoaded = DateTime.MinValue;

    /// <summary>The last app (not us, not the desktop) that had focus, so the tray can offer "treat X as a game".</summary>
    public static string? LastForeignExe { get; private set; }

    public static GameInfo? Detect(IEnumerable<string> userGames)
    {
        IntPtr fg = Native.GetForegroundWindow();
        bool d3dFull = Native.SHQueryUserNotificationState(out int quns) == 0 &&
                       (quns == Native.QUNS_RUNNING_D3D_FULL_SCREEN || quns == Native.QUNS_BUSY || quns == Native.QUNS_PRESENTATION_MODE);

        if (fg == IntPtr.Zero || fg == Native.GetShellWindow() || !Native.IsWindowVisible(fg))
            return null;

        string cls = Native.ClassNameOf(fg);
        if (cls is "Progman" or "WorkerW" or "Shell_TrayWnd" or "Shell_SecondaryTrayWnd" or "NotifyIconOverflowWindow")
            return null;

        string? path = ExePath(fg);
        string? exe = path != null ? Path.GetFileName(path) : null;
        if (exe != null && !exe.Equals("WebWalls.exe", StringComparison.OrdinalIgnoreCase)) LastForeignExe = exe;

        if (!Native.GetWindowRect(fg, out var wr)) return null;
        IntPtr mon = Native.MonitorFromWindow(fg, Native.MONITOR_DEFAULTTONEAREST);
        var mi = new Native.MONITORINFO { cbSize = Marshal.SizeOf<Native.MONITORINFO>() };
        if (!Native.GetMonitorInfo(mon, ref mi)) return null;
        Rectangle m = mi.rcMonitor.ToRectangle(), w = wr.ToRectangle();

        bool hasCaption = (Native.GetStyle(fg, Native.GWL_STYLE) & Native.WS_CAPTION) == Native.WS_CAPTION;
        bool coversWhole = w.Left <= m.Left && w.Top <= m.Top && w.Right >= m.Right && w.Bottom >= m.Bottom;

        bool maximized = Native.IsZoomed(fg);

        // 1) Real fullscreen (borderless or exclusive): always a game/video, whoever made it.
        //    Maximized windows don't count: Chrome, Discord, VS Code, the Claude app etc. draw their own
        //    title bars, so a maximized one on a screen with no taskbar looks borderless and fills the screen.
        //    Real fullscreen games/videos aren't "maximized" in Windows' eyes, so this tells them apart.
        bool knownApp = exe != null && NotGames.Contains(exe);   // Claude, browsers, launchers: never a game
        if (coversWhole && ((!hasCaption && !maximized && !knownApp) || d3dFull))
            return new GameInfo(m, true, exe);

        // 2) Windowed / maximized: only if we know this exe is a game.
        if (path == null || exe == null || NotGames.Contains(exe)) return null;
        if (!IsKnownGame(path, exe, userGames)) return null;

        var overlap = Rectangle.Intersect(w, m);
        double cover = (double)overlap.Width * overlap.Height / Math.Max(1.0, (double)m.Width * m.Height);
        bool covers = maximized || cover >= 0.85;
        return new GameInfo(m, covers, exe);
    }

    private static bool IsKnownGame(string path, string exe, IEnumerable<string> userGames)
    {
        if (userGames.Contains(exe, StringComparer.OrdinalIgnoreCase)) return true;
        string p = path.ToLowerInvariant();
        foreach (var f in StoreFolders) if (p.Contains(f)) return true;
        RefreshGameBarList();
        return _gameBarExes.Contains(path);
    }

    /// <summary>Windows Game Bar keeps a list of exes it has recognised as games. Re-read it once a minute.</summary>
    private static void RefreshGameBarList()
    {
        if ((DateTime.UtcNow - _gameBarLoaded).TotalSeconds < 60) return;
        _gameBarLoaded = DateTime.UtcNow;
        var set = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        try
        {
            using var root = Registry.CurrentUser.OpenSubKey(@"System\GameConfigStore\Children");
            if (root != null)
                foreach (var name in root.GetSubKeyNames())
                {
                    using var k = root.OpenSubKey(name);
                    if (k?.GetValue("MatchedExeFullPath") is string exePath && exePath.Length > 0) set.Add(exePath);
                }
        }
        catch { }
        _gameBarExes = set;
    }

    private static string? ExePath(IntPtr hwnd)
    {
        try
        {
            GetWindowThreadProcessId(hwnd, out uint pid);
            if (pid == 0) return null;
            IntPtr h = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, pid);
            if (h == IntPtr.Zero) return null;
            try
            {
                var sb = new StringBuilder(1024);
                int size = sb.Capacity;
                return QueryFullProcessImageName(h, 0, sb, ref size) ? sb.ToString() : null;
            }
            finally { CloseHandle(h); }
        }
        catch { return null; }
    }

    private const uint PROCESS_QUERY_LIMITED_INFORMATION = 0x1000;

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool QueryFullProcessImageName(IntPtr hProcess, uint flags, StringBuilder exeName, ref int size);

    [DllImport("kernel32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr h);
}

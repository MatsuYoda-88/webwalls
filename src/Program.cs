namespace WebWalls;

internal static class Program
{
    public const string QuitEventName = @"Local\WebWalls.Quit";

    [STAThread]
    private static void Main(string[] args)
    {
        // "WebWalls.exe --quit" politely closes the running copy (used by the installer / uninstaller),
        // so it can put the normal Windows wallpaper back instead of being force-killed.
        if (args.Any(a => a.Equals("--quit", StringComparison.OrdinalIgnoreCase)))
        {
            try { using var ev = EventWaitHandle.OpenExisting(QuitEventName); ev.Set(); } catch { }
            return;
        }

        // Only one Ricky at a time.
        using var mutex = new Mutex(true, @"Local\WebWalls.SingleInstance", out bool first);
        if (!first) return;

        ApplicationConfiguration.Initialize();
        Application.ThreadException += (_, e) => Log(e.Exception);
        AppDomain.CurrentDomain.UnhandledException += (_, e) => Log(e.ExceptionObject as Exception);

        Application.Run(new TrayApp());
    }

    private static void Log(Exception? ex)
    {
        try
        {
            Directory.CreateDirectory(Settings.Folder);
            File.AppendAllText(Path.Combine(Settings.Folder, "error.log"), $"[{DateTime.Now:u}] {ex}\n\n");
        }
        catch { }
    }
}

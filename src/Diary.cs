namespace WebWalls;

/// <summary>Small diary of what web.walls fixed on its own: %APPDATA%\WebWalls\events.log (kept under ~200 KB).</summary>
internal static class Diary
{
    private static readonly object Gate = new();

    public static void Log(string msg)
    {
        try
        {
            lock (Gate)
            {
                Directory.CreateDirectory(Settings.Folder);
                string path = Path.Combine(Settings.Folder, "events.log");
                var fi = new FileInfo(path);
                if (fi.Exists && fi.Length > 200_000)
                {
                    string old = Path.Combine(Settings.Folder, "events.old.log");
                    File.Copy(path, old, true);
                    File.WriteAllText(path, "");
                }
                File.AppendAllText(path, $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {msg}\n");
            }
        }
        catch { }
    }
}

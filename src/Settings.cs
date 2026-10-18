using System.Text.Json;

namespace WebWalls;

public enum BatteryMode { KeepGoing, Cap30, Pause }

/// <summary>What the screens WITHOUT the game do while you play. (The game's own screen always sleeps.)</summary>
public enum GamingMode { Lighter, Freeze, Full }

/// <summary>Saved to %APPDATA%\WebWalls\settings.json.</summary>
public sealed class Settings
{
    public string? CurrentWallpaper { get; set; }
    public List<string> CustomWallpapers { get; set; } = new();
    public int FpsCap { get; set; } = 60;            // 0 = unlimited
    public bool PauseWhenFullscreen { get; set; } = true;
    public BatteryMode OnBattery { get; set; } = BatteryMode.Cap30;
    public bool Muted { get; set; } = true;
    /// <summary>Monitors (by Windows device name, e.g. \\.\DISPLAY2) the user switched the wallpaper off on.</summary>
    public List<string> HiddenScreens { get; set; } = new();
    /// <summary>Render resolution: 1 = full, 0.75 = balanced, 0.5 = performance.</summary>
    public double RenderScale { get; set; } = 1.0;
    public GamingMode WhileGaming { get; set; } = GamingMode.Lighter;
    /// <summary>Exe names you told web.walls are games (for windowed games it can't recognise on its own).</summary>
    public List<string> GameExes { get; set; } = new();

    public static string Folder =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WebWalls");

    private static string FilePath => Path.Combine(Folder, "settings.json");
    private static readonly JsonSerializerOptions Json = new() { WriteIndented = true };

    public static Settings Load()
    {
        try
        {
            if (File.Exists(FilePath))
                return JsonSerializer.Deserialize<Settings>(File.ReadAllText(FilePath), Json) ?? new Settings();
        }
        catch { /* corrupted settings? start fresh, no drama */ }
        return new Settings();
    }

    public void Save()
    {
        try
        {
            Directory.CreateDirectory(Folder);
            File.WriteAllText(FilePath, JsonSerializer.Serialize(this, Json));
        }
        catch { }
    }
}

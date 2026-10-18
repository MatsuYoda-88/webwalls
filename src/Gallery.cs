using System.Reflection;
using System.Text.RegularExpressions;

namespace WebWalls;

internal sealed record WallpaperItem(string Name, string Path, bool BuiltIn);

/// <summary>Built-in wallpapers are baked into the exe and unpacked to %APPDATA%\WebWalls\wallpapers.</summary>
internal static class Gallery
{
    public static string Folder => System.IO.Path.Combine(Settings.Folder, "wallpapers");

    public static void Unpack()
    {
        var asm = Assembly.GetExecutingAssembly();
        foreach (var res in asm.GetManifestResourceNames())
        {
            string rel = res.Replace('\\', '/');
            if (!rel.StartsWith("wallpapers/")) continue;
            string dest = System.IO.Path.Combine(Folder, rel["wallpapers/".Length..].Replace('/', System.IO.Path.DirectorySeparatorChar));
            try
            {
                using var src = asm.GetManifestResourceStream(res)!;
                // Always refresh built-ins so updates to the app update the gallery.
                Directory.CreateDirectory(System.IO.Path.GetDirectoryName(dest)!);
                using var fs = File.Create(dest);
                src.CopyTo(fs);
            }
            catch { /* file in use, whatever, it's already there */ }
        }
    }

    public static List<WallpaperItem> BuiltIns()
    {
        var list = new List<WallpaperItem>();
        if (!Directory.Exists(Folder)) return list;
        foreach (var f in Directory.GetFiles(Folder, "*.html").OrderBy(f => f))
            list.Add(new WallpaperItem(NameOf(f), f, true));
        foreach (var d in Directory.GetDirectories(Folder).OrderBy(d => d))
        {
            string idx = System.IO.Path.Combine(d, "index.html");
            if (File.Exists(idx)) list.Add(new WallpaperItem(NameOf(idx), idx, true));
        }
        return list;
    }

    /// <summary>Uses the page's &lt;title&gt; if it has one, else the file/folder name.</summary>
    public static string NameOf(string path)
    {
        try
        {
            string head = new string(File.ReadAllText(path).Take(4000).ToArray());
            var m = Regex.Match(head, "<title>(.*?)</title>", RegexOptions.IgnoreCase | RegexOptions.Singleline);
            if (m.Success && m.Groups[1].Value.Trim().Length > 0) return m.Groups[1].Value.Trim();
        }
        catch { }
        string name = System.IO.Path.GetFileNameWithoutExtension(path);
        if (name.Equals("index", StringComparison.OrdinalIgnoreCase))
            name = new DirectoryInfo(System.IO.Path.GetDirectoryName(path)!).Name;
        return name.Replace('-', ' ').Replace('_', ' ');
    }
}

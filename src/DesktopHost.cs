using System.Text;

namespace WebWalls;

/// <summary>
/// Finds the secret layer between the Windows wallpaper and the desktop icons, and glues our
/// windows into it. Handles both the classic layout and the Windows 11 24H2+ layout
/// (where WorkerW moved inside Progman).
/// </summary>
internal static class DesktopHost
{
    public sealed record Target(IntPtr Parent, IntPtr InsertAfter, bool Raised);

    public static Target? Find()
    {
        IntPtr progman = Native.FindWindow("Progman", null);
        if (progman == IntPtr.Zero) return null;

        // Ask Progman to spawn the WorkerW layer behind the icons (undocumented but used by everyone).
        Native.SendMessageTimeout(progman, 0x052C, new IntPtr(0xD), new IntPtr(0x1), Native.SMTO_NORMAL, 1000, out _);
        Native.SendMessageTimeout(progman, 0x052C, IntPtr.Zero, IntPtr.Zero, Native.SMTO_NORMAL, 1000, out _);

        // --- Windows 11 24H2 and newer: icons view + WorkerW are both children of Progman ---
        IntPtr defViewInProgman = Native.FindWindowEx(progman, IntPtr.Zero, "SHELLDLL_DefView", null);
        IntPtr workerInProgman = Native.FindWindowEx(progman, IntPtr.Zero, "WorkerW", null);
        if (defViewInProgman != IntPtr.Zero && workerInProgman != IntPtr.Zero)
        {
            // Child of Progman, slotted directly under the icon view (so above WorkerW, below icons).
            return new Target(progman, defViewInProgman, true);
        }

        // --- Classic layout: the icons live in some top-level WorkerW; the next WorkerW is our layer ---
        IntPtr workerW = IntPtr.Zero;
        Native.EnumWindows((top, _) =>
        {
            IntPtr defView = Native.FindWindowEx(top, IntPtr.Zero, "SHELLDLL_DefView", null);
            if (defView != IntPtr.Zero)
            {
                workerW = Native.FindWindowEx(IntPtr.Zero, top, "WorkerW", null);
            }
            return true;
        }, IntPtr.Zero);

        if (workerW != IntPtr.Zero) return new Target(workerW, IntPtr.Zero, false);

        // Last resort: Progman itself (icons stay on top because DefView paints over us).
        return new Target(progman, defViewInProgman, defViewInProgman != IntPtr.Zero);
    }

    /// <summary>Make <paramref name="hwnd"/> a child of the desktop layer, covering <paramref name="screenBounds"/>.</summary>
    public static bool Attach(IntPtr hwnd, Rectangle screenBounds)
    {
        var target = Find();
        if (target is null) return false;

        long style = Native.GetStyle(hwnd, Native.GWL_STYLE);
        style &= ~(Native.WS_POPUP | Native.WS_CAPTION | Native.WS_THICKFRAME);
        style |= Native.WS_CHILD | Native.WS_VISIBLE;
        Native.SetStyle(hwnd, Native.GWL_STYLE, style);

        long ex = Native.GetStyle(hwnd, Native.GWL_EXSTYLE);
        ex &= ~Native.WS_EX_APPWINDOW;
        ex |= Native.WS_EX_TOOLWINDOW | Native.WS_EX_NOACTIVATE;
        if (target.Raised) ex |= Native.WS_EX_LAYERED; // 24H2 needs a layered child to composite
        Native.SetStyle(hwnd, Native.GWL_EXSTYLE, ex);
        if (target.Raised) Native.SetLayeredWindowAttributes(hwnd, 0, 255, Native.LWA_ALPHA);

        Native.SetParent(hwnd, target.Parent);

        // Child coordinates are relative to the parent, which spans the whole virtual screen.
        Rectangle parentRect = Native.GetWindowRect(target.Parent, out var pr) ? pr.ToRectangle() : SystemInformation.VirtualScreen;
        int x = screenBounds.Left - parentRect.Left;
        int y = screenBounds.Top - parentRect.Top;

        uint flags = Native.SWP_NOACTIVATE | Native.SWP_SHOWWINDOW | Native.SWP_FRAMECHANGED;
        if (target.InsertAfter == IntPtr.Zero) flags |= Native.SWP_NOZORDER;
        Native.SetWindowPos(hwnd, target.InsertAfter, x, y, screenBounds.Width, screenBounds.Height, flags);
        return true;
    }

    /// <summary>Repaint the normal Windows wallpaper (used when we quit so the desktop isn't left black).</summary>
    public static void RestoreStockWallpaper()
    {
        var sb = new StringBuilder(520);
        if (Native.SystemParametersInfo(Native.SPI_GETDESKWALLPAPER, (uint)sb.Capacity, sb, 0))
        {
            Native.SystemParametersInfo(Native.SPI_SETDESKWALLPAPER, 0, sb.ToString(), Native.SPIF_SENDCHANGE);
        }
    }
}

## Install
1. Download **WebWalls-Setup-x.y.z.exe** below (under *Assets*).
2. Run it. If Windows shows a blue **"Windows protected your PC"** box, click **More info → Run anyway**. (web.walls is a free hobby app and isn't paid-signed. That's the only reason you see it.)
3. Look for the neon **W** in your system tray (click the `^` arrow if it's hidden) and right-click it to pick a wallpaper.

No admin rights needed. Uninstall any time from **Settings → Apps → web.walls**.

## New in v0.8.2: smooth again
- Fixed lag from 0.8.1's self-healing: it was reloading wallpapers that were only *covered* (Windows slows covered pages on purpose), and nudging the desktop every 3 s. Checks are now look-only, every 5 s, and a reload needs a full minute of a visible wallpaper being truly stuck.
- New tray item **Show fix log** opens the list of everything web.walls fixed on its own.

## New in v0.8.1: self-healing
- **No more falling back to the Windows wallpaper.** Every 3 seconds web.walls checks it's still glued behind your icons, and re-glues if Windows knocked it loose (theme or wallpaper changes, sleep/wake, unlocking, monitors waking up, Spotlight).
- **No more frozen or black wallpapers.** If the browser's graphics or page process crashes or hangs, or a GPU scene loses the graphics card (driver reset, eGPU hiccup), the wallpaper reloads itself. If the whole browser dies, the screens are rebuilt.
- What it fixed and when goes in `%APPDATA%\WebWalls\events.log`.

## New in v0.8: OLED showcase scenes
Four new GPU wallpapers built to show off high-res OLEDs. They render at your screen's exact pixels, up to 8K, run smooth at up to 240 Hz, and empty space is true black (pixels off):
- **Event Horizon**: a ray-traced black hole bending a blazing accretion disk and the starfield around it
- **Abyss**: neon jellyfish trailing hair-thin tentacles through bioluminescent plankton
- **Prairie Fireflies**: thousands of fireflies blinking over dark grass under the Milky Way
- **Fractal Dive**: endless Mandelbrot dives drawn as razor-thin neon filaments

## New in v0.7.1
- "Start with Windows" is checked by default again.

## New in v0.7
- **Super-ultrawide 32:9 support** (5120×1440 / 3840×1080, e.g. Samsung Odyssey OLED G9): every scene reflows to fill the full width. Wallpapers get a `ww-superultrawide` class (plus `ww-ultrawide`) to tune for it.
- **High-refresh frame rates:** *Performance → Frame rate* now has 240 / 144 / 120 FPS, and *Unlimited* matches your screen's refresh rate.

## What's in it
- 12 animated wallpapers: Event Horizon, Abyss, Prairie Fireflies, Fractal Dive (new in v0.8), Neon Galaxy (new in v0.6, OLED-tuned), Neon Highway, Midnight Rain City, Aurora Lake, Baldwin's Crusade, and the Montgisard trilogy
- Works on every monitor: 32:9 super-ultrawide, ultrawide, 16:9 and portrait screens all get their own properly fitted copy
- Gaming-aware: the screen your game is on sleeps completely, and your other screens drop to 30 FPS / half resolution while you play (windowed games too)
- Battery saver, FPS cap, quality setting, and load your own HTML wallpapers

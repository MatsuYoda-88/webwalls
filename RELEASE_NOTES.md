## Install
1. Download **WebWalls-Setup-x.y.z.exe** below (under *Assets*).
2. Run it. If Windows shows a blue **"Windows protected your PC"** box, click **More info → Run anyway**. (web.walls is a free hobby app and isn't paid-signed. That's the only reason you see it.)
3. Look for the neon **W** in your system tray (click the `^` arrow if it's hidden) and right-click it to pick a wallpaper.

No admin rights needed. Uninstall any time from **Settings → Apps → web.walls**.

## New in v0.9: Abyss Pets
- **New wallpaper: Abyss Pets.** Same deep sea as Abyss, but the jellies are your pets. They stick around and never leave the screen, blink at you, and take turns showing off: **backflips, twirls, loop-de-loops and a rainbow happy dance**. About every minute and a quarter, one swims right up to the glass, gets big, boops it with a ripple, smiles and **waves at you**.

## New in v0.8.5
- Abyss: jellyfish tentacles stay attached to the bell when it tilts (each one is pinned to its own spot on the rim, and they come out of it straight before swaying).

## New in v0.8.4: livelier jellies, no more glitching
- **Abyss jellyfish come alive**: they swim in surges with each pulse, wander around the screen, tilt toward where they're heading, and their tentacles trail and curl behind them with light pulses running down. Vivid neon colours (hot pink, cyan, electric blue, violet, lime, orange), near and far jellies, and more of them on wide screens.
- **Fixed the GPU scenes going stripy and choppy after the PC had been on for hours** (Event Horizon, Abyss, Prairie Fireflies, Fractal Dive, Neon Galaxy). Their clock now loops every 30 minutes with a quick dip to black, so they look as good on day 5 as after a fresh start.

## New in v0.8.3: starts with Windows again
- Fixed "Start with Windows" quietly staying off after updating. The installer was remembering an old unticked box from v0.7.0.
- web.walls now keeps its own startup entry healthy: every launch it puts it back if an update, a cleanup tool or Task Manager switched it off. To really turn it off, untick **Start with Windows** in the web.walls tray menu.

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

## Make your own
Every wallpaper is just a web page. **[How to add your own wallpapers](https://github.com/MatsuYoda-88/webwalls/blob/main/docs/ADD-WALLPAPERS.md)**: load ones friends send you, add them to the list, or make your own (there's a starter and a ready-made AI prompt).

## What's in it
- 13 animated wallpapers: Abyss Pets (new in v0.9), Event Horizon, Abyss, Prairie Fireflies, Fractal Dive (new in v0.8), Neon Galaxy (new in v0.6, OLED-tuned), Neon Highway, Midnight Rain City, Aurora Lake, Baldwin's Crusade, and the Montgisard trilogy
- Works on every monitor: 32:9 super-ultrawide, ultrawide, 16:9 and portrait screens all get their own properly fitted copy
- Gaming-aware: the screen your game is on sleeps completely, and your other screens drop to 30 FPS / half resolution while you play (windowed games too)
- Battery saver, FPS cap, quality setting, and load your own HTML wallpapers

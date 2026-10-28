# web.walls

**Animated live wallpapers for Windows 10/11**: an OLED-tuned neon galaxy, neon synthwave highways, rainy cities, northern lights, and crusader battles, running behind your desktop icons.

### [⬇ Download the latest installer](https://github.com/MatsuYoda-88/webwalls/releases/latest)

Grab **WebWalls-Setup-x.y.z.exe** under *Assets*.

**On Android?** Grab **WebWalls-Android-x.y.apk** from the newest *web.walls for Android* release on the [Releases page](https://github.com/MatsuYoda-88/webwalls/releases). If Windows says **"Windows protected your PC"**, click **More info → Run anyway**. It's a free hobby app and isn't paid-signed; that's the only reason. No admin needed.

![Neon Galaxy on an ultrawide](docs/neon-galaxy.jpg)

![Neon Highway on an ultrawide](docs/neon-highway.jpg)

| | |
|---|---|
| ![Montgisard](docs/montgisard.jpg) | ![Baldwin's Crusade](docs/baldwins-crusade.jpg) |
| ![Midnight Rain City](docs/rain-city.jpg) | ![Aurora Lake](docs/aurora-lake.jpg) |

**Every screen gets its own fitted copy:** ultrawide, regular, or a laptop stood up in portrait.
<img src="docs/portrait.jpg" width="180" alt="Neon Highway in portrait">

---


Animated HTML live wallpapers that sit behind your desktop icons. Windows sibling of the web.walls Android app: same HTML wallpapers work on both.

## Run it
Install it, then look for the neon **W** in the system tray (click the `^` arrow if it's hidden).

- **Right-click the tray icon** → pick a wallpaper, load your own HTML, pause, performance settings, start with Windows, quit.
- **Double-click the tray icon** → pause / resume.
- Quitting puts your normal Windows wallpaper back.

## Multi-monitor + ultrawide (v0.2)
- **Same wallpaper on every screen.** Each monitor runs its own copy sized to *its* shape, so the scene reflows to fit instead of stretching across the gap.
- **Any shape:** ultrawide 21:9 (2560×1080), regular 16:9/16:10, and **portrait** (the X Flip standing on end). The built-in scenes reflow for each. Montgisard pans its camera to keep Baldwin in frame on tall screens, and Neon Highway keeps its mountains from going spiky.
- **Displays menu:** right-click the tray icon → *Displays* to switch the wallpaper off on any monitor (e.g. ultrawide only). *Show on all displays* turns them all back on.
- **Plug / unplug / rotate:** web.walls notices, waits a second for Windows to settle, then rebuilds only if the layout actually changed.

## OLED showcase scenes (v0.8)
- **Event Horizon, Abyss, Prairie Fireflies, Fractal Dive**: GPU-rendered at each screen's exact pixels up to 8K, frame-rate independent up to 240 Hz, true-black backgrounds. Source shaders live in `tools/gen_oled.py`.

## Super-ultrawide 32:9 (v0.7)
- **5120×1440 / 3840×1080 screens** (Odyssey OLED G9 and friends) get a fitted copy that fills the full 32:9 width. Wallpaper makers can target them with the `ww-superultrawide` class or `window.__webwalls.screen.shape === 'superultrawide'`.
- **High refresh:** *Performance → Frame rate* adds 240 / 144 / 120 FPS; *Unlimited* runs at your screen's native refresh.

## Gaming (v0.3)
- **The screen your game is on sleeps completely**, so it doesn't fight the game for the GPU.
- **Your other screens go lighter while you play** (30 FPS, half resolution). Change this in *Performance → Gaming*: Lighter / Freeze / Full quality.
- **Windowed and maximized games count too.** web.walls recognises games installed by Steam, Epic, GOG, Xbox, EA, Ubisoft, Riot, Battle.net and Rockstar, plus anything Windows Game Bar has flagged as a game. A maximized browser is never mistaken for one.
- **Game not recognised?** Play it for a few seconds, then right-click the tray icon → *Performance → Gaming → Treat "game.exe" as a game*.
- **Gaming mode on right now (manual)** forces it on whenever you want.
- **No more black screens (v0.4):** a sleeping screen shows its last frame as a still picture, and maximized apps (Chrome, Discord, VS Code...) are never mistaken for fullscreen games.
- **Quality** (*Performance → Quality*): Full / Balanced (75%) / Performance (half resolution), for everyday use too.

## What it does on its own
- **Battery:** pick in *Performance → On battery*: keep going full send, cap at 30 FPS (default), or pause.
- **Frame rate cap:** Unlimited / 60 / 30 / 15 in *Performance → Frame rate*. Works on any HTML wallpaper, even ones that don't know about web.walls.
- **Sound:** wallpapers are muted by default.

## Neon Galaxy (v0.6)
- A GPU-rendered spiral galaxy tuned for OLED. Empty space is true black (pixels fully off), colours are fully saturated, and it renders at native resolution and your screen's full refresh rate.
- Burn-in friendly: the galaxy spins, wanders and tilts, nebulae flow, stars drift in parallax, shooting stars fly through, and the colours cycle every ~5 minutes.

## Your own wallpapers
*Wallpapers → Load my own HTML…* and pick an `.html` file. Images, scripts and videos next to it (or in subfolders) load fine because the folder is served like a mini website.

Want it in the built-in list? Drop it in the gallery folder (*Wallpapers → Open gallery folder*, which is `%APPDATA%\WebWalls\wallpapers`) as `name.html` or `name\index.html`. The menu uses the page's `<title>` as its name.

**Optional hook for wallpaper makers:** web.walls fires a `webwalls` event when it pauses or changes FPS:
```js
addEventListener('webwalls', e => console.log(e.detail.paused, e.detail.fps));
```
It also tells each wallpaper what screen it's on, so you can lay things out differently for ultrawide or portrait:
```js
window.__webwalls.screen  // { index, count, width, height, aspect, shape: 'ultrawide'|'wide'|'portrait', primary }
```
```css
.ww-ultrawide .sidebar { display: block }   /* <html> gets ww-ultrawide / ww-wide / ww-portrait */
```

## Releases
Friends get a normal Windows installer: **WebWalls-Setup-x.y.z.exe**. It needs no admin, adds a Start menu entry and an optional "start with Windows", and uninstalls cleanly from *Settings → Apps*.

- **Publish a new version:** bump `<Version>` in `src\WebWalls.csproj` and push to main. GitHub Actions builds the app + installer and creates the Release automatically. Send friends the Releases link.
- Friends will see **"Windows protected your PC"** (it's not paid-signed): **More info → Run anyway**. The release notes tell them this.

## Build it yourself
Needs the .NET 8 SDK and Inno Setup 6: `dotnet publish src\WebWalls.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -p:EnableCompressionInSingleFile=true -o dist`, then `ISCC /DAppVersion=0.6.0 installer\WebWalls.iss`.

## Files
- `src\` C# app (WinForms + WebView2)
- `installer\` Inno Setup script for the friends' installer
- `.github\workflows\release.yml` builds and publishes Releases on GitHub
- `wallpapers\` built-in gallery (baked into the exe)
- Settings: `%APPDATA%\WebWalls\settings.json` · crash log: `%APPDATA%\WebWalls\error.log`

Needs Windows 10/11 with the Edge WebView2 Runtime (built into Windows 11).

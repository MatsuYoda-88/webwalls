# How to add your own wallpapers to web.walls

A web.walls wallpaper is just a **web page**: an `.html` file, the same kind of file a website is made of. If it runs in Chrome or Edge, it'll run on your desktop. You don't need to install anything to make one; Notepad works.

There are 3 ways to do it, from easiest to most fun:

1. [Load one somebody gave you](#1-load-a-wallpaper-file-somebody-gave-you) (10 seconds)
2. [Put it in the built-in list](#2-put-it-in-the-built-in-list) (1 minute)
3. [Make your own](#3-make-your-own) (as long as you want)

---

## 1. Load a wallpaper file somebody gave you

1. Save the `.html` file somewhere it'll stay, like `Documents\Wallpapers\`. (Don't leave it in Downloads if you clean that out; web.walls loads it from where it sits.)
2. Right-click the neon **W** in the system tray (click the `^` by the clock if you don't see it).
3. **Wallpapers → Load my own HTML…** and pick the file.

That's it. It now shows up under **Wallpapers → My wallpapers** so you can switch back to it any time.

**Got a folder instead of one file?** (Some wallpapers come with pictures, music or videos.) Keep the whole folder together and pick the `.html` file inside it. Everything next to it loads fine.

**Wallpaper Engine "Web" wallpapers:** a lot of them work. Find the folder with `index.html` in it and load that. Any sliders or settings they had in Wallpaper Engine just use their defaults.

---

## 2. Put it in the built-in list

If you want it sitting right there in the main **Wallpapers** list with the others:

1. Right-click the **W** → **Wallpapers → Open gallery folder**.
   (It's `%APPDATA%\WebWalls\wallpapers`. You can paste that into the File Explorer address bar.)
2. Copy your file in as `something.html`.
   For a wallpaper with extra files, copy the whole folder in and make sure the main file inside is called `index.html`.
3. Right-click the **W** again. It's in the list.

The name in the menu comes from the `<title>` line at the top of the file. Change that to rename it.

> ⚠️ Don't use the same file name as one of the built-in wallpapers (like `abyss.html`). Built-ins get refreshed every time web.walls starts, so yours would be overwritten.

---

## 3. Make your own

### Start from the starter

Grab **[starter-wallpaper.html](../examples/starter-wallpaper.html)** (click it, then the download button ⤓). It's glowing neon bubbles floating up on black:

![Starter wallpaper](starter.jpg)

1. Open it in **Chrome or Edge** (double-click it) to see it running.
2. Open it in **Notepad** (right-click → Open with → Notepad) and change the lines marked `CHANGE ME`: the colours, how many bubbles, how fast.
3. Save, then hit **F5** in the browser to see your change.
4. Happy with it? Load it into web.walls (step 1 or 2 above).

### Let an AI write one for you

The fastest way to get something wild is to ask Claude (or any AI) for it. Paste something like this:

> Make me a live wallpaper as ONE html file. It should be **[a rainy neon Tokyo street / koi fish swimming in a dark pond / a spinning rotary engine made of glowing lines]**.
> Rules: full-screen canvas, black background, size the canvas with `devicePixelRatio` so it's sharp on 4K and 5120×1440 screens, animate with `requestAnimationFrame` using real time so it's smooth at any frame rate, keep moving slowly so nothing burns into an OLED, and look good on 16:9, 21:9, 32:9 and portrait screens. No libraries, no internet needed.

Save what it gives you as `whatever.html`, double-click to test, then load it into web.walls.

### Rules of thumb for good wallpapers

- **Black is your friend.** On OLED screens, pure black (`#000`) pixels are switched fully off: deeper looks and less power.
- **Keep things moving.** Anything bright that sits still for hours can burn into an OLED. Slow drift is enough.
- **Fill any shape.** Your wallpaper runs on every monitor, sized to that monitor: regular 16:9, ultrawide 21:9, super-ultrawide 32:9, a laptop stood up in portrait. Use `innerWidth` / `innerHeight` for layout and don't assume 1920×1080.
- **Be sharp.** Multiply your canvas size by `window.devicePixelRatio`, or 4K screens will look blurry.
- **Move by time, not frames.** If you move things "5 pixels per frame", it'll run 4× faster at 240 Hz than at 60. Use the time between frames instead (the starter shows how).
- **Don't worry about pausing.** web.walls pauses your wallpaper for you when you game, go on battery, or hit pause. It works on any page, even ones that know nothing about web.walls.
- **No sound by default.** Wallpapers are muted unless you untick *Performance → Mute wallpaper sound* in the tray menu.
- **No internet needed.** It's best if everything is in the file or folder. Pages that pull stuff from the internet will break when you're offline.

### Extra tricks web.walls gives you (optional)

**Know what screen you're on:**
```js
window.__webwalls.screen
// → { index, count, width, height, aspect, shape, primary }
// shape is 'superultrawide' (32:9), 'ultrawide' (21:9), 'wide' (16:9/16:10) or 'portrait'
```
The page also gets a class on `<html>`, so you can do it in CSS:
```css
.ww-superultrawide .side-panels { display: block; }  /* only on 32:9 screens */
.ww-portrait .title { font-size: 6vw; }               /* laptop stood on end */
```

**Know when you're paused or capped:**
```js
addEventListener('webwalls', e => {
  e.detail.paused   // true while paused (gaming, battery, manual)
  e.detail.fps      // frame-rate cap, 0 = unlimited
});
```

### Share it with your friends

Send them the `.html` file (or zip up the folder) and point them at [step 1](#1-load-a-wallpaper-file-somebody-gave-you). The **web.walls Android app** can load the same file, so it works on their phone too.

Made something sick? Open an issue on this repo with a screenshot and the file. It might end up in the built-in list.

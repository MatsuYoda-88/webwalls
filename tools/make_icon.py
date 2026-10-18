"""Builds src/assets/webwalls.ico the way Windows' shell likes it:
classic 32-bit BMP frames for 16-128px, PNG only for the 256px frame, planes=1, bpp=32."""
import io, struct, sys
from PIL import Image, ImageDraw, ImageFilter

S = 1024


def lin(w, h, c0, c1, mode):
    im = Image.new('RGBA', (w, h)); px = im.load()
    for y in range(h):
        for x in range(w):
            t = (x + y) / (w + h - 2) if mode == 'diag' else x / (w - 1)
            px[x, y] = tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3)) + (255,)
    return im


BG = lin(S, S, (20, 10, 40), (40, 0, 60), 'diag')
GRAD = lin(S, S, (0, 255, 230), (255, 40, 200), 'h')


def make(size):
    k = S / 32
    mask = Image.new('L', (S, S), 0); ImageDraw.Draw(mask).ellipse([1 * k, 1 * k, 31 * k, 31 * k], fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0)); out.paste(BG, (0, 0), mask)
    sw = 3.2 * k * (1.25 if size <= 24 else 1.0)          # chunkier W at taskbar sizes
    pts = [(6 * k, 9 * k), (11 * k, 23 * k), (16 * k, 13 * k), (21 * k, 23 * k), (26 * k, 9 * k)]
    wm = Image.new('L', (S, S), 0); d = ImageDraw.Draw(wm)
    d.line(pts, fill=255, width=int(sw), joint='curve')
    for (x, y) in pts: d.ellipse([x - sw / 2, y - sw / 2, x + sw / 2, y + sw / 2], fill=255)
    glow = wm.filter(ImageFilter.GaussianBlur(S * 0.03)).point(lambda v: int(v * 0.7))
    gl = Image.new('RGBA', (S, S), (0, 0, 0, 0)); gl.paste(GRAD, (0, 0), glow)
    gl.putalpha(Image.composite(glow, Image.new('L', (S, S), 0), mask))
    out = Image.alpha_composite(out, gl)
    st = Image.new('RGBA', (S, S), (0, 0, 0, 0)); st.paste(GRAD, (0, 0), wm)
    return Image.alpha_composite(out, st).resize((size, size), Image.LANCZOS)


def bmp_frame(img):
    """32bpp DIB: BITMAPINFOHEADER (height doubled) + bottom-up BGRA rows + 1bpp AND mask."""
    w, h = img.size
    hdr = struct.pack('<IiiHHIIiiII', 40, w, h * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    px = img.load(); xor = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = px[x, y]; xor += bytes((b, g, r, a))
    row = ((w + 31) // 32) * 4; andm = bytearray()
    for y in range(h - 1, -1, -1):
        bits = bytearray(row)
        for x in range(w):
            if px[x, y][3] == 0: bits[x // 8] |= 0x80 >> (x % 8)
        andm += bits
    return hdr + bytes(xor) + bytes(andm)


def main(out_path):
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    frames = []
    for s in sizes:
        im = make(s)
        if s == 256:
            b = io.BytesIO(); im.save(b, 'PNG'); frames.append((s, b.getvalue()))
        else:
            frames.append((s, bmp_frame(im)))
    head = struct.pack('<HHH', 0, 1, len(frames))
    off = 6 + 16 * len(frames); dir_ = b''; blob = b''
    for s, data in frames:
        dim = 0 if s >= 256 else s
        dir_ += struct.pack('<BBBBHHII', dim, dim, 0, 0, 1, 32, len(data), off + len(blob))
        blob += data
    open(out_path, 'wb').write(head + dir_ + blob)


if __name__ == '__main__':
    main(sys.argv[1])

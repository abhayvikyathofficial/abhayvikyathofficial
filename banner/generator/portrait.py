# photo -> dithered dot grids for the banner (saved to banner/data)

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "portrait_cutout.png"
DATA = ROOT / "data"
PREVIEW = ROOT / "preview"

GRID_W, GRID_H = 300, 340

PAD_TOP = 26  # space above the hair
CROP_CENTER_X = 0.64

CONTRAST = 1.3
AUTOCONTRAST_CUTOFF = 1
UNSHARP = dict(radius=3, percent=140, threshold=0)


def load_crop():
    im = ImageOps.exif_transpose(Image.open(SRC)).convert("RGBA")
    padded = Image.new("RGBA", (im.width, im.height + PAD_TOP), (0, 0, 0, 0))
    padded.paste(im, (0, PAD_TOP))
    h = padded.height
    w = int(round(h * GRID_W / GRID_H))
    left = int(round(CROP_CENTER_X * padded.width - w / 2))
    left = max(0, min(left, padded.width - w))
    if w > padded.width:
        wide = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        wide.paste(padded, ((w - padded.width) // 2, 0))
        return wide
    return padded.crop((left, 0, left + w, h))


def process_tone(im):
    small = im.resize((GRID_W, GRID_H), Image.LANCZOS)
    rgba = np.asarray(small, dtype=np.float32)
    lum = rgba[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    subject = rgba[..., 3] > 127
    # fill the transparent bg with a mid grey so it doesn't mess up autocontrast
    lum[~subject] = np.median(lum[subject])
    g = Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8))
    g = ImageOps.autocontrast(g, cutoff=AUTOCONTRAST_CUTOFF)
    g = ImageEnhance.Contrast(g).enhance(CONTRAST)
    g = g.filter(ImageFilter.UnsharpMask(**UNSHARP))
    return np.asarray(g, dtype=np.float32) / 255.0


def subject_mask(im):
    alpha = np.asarray(im.resize((GRID_W, GRID_H), Image.LANCZOS))[..., 3]
    fg = alpha > 127
    fg = ndimage.binary_closing(fg, structure=np.ones((3, 3)), iterations=2)
    fg = ndimage.binary_fill_holes(fg)
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = ndimage.sum(fg, lab, range(1, n + 1))
        fg = lab == (int(np.argmax(sizes)) + 1)
    return fg


def dither(tone, valid=None):
    # floyd-steinberg, serpentine
    h, w = tone.shape
    buf = tone.astype(np.float64).copy()
    out = np.zeros((h, w), dtype=bool)
    if valid is None:
        valid = np.ones((h, w), dtype=bool)
    buf[~valid] = 0.0
    for y in range(h):
        if y % 2 == 0:
            xs, step = range(w), 1
        else:
            xs, step = range(w - 1, -1, -1), -1
        row = buf[y]
        nxt = buf[y + 1] if y + 1 < h else None
        for x in xs:
            if not valid[y, x]:
                continue
            v = row[x]
            on = v >= 0.5
            out[y, x] = on
            err = v - (1.0 if on else 0.0)
            xf = x + step
            xb = x - step
            if 0 <= xf < w and valid[y, xf]:
                row[xf] += err * 7 / 16
            if nxt is not None:
                if 0 <= xb < w and valid[y + 1, xb]:
                    nxt[xb] += err * 3 / 16
                if valid[y + 1, x]:
                    nxt[x] += err * 5 / 16
                if 0 <= xf < w and valid[y + 1, xf]:
                    nxt[xf] += err * 1 / 16
    return out


def save_preview(dots, path, fg, bg, scale=2):
    fg_rgb = np.array([int(fg[i : i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)
    bg_rgb = np.array([int(bg[i : i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)
    img = np.where(dots[..., None], fg_rgb, bg_rgb).astype(np.uint8)
    Image.fromarray(img).resize((dots.shape[1] * scale, dots.shape[0] * scale), Image.NEAREST).save(path)


def main():
    DATA.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)

    im = load_crop()
    tone = process_tone(im)
    mask = subject_mask(im)

    # dark mode: bright parts are dots. light mode: dark parts are dots
    dark = dither(tone, valid=mask)
    dark &= ndimage.binary_erosion(mask, iterations=1)
    light = dither(1.0 - tone, valid=mask)
    light &= ndimage.binary_erosion(mask, iterations=1)

    np.save(DATA / "tone.npy", tone.astype(np.float32))
    np.save(DATA / "mask.npy", mask)
    np.save(DATA / "dots_dark.npy", dark)
    np.save(DATA / "dots_light.npy", light)

    save_preview(dark, PREVIEW / "portrait_dark.png", "#A78BFA", "#0A101F")
    save_preview(light, PREVIEW / "portrait_light.png", "#7C3AED", "#FFFFFF")

    print("dark", int(dark.sum()), "light", int(light.sum()))


if __name__ == "__main__":
    main()

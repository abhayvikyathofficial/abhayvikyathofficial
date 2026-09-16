# turns the logo svgs in banner/src/logos into masks for the banner animation

import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "logos"
DATA = ROOT / "data"
PREVIEW = ROOT / "preview"
LOGO_RES = 480


def render(svg):
    png = PREVIEW / f"_render_{svg.stem}.png"
    subprocess.run(
        ["node", str(Path(__file__).with_name("render_svg.cjs")), str(svg), str(png), str(LOGO_RES)],
        check=True,
    )
    return np.asarray(Image.open(png).convert("RGBA"), dtype=np.float32) / 255.0


def figma_mask(rgba):
    return rgba[..., 3] > 0.5


def photoshop_mask(rgba):
    # keep the square, cut out the "Ps" letters
    alpha = rgba[..., 3] > 0.5
    lum = rgba[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return alpha & ~(lum > 0.35)


LOGOS = {
    "figma": (SRC / "figma.svg", figma_mask),
    "photoshop": (SRC / "photoshop.svg", photoshop_mask),
}


def main():
    DATA.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    for name, (svg, fn) in LOGOS.items():
        mask = fn(render(svg))
        np.save(DATA / f"logo_{name}.npy", mask)
        Image.fromarray((mask * 255).astype(np.uint8)).save(PREVIEW / f"logo_{name}.png")
        print(name, round(float(mask.mean()), 3))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
render_graphics.py
Lager statistikk-grafikk (PNG med alpha) fra script.json -> graphics-feltet.
Disse legges som overlays i ffmpeg-steget. Bruker Pillow, ingen kampbilder.
"""
import os, json, sys
from PIL import Image, ImageDraw, ImageFont

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "config.json")))
PRIMARY = CFG["brand"]["primary_color"]
ACCENT = CFG["brand"]["accent_color"]
W, H = 1080, 1920


def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def font(size, bold=True):
    # Anton om tilgjengelig, ellers DejaVu
    for p in ["assets/fonts/Anton-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def stat_bar(card, idx, outdir):
    img = Image.new("RGBA", (W, 360), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    label = card.get("label", ""); home = card.get("home", 0); away = card.get("away", 0)
    total = max(home + away, 1)
    d.text((W//2, 40), label, font=font(64), fill=(255, 255, 255, 255), anchor="mm")
    # home-bar
    bar_w = W - 160
    hw = int(bar_w * home / total)
    d.rounded_rectangle([80, 140, 80 + hw, 240], radius=20, fill=hex2rgb(PRIMARY) + (255,))
    d.rounded_rectangle([80 + hw, 140, 80 + bar_w, 240], radius=20, fill=hex2rgb(ACCENT) + (255,))
    d.text((100, 190), str(home), font=font(72), fill=(255,255,255,255), anchor="lm")
    d.text((W-100, 190), str(away), font=font(72), fill=(255,255,255,255), anchor="rm")
    path = os.path.join(outdir, f"gfx_{idx:02d}.png")
    img.save(path)
    return path


if __name__ == "__main__":
    job_id = sys.argv[1]
    outdir = f"build/{job_id}"
    script = json.load(open(f"{outdir}/script.json"))
    paths = []
    for i, card in enumerate(script.get("graphics", [])):
        if card.get("type") == "stat_bar":
            paths.append(stat_bar(card, i, outdir))
    json.dump(paths, open(f"{outdir}/graphics.json", "w"))
    print(f"{len(paths)} grafikk-kort generert.")

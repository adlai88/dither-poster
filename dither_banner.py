#!/usr/bin/env python3
"""
Simmer dithered release-banner generator.

Pipeline: source image -> zoom/cover-crop to square -> grayscale + contrast ->
2-tone Floyd-Steinberg dither -> composite white label chips (multi-line,
auto-wrap) -> export PNG.

Reusable workflow. Drive it with a JSON spec:

  { "src":"...", "out":"...", "size":1080, "zoom":3.5, "fx":0.5, "fy":0.42,
    "cell":2, "contrast":1.3, "palette":"cream",
    "margin":65, "gap":22,
    "chips":[
      {"text":"REFERRAL PROGRAM","font":"mono","size":32,"weight":"Medium","upper":true},
      {"text":"The referral program\\nis now live","font":"sans","size":74,"weight":"SemiBold"},
      ...
    ] }

Each chip auto-stacks below the previous (common left margin) unless it sets
explicit "x"/"y". "max_w" enables word-wrap to that pixel width.
"""
import argparse, glob, json, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

PALETTES = {
    "cream": ((47, 51, 0),  (251, 255, 204)),   # #2f3300 / #fbffcc
    "blue":  ((20, 20, 20), (122, 162, 247)),   # terminal-black / terminal-blue
    "green": ((20, 20, 20), (158, 206, 106)),   # terminal-black / terminal-green
    "amber": ((20, 20, 20), (224, 175, 104)),   # terminal-black / terminal-amber
    "mono":  ((20, 20, 20), (201, 201, 201)),   # terminal-black / terminal-text
}
GEIST_DIR = os.path.expanduser("~/Library/Fonts")

PIXEL_FONT = "/tmp/GeistPixel-Square.ttf"

def font_path(family="sans", weight="Medium"):
    if family == "pixel":
        return PIXEL_FONT
    name = "GeistMono" if family == "mono" else "Geist"
    for w in (weight, "Medium", "SemiBold", "Regular"):
        hit = glob.glob(os.path.join(GEIST_DIR, f"{name}-{w}.otf"))
        if hit:
            return hit[0]
    return "/System/Library/Fonts/Helvetica.ttc"

def zoom_crop(im, size, zoom, fx, fy):
    im = ImageOps.exif_transpose(im).convert("RGB")
    w, h = im.size
    scale = max(size / w, size / h) * zoom
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    w, h = im.size
    left = max(0, min(round((w - size) * fx), w - size))
    top  = max(0, min(round((h - size) * fy), h - size))
    return im.crop((left, top, left + size, top + size))

def dither(im, cell, contrast, brightness, dark, light):
    g = im.convert("L")
    if contrast != 1.0:
        g = ImageEnhance.Contrast(g).enhance(contrast)
    if brightness != 1.0:
        g = ImageEnhance.Brightness(g).enhance(brightness)
    size = g.size[0]
    if cell > 1:
        small = g.resize((size // cell, size // cell), Image.LANCZOS)
        bw = small.convert("1").resize((size, size), Image.NEAREST)
    else:
        bw = g.convert("1")
    out = Image.new("RGB", bw.size)
    out.putdata([light if p else dark for p in bw.getdata()])
    return out

def wrap(draw, text, font, max_w):
    """Word-wrap honoring explicit \\n, to max_w pixels."""
    lines = []
    for para in text.split("\n"):
        if not max_w:
            lines.append(para); continue
        cur = ""
        for word in para.split(" "):
            trial = (cur + " " + word).strip()
            if draw.textlength(trial, font=font) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    return lines

def draw_chip(img, chip, default_x, y, pad_x, pad_y, radius, line_gap):
    draw = ImageDraw.Draw(img)
    text = chip["text"].upper() if chip.get("upper") else chip["text"]
    font = ImageFont.truetype(font_path(chip.get("font", "sans"),
                                        chip.get("weight", "Medium")),
                              chip.get("size", 48))
    x = chip.get("x", default_x)
    y = chip.get("y", y)
    lines = wrap(draw, text, font, chip.get("max_w"))
    # measure
    asc, desc = font.getmetrics()
    line_h = asc + desc
    widths = [draw.textlength(ln, font=font) for ln in lines]
    tw = max(widths) if widths else 0
    th = line_h * len(lines) + line_gap * (len(lines) - 1)
    bw, bh = tw + 2 * pad_x, th + 2 * pad_y
    draw.rounded_rectangle((x, y, x + bw, y + bh), radius=radius,
                           fill=tuple(chip.get("fill", (255, 255, 255))))
    tcol = tuple(chip.get("tcol", (0, 0, 0)))
    cy = y + pad_y
    for ln in lines:
        draw.text((x + pad_x, cy), ln, font=font, fill=tcol)
        cy += line_h + line_gap
    return y + bh

def render(spec):
    dark, light = PALETTES[spec.get("palette", "cream")]
    size = spec.get("size", 1080)
    base = zoom_crop(Image.open(spec["src"]), size, spec.get("zoom", 1.0),
                     spec.get("fx", 0.5), spec.get("fy", 0.5))
    img = dither(base, spec.get("cell", 2), spec.get("contrast", 1.3),
                 spec.get("brightness", 1.0), dark, light)
    margin = spec.get("margin", int(size * 0.06))
    gap = spec.get("gap", 22)
    pad_x = spec.get("pad_x", 24)
    pad_y = spec.get("pad_y", 14)
    radius = spec.get("radius", 6)
    line_gap = spec.get("line_gap", 6)
    y = margin
    for chip in spec["chips"]:
        bottom = draw_chip(img, chip, margin, y, pad_x, pad_y, radius, line_gap)
        y = bottom + gap
    img.save(spec["out"])
    print("saved", spec["out"], img.size, spec.get("palette", "cream"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", help="JSON spec file")
    # single-chip convenience mode:
    ap.add_argument("--src"); ap.add_argument("--out")
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--fx", type=float, default=0.5)
    ap.add_argument("--fy", type=float, default=0.5)
    ap.add_argument("--palette", default="cream")
    ap.add_argument("--title", default="New Feature")
    args = ap.parse_args()
    if args.spec:
        render(json.load(open(args.spec)))
    else:
        render({"src": args.src, "out": args.out, "zoom": args.zoom,
                "fx": args.fx, "fy": args.fy, "palette": args.palette,
                "chips": [{"text": args.title, "font": "sans", "size": 52}]})

if __name__ == "__main__":
    main()

# Dither Poster

A one-screen, brand-locked poster maker for Simmer feature announcements. Drop an
image, edit the copy, and it renders a dithered 2-tone poster in the Simmer kit.
Everything runs in the browser — **the image never leaves your machine**.

**Live:** https://adlai88.github.io/dither-poster/

## Use it

Use the hosted version above, or run it locally: open `index.html` in a browser
(double-click works — no server, no install, works offline). Or serve the folder:
`python3 -m http.server` then open `localhost:8000`.

1. **Drop an image** (or click "Use sample image").
2. **Drag on the preview** to set the focal point.
3. Tune **Zoom / Contrast / Dither** size.
4. Pick a **Format** (1:1, 4:5, 16:9) and **Palette**.
5. Edit the **Boxes** — text, font, weight, size. **Drag boxes** on the preview to
   reposition. Add/remove boxes as needed.
6. **Download PNG.**

It opens pre-loaded with the referral-announcement template so you start by editing,
not from a blank canvas.

## The brand lock

The constraint is the feature — a teammate can't make an off-brand poster, only an
on-brand one, fast. Locked to:

- **Fonts:** Geist Sans, Geist Mono, Geist Pixel (weights only — no other families)
- **Palettes:** cream, blue, green, amber, mono (DESIGN.md tokens — no arbitrary hex)
- **Chips:** white box / black text, 12px radius
- **Dither:** fixed Floyd–Steinberg 2-tone

## How it works

Single `index.html`, no dependencies. The dither pipeline (canvas): cover-crop with
zoom/focal → grayscale + contrast → downscale by the dither cell → Floyd–Steinberg →
map to the 2-tone palette → nearest-neighbour upscale → composite the white chips.

Fonts are bundled in `fonts/` (Geist is SIL OFL). `assets/sample.jpg` is a generated
placeholder, safe to redistribute.

## Adding to the kit

- **Palette:** add an entry to `PALETTES` in `index.html` (`{dark:[r,g,b], light:[r,g,b], sw:'#hex'}`).
- **Format:** add to `FORMATS` (e.g. `[1920,368]`).
- **Batch / headless:** not built. If it's ever needed, reuse this file's JS dither
  engine (Node + `node-canvas`, or a Playwright script driving the page) — don't
  re-port it. One source of truth.

## Not yet built (intentional v1 scope cap)

- Wide formats (X banner / X article) render, but reuse the vertical box stack — no
  horizontal default layout (boxes clamp into bounds; reposition by hand).
- Saved projects / templates gallery — out of scope; keep it one screen.
- Animated export and an erase-to-background tool — parked until there's a need.

import pathlib
#!/usr/bin/env python3
"""
Shadow Ninja — 5-second cinematic intro (1280x720, 24 fps, 120 frames)

Timeline:
  0.0-2.0s  The ninja stands on a cliff at night, full moon behind him,
            scarf streaming in the wind (idle sprite + hand-drawn scarf
            ribbon), slow camera push-in, drifting mist and leaves.
  2.0-3.0s  He runs to the cliff edge (run cycle).
  3.0-5.0s  He leaps off into the dark forest below (jump -> fall frames,
            forward tumble tilt, camera pans right and tilts down with
            parallax separation), fading to black.

Art: the generated ninja sprite sheet + the 3 parallax background
layers from the earlier steps. Encoded with OpenCV (mp4v).
Run:  python3 render_intro.py
"""
import math, os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
OUT = f"{ROOT}/assets/video/shadow-ninja-intro.mp4"
W, H, FPS, FRAMES = 1280, 720, 24, 120

# ------------------------------------------------------------------ assets
sheet = Image.open(f"{ROOT}/assets/sprites/shadow-ninja-v2.png").convert("RGBA")
def sprite(frame, size=184):
    cell = sheet.crop(((frame % 5) * 128, (frame // 5) * 128,
                       (frame % 5) * 128 + 128, (frame // 5) * 128 + 128))
    return cell.resize((size, size), Image.LANCZOS)

layers = []
for name in ("far-mountains", "mid-bamboo-forest", "near-trees"):
    im = Image.open(f"{ROOT}/assets/backgrounds/{name}.png").convert("RGBA")
    layers.append(im.resize((2560, 1440), Image.LANCZOS))   # oversize for camera moves

# ------------------------------------------------------------------ sky base
sky = Image.new("RGB", (W, H))
sd = ImageDraw.Draw(sky, "RGBA")
for y in range(H):
    k = y / H
    sd.line([(0, y), (W, y)], fill=(int(16 + 22 * k), int(15 + 14 * k), int(42 + 34 * k)))
for i in range(130):  # deterministic stars
    x = (i * 613) % W; y = (i * 389) % 330
    r = 1.6 if i % 7 == 0 else 1.0
    sd.ellipse([x - r, y - r, x + r, y + r], fill=(220, 222, 255, 90 + (i % 5) * 26))

# vignette (reused every frame)
vign = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vign)
vd.ellipse([-360, -200, W + 360, H + 200], fill=255)
vign = vign.filter(ImageFilter.GaussianBlur(180))
black = Image.new("RGBA", (W, H), (0, 0, 0, 255))

def cliff_top(x):
    """Height of the cliff surface at world x (gentle rise to the edge)."""
    return 512 - 34 * max(0.0, min(1.0, (x + 200) / 850.0))

def draw_cliff(d, camx, camy):
    pts = [(-260, 518), (648, 480), (706, 548), (782, 900), (-260, 900)]
    pts = [(x - camx, y - camy) for (x, y) in pts]
    d.polygon(pts, fill=(7, 8, 17))
    # rocky facets + edge highlight
    for (x, y, w2, h2) in [(60, 610, 150, 26), (300, 680, 190, 30), (540, 590, 120, 22), (-60, 700, 170, 30)]:
        d.polygon([(x - camx, y - camy), (x + w2 - camx, y + 8 - camy), (x + w2 - 30 - camx, y + h2 - camy)], fill=(13, 15, 28))
    d.line([(pts[0][0], pts[0][1]), (pts[1][0], pts[1][1])], fill=(42, 46, 74), width=4)
    # a windswept pine branch reaching in from the left
    d.line([(-20 - camx, 250 - camy), (150 - camx, 300 - camy)], fill=(7, 8, 17), width=17)
    for i in range(7):
        bx = 20 + i * 20 - camx; by = 262 + i * 6 - camy
        d.ellipse([bx - 30, by - 13, bx + 30, by + 13], fill=(10, 14, 26))

def draw_scarf(d, neck, t, wind, falling=False):
    """Extra animated scarf ribbon streaming from the neck (the sprite's
    own scarf is short; this one sells the wind)."""
    x, y = neck
    pts = [(x, y)]
    n = 5
    for i in range(1, n + 1):
        px = x - i * (17 + wind * 3)
        py = y + math.sin(t * 5.2 - i * 0.9) * (4 + i * 2.4) + i * (2.2 if not falling else -5)
        pts.append((px, py))
    for i in range(n):
        wdt = 11 - i * 1.8
        d.line([pts[i], pts[i + 1]], fill=(196, 34, 52) if i % 2 == 0 else (158, 24, 40), width=int(wdt))
        d.ellipse([pts[i][0] - wdt / 2, pts[i][1] - wdt / 2, pts[i][0] + wdt / 2, pts[i][1] + wdt / 2],
                  fill=(196, 34, 52) if i % 2 == 0 else (158, 24, 40))

def paste_rotated(base, spr, center, angle_deg):
    if angle_deg:
        spr = spr.rotate(angle_deg, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(spr, (int(center[0] - spr.width / 2), int(center[1] - spr.height / 2)))

# ------------------------------------------------------------------ render
writer = cv2.VideoWriter(OUT, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
assert writer.isOpened(), "VideoWriter failed to open"

IDLE = [0, 1, 2, 3]
RUN = [4, 5, 6, 7, 8, 9]

for f in range(FRAMES):
    t = f / FPS
    img = sky.copy().convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")

    # ---- camera: slow push-in, then pans right/down following the leap
    if t < 3.0:
        camx = 26 * t                      # gentle drift right
        camy = 6 * math.sin(t * 0.7)
        zoom = 1.0 + 0.012 * t
    else:
        lt = t - 3.0
        camx = 78 + 300 * lt               # chase the ninja
        camy = 150 * lt * lt               # tilt down into the valley
        zoom = 1.036

    # ---- moon (behind everything, drifts least)
    mx, my = 972 - camx * 0.05, 138 - camy * 0.05
    d.ellipse([mx - 108, my - 108, mx + 108, my + 108], fill=(240, 234, 205, 26))
    d.ellipse([mx - 76, my - 76, mx + 76, my + 76], fill=(243, 238, 214, 255))
    d.ellipse([mx - 58, my - 30, mx - 26, my + 2], fill=(228, 220, 192, 255))   # crater shading
    d.ellipse([mx + 12, my + 22, mx + 36, my + 46], fill=(228, 220, 192, 255))

    # ---- parallax layers (far 0.15 / mid 0.42 / near 0.72 of camera)
    for li, (layer, factor) in enumerate(zip(layers, (0.15, 0.42, 0.72))):
        cx = min(int(240 + camx * factor), layer.width - W)    # clamp: never crop
        cy = min(int(230 + camy * (0.35 + li * 0.22)), layer.height - H)  # outside the art
        img.alpha_composite(layer.crop((cx, cy, cx + W, cy + H)), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")

    # ---- drifting mist: drawn on its own layer and blurred, so it
    # reads as soft fog instead of hard-edged ovals
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for i, (my2, sp, al) in enumerate([(486, 9, 15), (576, 14, 12), (652, 20, 10)]):
        for k in range(3):
            cx = ((k * 620 + f * sp + i * 210) % (W + 640)) - 320
            md.ellipse([cx - 330, my2 - camy * 0.4 - 16, cx + 330, my2 - camy * 0.4 + 16], fill=(172, 166, 226, al))
    img.alpha_composite(mist.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(img, "RGBA")

    draw_cliff(d, camx, camy)

    # ---- ninja choreography
    angle = 0
    if t < 2.0:                                   # STAND — idle, scarf in the wind
        nx, ny = 452, None
        nyy = cliff_top(nx)
        frame = IDLE[int(t * 6) % 4]              # idle @ 6 fps
        wind = 1.6 + math.sin(t * 1.4) * 0.9      # gusting
        falling = False
    elif t < 3.0:                                 # RUN to the edge
        rt = t - 2.0
        nx = 452 + 176 * rt
        nyy = cliff_top(nx)
        frame = RUN[int(rt * 12) % 6]             # run @ 12 fps
        wind = 2.6
        falling = False
    else:                                         # LEAP into the forest
        lt = t - 3.0
        nx = 628 + 330 * lt
        nyy = cliff_top(650) - (430 * lt - 560 * lt * lt)   # up, then plunging
        frame = 10 if lt < 0.38 else 12                     # jump -> fall frame
        angle = -8 - 30 * max(0.0, lt - 0.3)                # forward tumble tilt
        wind = 3.4
        falling = lt > 0.35
        if lt < 0.12:                             # dust burst at takeoff
            for i in range(10):
                px = 636 - camx - i * 7; py = cliff_top(650) - camy - 4 - (i % 4) * 5
                d.ellipse([px - 5, py - 3, px + 5, py + 3], fill=(150, 148, 180, 130 - i * 11))

    scale = 1.0 if t < 3.0 else max(0.74, 1.0 - (t - 3.0) * 0.13)   # falls away slightly
    size = int(184 * scale * zoom)
    spr = sprite(frame, size)
    sx = nx - camx
    sy = nyy - camy
    # scarf first (behind the body), anchored at the neck of the sprite
    neck = (sx - size * 0.02, sy - size * 0.54)  # sprite neck: cell (62,52)/128 mapped through the paste offset
    draw_scarf(d, neck, t, wind, falling)
    paste_rotated(img, spr, (sx, sy - size / 2 + size * 0.06), angle)
    d = ImageDraw.Draw(img, "RGBA")

    # ---- wind-blown leaves / embers
    for i in range(22):
        px = (i * 173 + f * (2.2 + (i % 4)) * 2.2) % (W + 40) - 20
        py = (i * 97 + int(30 * math.sin(f * 0.11 + i))) % H
        if py < H * 0.75:
            d.ellipse([px - 3, py - 1.6, px + 3, py + 1.6], fill=(120, 140, 190, 110))
    for i in range(10):  # faint fireflies low in the forest
        px = (i * 211 + int(24 * math.sin(f * 0.07 + i * 2.0))) % W
        py = 560 + (i * 53) % 130 - int(camy * 0.6)
        glow = 90 + int(70 * math.sin(f * 0.35 + i * 1.7))
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 196, 110, max(20, glow)))

    # ---- letterbox bars + vignette + fades
    img = Image.composite(img, black, vign) if False else img
    img.paste(black, (0, 0), vign.point(lambda v: 255 - v)) if False else None
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, 46], fill=(0, 0, 0, 255))
    d.rectangle([0, H - 46, W, H], fill=(0, 0, 0, 255))
    # soft vignette via pre-rendered mask
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img = Image.composite(img, Image.blend(img, dark, 0.55), vign)
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, 46], fill=(0, 0, 0, 255))
    d.rectangle([0, H - 46, W, H], fill=(0, 0, 0, 255))

    fade = 1.0
    if f < 10: fade = f / 10.0                    # fade in
    if f >= FRAMES - 16: fade = max(0.0, (FRAMES - 1 - f) / 16.0)   # fade out
    if fade < 1.0:
        img = Image.blend(dark, img, fade)

    writer.write(cv2.cvtColor(np.asarray(img.convert("RGB")), cv2.COLOR_RGB2BGR))
    if f % 30 == 0: print(f"frame {f}/{FRAMES}")

writer.release()
# poster frame for preview
poster = sky.copy()
poster.save(f"{ROOT}/ninja-intro/_render-check.png")
print("saved", OUT, f"({os.path.getsize(OUT)//1024} KB)")

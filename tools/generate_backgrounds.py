#!/usr/bin/env python3
"""
Misty ancient Japanese forest at dusk — background set + tileset
----------------------------------------------------------------
Outputs (in this folder):
  far-mountains.png       1920x1080, transparent, seamless horizontal tile
  mid-bamboo-forest.png   1920x1080, transparent, seamless horizontal tile
  near-trees.png          1920x1080, transparent, seamless horizontal tile
  tileset.png             512x256 atlas = 8x4 tiles of 64x64, transparent
  tileset.json            tile name -> atlas coordinates
  _preview-composite.png  the 3 layers stacked over a dusk sky (QA only)
  _preview-tileset.png    tileset over a checkerboard (QA only)

Seamlessness strategy:
  * ridgelines / ground lines are sums of sines whose frequencies are
    whole numbers of cycles across 1920 px -> left edge == right edge
  * mid / near layers are built from a motif segment (320 / 480 px)
    that repeats a whole number of times across 1920, with no shape
    crossing a segment boundary
Palette: dark blues & purples; warm orange only for lantern light.
Run:  python3 generate_background.py
"""
import json, pathlib, math
from PIL import Image, ImageDraw

W, H = 1920, 1080
OUT = str(pathlib.Path(__file__).resolve().parent.parent / "assets" / "backgrounds")

# ------------------------------------------------------------------ palette
FAR_BACK  = (64, 55, 118, 165)   # haziest ridge
FAR_MID   = (46, 40, 92, 205)
FAR_FRONT = (30, 27, 66, 255)
MIST      = (168, 160, 220, 42)
BAMBOO_FAR  = (44, 54, 96, 150)
BAMBOO_MID  = (32, 42, 80, 200)
BAMBOO_NEAR = (20, 28, 58, 255)
NEAR_TREE   = (9, 11, 26, 255)
NEAR_LEAF   = (15, 19, 40, 255)
GROUND_MID  = (17, 21, 44, 255)
GROUND_NEAR = (6, 8, 18, 255)

def ridge_y(x, base, terms):
    """Periodic ridgeline height (whole cycles across W -> seamless)."""
    y = base
    for cycles, amp, phase in terms:
        y += amp * math.sin(2 * math.pi * cycles * x / W + phase)
    return y

def draw_ridge(d, base, terms, color):
    pts = [(x, ridge_y(x, base, terms)) for x in range(0, W + 8, 8)]
    d.polygon(pts + [(W, H), (0, H)], fill=color)

def mist_band(d, y, h, offset=0):
    """Soft repeating mist blobs (segment 480 px, tiled)."""
    for seg in range(-1, 5):
        for (rx, rw, rh, a) in [(60, 300, 34, 46), (230, 360, 26, 34), (390, 240, 40, 26)]:
            cx = seg * 480 + rx + offset
            d.ellipse([cx - rw / 2, y - rh / 2, cx + rw / 2, y + rh / 2], fill=(168, 160, 220, a))

def pine(d, x, y, s, color):
    d.rectangle([x - 1.5 * s / 10, y - 6 * s / 10, x + 1.5 * s / 10, y], fill=color)
    for i, wdt in enumerate((16, 12, 8)):
        yy = y - 4 * s / 10 - i * 5 * s / 10
        d.polygon([(x - wdt * s / 10, yy), (x + wdt * s / 10, yy), (x, yy - 7 * s / 10)], fill=color)

# ==================================================================
# LAYER 1 — FAR MOUNTAINS
# ==================================================================
def far_mountains():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_ridge(d, 560, [(3, 95, 0.4), (7, 42, 1.7), (13, 16, 4.0)], FAR_BACK)
    mist_band(d, 640, 60)
    draw_ridge(d, 720, [(4, 80, 2.2), (9, 34, 0.6), (17, 12, 2.9)], FAR_MID)
    # sparse pines standing on the middle ridge (period 240 px)
    for i in range(8):
        x = i * 240 + 90
        pine(d, x, ridge_y(x, 720, [(4, 80, 2.2), (9, 34, 0.6), (17, 12, 2.9)]) + 6, 26, FAR_MID)
    mist_band(d, 830, 70, offset=140)
    draw_ridge(d, 880, [(5, 62, 5.1), (11, 26, 3.3), (23, 9, 1.1)], FAR_FRONT)
    for i in range(8):
        x = i * 240 + 200
        pine(d, x, ridge_y(x, 880, [(5, 62, 5.1), (11, 26, 3.3), (23, 9, 1.1)]) + 6, 38, FAR_FRONT)
    img.save(f"{OUT}/far-mountains.png")
    print("far-mountains.png")

# ==================================================================
# LAYER 2 — MID BAMBOO FOREST  (320 px motif x 6)
# ==================================================================
# (x in segment, width, top y, shade index, leaf phase)
_STALKS = [(18, 7, 300, 0, 0), (52, 9, 240, 1, 2), (88, 6, 340, 0, 4), (120, 11, 210, 2, 1),
           (158, 7, 290, 1, 5), (190, 9, 250, 2, 3), (226, 6, 330, 0, 2), (258, 10, 230, 1, 0),
           (292, 7, 300, 2, 4), (306, 5, 360, 0, 1)]
_SHADES = [BAMBOO_FAR, BAMBOO_MID, BAMBOO_NEAR]

def _bamboo_segment(d, ox):
    for (sx, wdt, top, shade, phase) in _STALKS:
        x = ox + sx
        col = _SHADES[shade]
        d.rectangle([x - wdt / 2, top, x + wdt / 2, H], fill=col)
        # node rings + leaves, kept inside the segment so tiling is clean
        yy = top + 46
        side = 1 if phase % 2 == 0 else -1
        while yy < 1010:
            d.line([(x - wdt / 2, yy), (x + wdt / 2, yy)], fill=(10, 14, 30, 160), width=3)
            lx = min(max(x + side * 34, ox + 26), ox + 294)
            d.polygon([(x, yy - 4), (lx, yy - 13), (x + side * 8, yy + 3)], fill=col)
            side = -side
            yy += 78

def mid_bamboo():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for seg in range(6):
        _bamboo_segment(d, seg * 320)
    mist_band(d, 560, 60, offset=60)
    mist_band(d, 800, 70, offset=260)
    # ground shadow the bamboo rises from (periodic -> seamless)
    pts = [(x, 990 + 14 * math.sin(2 * math.pi * 6 * x / W + 1.0)) for x in range(0, W + 8, 8)]
    d.polygon(pts + [(W, H), (0, H)], fill=GROUND_MID)
    img.save(f"{OUT}/mid-bamboo-forest.png")
    print("mid-bamboo-forest.png")

# ==================================================================
# LAYER 3 — NEAR TREES  (480 px motif x 4)
# ==================================================================
def _near_segment(d, ox, variant=0):
    # Two alternating variants (A/B/A/B) -> the layer's true period is
    # 960 px, so it still tiles seamlessly but doesn't look stamped.
    if variant == 0:
        cx, sx = ox + 240, ox + 66
        canopy = [(-102, 262, 70), (-18, 208, 92), (96, 252, 66), (-38, 282, 58),
                  (52, 296, 50), (-128, 300, 42), (128, 300, 40)]
        strands = (cx - 138, cx - 62, cx + 72, cx + 142, sx + 34)
    else:
        cx, sx = ox + 196, ox + 392
        canopy = [(-88, 238, 62), (6, 192, 84), (104, 236, 58), (-22, 268, 66),
                  (66, 282, 44), (-118, 282, 38), (132, 276, 36)]
        strands = (cx - 122, cx - 40, cx + 88, cx + 138, sx - 30)
    # main tree: tapered trunk + two big branches (all inside the segment)
    d.polygon([(cx - 26, H), (cx - 9, 330), (cx + 7, 330), (cx + 24, H)], fill=NEAR_TREE)
    d.polygon([(cx - 6, 430), (cx - 120, 300), (cx - 104, 282), (cx + 2, 400)], fill=NEAR_TREE)
    d.polygon([(cx + 6, 400), (cx + 128, 276), (cx + 112, 258), (cx - 2, 372)], fill=NEAR_TREE)
    # irregular canopy: overlapping blobs, no concentric "target" centre
    for (dx, ly, r) in canopy:
        lx = cx + dx
        d.ellipse([lx - r, ly - r * .68, lx + r, ly + r * .68], fill=NEAR_LEAF)
    for (dx, ly, r) in [(-52, 236, 44), (38, 222, 38), (2, 272, 46)]:
        lx = cx + dx
        d.ellipse([lx - r, ly - r * .66, lx + r, ly + r * .66], fill=NEAR_TREE)
    # slim secondary tree
    d.polygon([(sx - 9, H), (sx - 3, 520), (sx + 4, 520), (sx + 10, H)], fill=NEAR_TREE)
    for (lx, ly, r) in [(sx - 30, 500, 44), (sx + 26, 478, 50), (sx, 442, 42)]:
        d.ellipse([lx - r, ly - r * .7, lx + r, ly + r * .7], fill=NEAR_LEAF)
    # hanging leaf strands from the canopy
    for hx in strands:
        for i in range(5):
            yy = 330 + i * 26
            d.ellipse([hx - 7, yy, hx + 7, yy + 12], fill=NEAR_LEAF)

def near_trees():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for seg in range(4):
        _near_segment(d, seg * 480, variant=seg % 2)
    # foreground ground (periodic -> seamless) + bush humps per segment
    pts = [(x, 1002 + 12 * math.sin(2 * math.pi * 8 * x / W + 2.0)) for x in range(0, W + 8, 8)]
    d.polygon(pts + [(W, H), (0, H)], fill=GROUND_NEAR)
    for seg in range(4):
        for (bx, br) in [(110, 56), (330, 70), (440, 44)]:
            x = seg * 480 + bx
            d.ellipse([x - br, 1006 - br * .5, x + br, 1006 + br * .6], fill=GROUND_NEAR)
    # grass blades along the bottom edge
    for i in range(96):
        x = i * 20 + (8 if i % 2 else 2)
        d.line([(x, H), (x + 5, H - 26 - (i % 5) * 5)], fill=NEAR_LEAF, width=4)
    img.save(f"{OUT}/near-trees.png")
    print("near-trees.png")

# ==================================================================
# TILESET — 8 x 4 tiles of 64 px, drawn at 4x then downscaled
# ==================================================================
TS = 4                      # supersample
TCELL = 64 * TS
tiles_img = Image.new("RGBA", (8 * TCELL, 4 * TCELL), (0, 0, 0, 0))
td = ImageDraw.Draw(tiles_img)

STONE   = (58, 63, 92, 255)
STONE_D = (38, 41, 64, 255)
STONE_L = (92, 99, 132, 255)
MOSS    = (52, 138, 104, 255)
MOSS_D  = (34, 96, 74, 255)
WOOD    = (96, 70, 48, 255)
WOOD_D  = (62, 44, 32, 255)
WOOD_L  = (128, 98, 66, 255)
STEEL   = (168, 176, 204, 255)
STEEL_D = (96, 102, 128, 255)
TORII   = (158, 46, 56, 255)
TORII_D = (110, 30, 40, 255)
GLOW    = (255, 176, 84, 255)

def T(col, row, p):  # tile-local 64-space -> atlas pixels
    return ((col * 64 + p[0]) * TS, (row * 64 + p[1]) * TS)

def trect(col, row, box, color):
    td.rectangle([T(col, row, (box[0], box[1])), T(col, row, (box[2], box[3]))], fill=color)

def tpoly(col, row, pts, color):
    td.polygon([T(col, row, p) for p in pts], fill=color)

def tline(col, row, pts, color, w=2):
    td.line([T(col, row, p) for p in pts], fill=color, width=int(w * TS), joint="curve")

def tellipse(col, row, c, rx, ry, color):
    td.ellipse([T(col, row, (c[0] - rx, c[1] - ry)), T(col, row, (c[0] + rx, c[1] + ry))], fill=color)

def stone_base(c, r, top=False, left=False, right=False, bottom=False):
    trect(c, r, (2, 2, 62, 62), STONE_D)
    trect(c, r, (4, 4, 60, 60), STONE)
    tline(c, r, [(4, 22), (60, 22)], STONE_D, 1.6); tline(c, r, [(4, 42), (60, 42)], STONE_D, 1.6)
    tline(c, r, [(32, 4), (32, 22)], STONE_D, 1.6); tline(c, r, [(18, 42), (18, 60)], STONE_D, 1.6)
    tline(c, r, [(46, 22), (46, 42)], STONE_D, 1.6)                                  # block seams
    tline(c, r, [(10, 50), (20, 44), (26, 50)], STONE_D, 1.4)                        # crack
    if top:    trect(c, r, (2, 2, 62, 9), STONE_L)
    if left:   trect(c, r, (2, 2, 9, 62), STONE_L)
    if right:  trect(c, r, (55, 2, 62, 62), STONE_D)
    if bottom: trect(c, r, (2, 55, 62, 62), STONE_D)

def moss_on(c, r, heavy=False):
    n = 7 if heavy else 4
    for i in range(n):
        x = 8 + i * 8
        tellipse(c, r, (x, 4), 6, 4.5, MOSS)
    tellipse(c, r, (16, 10), 4, 6, MOSS_D); tellipse(c, r, (42, 9), 3.4, 5, MOSS_D)
    if heavy:
        tellipse(c, r, (8, 26), 4, 9, MOSS); tellipse(c, r, (56, 32), 4, 10, MOSS_D)

def plank(c, r, box, vertical=False):
    trect(c, r, box, WOOD)
    if vertical:
        tline(c, r, [(box[0] + 3, box[1] + 3), (box[0] + 3, box[3] - 3)], WOOD_L, 1.2)
        tline(c, r, [(box[2] - 4, box[1] + 4), (box[2] - 4, box[3] - 4)], WOOD_D, 1.4)
    else:
        tline(c, r, [(box[0] + 3, box[1] + 3), (box[2] - 3, box[1] + 3)], WOOD_L, 1.2)
        tline(c, r, [(box[0] + 4, box[3] - 4), (box[2] - 4, box[3] - 4)], WOOD_D, 1.4)

def build_tileset():
    # ---- row 0: stone & moss terrain ----
    stone_base(0, 0, top=True);  moss_on(0, 0)                       # stone_top (mossy lip)
    stone_base(1, 0)                                                 # stone_fill
    stone_base(2, 0, top=True, left=True)                            # stone_left_edge
    stone_base(3, 0, top=True, right=True)                           # stone_right_edge
    stone_base(4, 0, bottom=True)                                    # stone_bottom_edge
    stone_base(5, 0, top=True);  moss_on(5, 0, heavy=True)           # mossy_stone_top
    stone_base(6, 0);            moss_on(6, 0, heavy=True)           # mossy_wall
    trect(6, 0, (2, 40, 62, 62), STONE_D)
    stone_base(7, 0, top=True);  moss_on(7, 0)                       # mossy_wall_top
    trect(7, 0, (20, 18, 44, 46), STONE_D); trect(7, 0, (24, 22, 40, 42), STONE)  # carved inset

    # ---- row 1: wood, bridges, crates ----
    for c in range(3):  # bridge deck left / mid / right
        plank(c, 1, (0, 24, 64, 38)); plank(c, 1, (0, 38, 64, 46))
        tline(c, 1, [(0, 20), (64, 20)], WOOD_D, 2.4); tline(c, 1, [(0, 50), (64, 50)], WOOD_D, 2.4)  # ropes
    trect(0, 1, (4, 38, 12, 64), WOOD_D)                             # bridge_left post
    trect(2, 1, (52, 38, 60, 64), WOOD_D)                            # bridge_right post
    tline(1, 1, [(6, 50), (32, 64)], WOOD_D, 3); tline(1, 1, [(58, 50), (32, 64)], WOOD_D, 3)  # mid brace
    plank(3, 1, (0, 8, 64, 24)); plank(3, 1, (0, 24, 64, 34))       # wooden platform top
    for c in (4,):                                                   # planks fill
        plank(c, 1, (0, 0, 64, 16)); plank(c, 1, (0, 16, 64, 32)); plank(c, 1, (0, 32, 64, 48)); plank(c, 1, (0, 48, 64, 64))
    def crate(c, cracked=False):
        trect(c, 1, (8, 8, 56, 56), WOOD); trect(c, 1, (8, 8, 56, 14), WOOD_L); trect(c, 1, (8, 50, 56, 56), WOOD_D)
        trect(c, 1, (8, 8, 14, 56), WOOD_D); trect(c, 1, (50, 8, 56, 56), WOOD_D)
        tline(c, 1, [(12, 12), (52, 52)], WOOD_D, 3); tline(c, 1, [(52, 12), (12, 52)], WOOD_D, 3)
        if cracked:
            tline(c, 1, [(30, 10), (26, 24), (34, 36), (28, 54)], (30, 20, 14, 255), 2)
    crate(5); crate(6, cracked=True)
    # wooden sign / spare planks tile
    plank(7, 1, (6, 14, 58, 26)); plank(7, 1, (6, 30, 58, 42)); trect(7, 1, (28, 42, 36, 62), WOOD_D)

    # ---- row 2: hazards + torii (2x2 assembled) + saw ----
    for flip in (0, 1):  # spikes up (col0), spikes down (col1)
        c = flip
        ys = (62, 14) if flip == 0 else (2, 50)
        for i in range(4):
            x = 4 + i * 15
            if flip == 0:
                tpoly(c, 2, [(x, 62), (x + 7, 14), (x + 14, 62)], STEEL_D)
                tpoly(c, 2, [(x, 62), (x + 7, 14), (x + 7, 62)], STEEL)
            else:
                tpoly(c, 2, [(x, 2), (x + 7, 50), (x + 14, 2)], STEEL_D)
                tpoly(c, 2, [(x, 2), (x + 7, 50), (x + 7, 2)], STEEL)
        trect(c, 2, (2, 58, 62, 64) if flip == 0 else (2, 0, 62, 6), STONE_D)
    def saw(c, r, rad):
        cx, cy = 32, 32
        teeth = []
        for i in range(24):
            ang = i / 24 * 2 * math.pi
            rr = rad if i % 2 == 0 else rad + 6
            teeth.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        tpoly(c, r, teeth, STEEL_D)
        tellipse(c, r, (cx, cy), rad - 5, rad - 5, STEEL)
        tellipse(c, r, (cx, cy), 6, 6, STEEL_D); tellipse(c, r, (cx, cy), 2.6, 2.6, GLOW)
    saw(2, 2, 22)                                                    # saw blade
    saw(3, 2, 15); trect(3, 2, (28, 44, 36, 64), STONE_D)            # saw on mount
    # torii gate occupies (4,2)(5,2)(4,3)? -> drawn as 2 cols on row 2 + pillars row 3 handled below
    def torii_part(c, r, qx, qy):
        # assembled gate space is 128x128; this tile shows quadrant (qx,qy)
        def tp(p): return (p[0] - qx * 64, p[1] - qy * 64)
        def rct(box):
            td.rectangle([T(c, r, tp((box[0], box[1]))), T(c, r, tp((box[2], box[3])))], fill=TORII)
        def rctd(box, col=TORII_D):
            td.rectangle([T(c, r, tp((box[0], box[1]))), T(c, r, tp((box[2], box[3])))], fill=col)
        rct((4, 10, 124, 22)); rctd((4, 19, 124, 22))                # top beam (kasagi)
        rct((16, 30, 112, 40))                                       # second beam (nuki)
        rct((56, 20, 72, 40))                                        # centre strut
        rct((26, 22, 38, 128)); rct((90, 22, 102, 128))              # pillars
        rctd((34, 22, 38, 128)); rctd((98, 22, 102, 128))
    torii_part(4, 2, 0, 0); torii_part(5, 2, 1, 0)                   # torii top L / R
    torii_part(6, 2, 0, 1); torii_part(7, 2, 1, 1)                   # torii bottom L / R (also on row 2 of atlas)

    # ---- row 3: lanterns & nature decor ----
    # hanging lantern
    tline(0, 3, [(32, 0), (32, 10)], STEEL_D, 2)
    trect(0, 3, (20, 10, 44, 16), TORII_D)
    trect(0, 3, (22, 16, 42, 42), GLOW); trect(0, 3, (22, 16, 42, 20), (255, 214, 140, 255))
    tline(0, 3, [(22, 29), (42, 29)], TORII_D, 1.6)
    trect(0, 3, (20, 42, 44, 47), TORII_D); tline(0, 3, [(32, 47), (32, 58)], TORII, 2.4)
    # standing lantern (stone post + glowing head)
    trect(1, 3, (29, 30, 35, 56), STONE_D); trect(1, 3, (22, 56, 42, 62), STONE_D)
    trect(1, 3, (22, 14, 42, 30), GLOW); trect(1, 3, (19, 9, 45, 14), STONE_D); trect(1, 3, (19, 30, 45, 34), STONE_D)
    tline(1, 3, [(32, 2), (32, 9)], STONE_D, 2); tellipse(1, 3, (32, 22), 13, 10, (255, 176, 84, 60))
    # bamboo shoots decor
    for (x, wdt, top) in [(14, 7, 12), (30, 9, 4), (47, 7, 16)]:
        trect(2, 3, (x - wdt / 2, top, x + wdt / 2, 64), BAMBOO_NEAR)
        tline(2, 3, [(x - wdt / 2, top + 18), (x + wdt / 2, top + 18)], STONE_D, 1.6)
        tpoly(2, 3, [(x, top + 22), (x + 18, top + 14), (x + 4, top + 28)], BAMBOO_MID)
    # foliage cluster
    for (x, y, r) in [(18, 22, 12), (34, 16, 14), (48, 24, 11), (26, 34, 12), (44, 38, 10)]:
        tellipse(3, 3, (x, y), r, r * .75, NEAR_LEAF)
    tellipse(3, 3, (30, 24), 5, 3.4, MOSS)
    # single rock
    tpoly(4, 3, [(8, 54), (18, 34), (36, 26), (52, 36), (58, 54)], STONE)
    tpoly(4, 3, [(18, 34), (36, 26), (40, 40), (22, 44)], STONE_L)
    tellipse(4, 3, (38, 30), 6, 3.6, MOSS)
    # hanging vines
    for x in (14, 30, 46):
        tline(5, 3, [(x, 0), (x + 3, 26), (x - 2, 48)], MOSS_D, 2.6)
        tellipse(5, 3, (x + 4, 18), 4.4, 3, MOSS); tellipse(5, 3, (x - 3, 36), 4, 2.8, MOSS)
    # rope coil / bridge rope detail
    tline(6, 3, [(4, 26), (60, 26)], WOOD_D, 3.4); tline(6, 3, [(4, 36), (60, 36)], WOOD_D, 3.4)
    for x in (12, 32, 52): trect(6, 3, (x - 2, 20, x + 2, 42), WOOD)
    # grass tuft
    for i, x in enumerate((12, 22, 32, 42, 52)):
        tline(7, 3, [(x, 64), (x - 4, 40 - (i % 3) * 5)], MOSS_D, 2.6)
        tline(7, 3, [(x, 64), (x + 5, 44 - (i % 2) * 6)], MOSS, 2.4)
    tellipse(7, 3, (20, 60), 4, 2.6, TORII)  # tiny fallen petals/flower accent

TILE_NAMES = [
    ["stone_top", "stone_fill", "stone_left_edge", "stone_right_edge", "stone_bottom_edge", "mossy_stone_top", "mossy_wall", "mossy_wall_top"],
    ["bridge_left", "bridge_mid", "bridge_right", "wood_platform", "wood_planks", "crate", "crate_cracked", "wood_sign"],
    ["spikes_up", "spikes_down", "saw_blade", "saw_mounted", "torii_top_left", "torii_top_right", "torii_bottom_left", "torii_bottom_right"],
    ["lantern_hanging", "lantern_standing", "bamboo_decor", "foliage", "rock", "vines", "rope", "grass"],
]

far_mountains(); mid_bamboo(); near_trees(); build_tileset()

tiles_img = tiles_img.resize((512, 256), Image.LANCZOS)
tiles_img.save(f"{OUT}/tileset.png")
meta = {"image": "tileset.png", "tileWidth": 64, "tileHeight": 64, "columns": 8, "rows": 4,
        "tiles": {name: {"index": r * 8 + c, "col": c, "row": r, "x": c * 64, "y": r * 64}
                  for r, row in enumerate(TILE_NAMES) for c, name in enumerate(row)},
        "notes": {"toriiGate": "assemble tiles torii_top_left, torii_top_right, torii_bottom_left, torii_bottom_right in a 2x2 block (128x128 px)"}}
with open(f"{OUT}/tileset.json", "w") as f:
    json.dump(meta, f, indent=2)
print("tileset.png + tileset.json")

# ---- QA previews ----
sky = Image.new("RGBA", (W, H))
sd = ImageDraw.Draw(sky)
for y in range(H):
    k = y / H
    col = (int(24 + 30 * k), int(22 + 18 * k), int(52 + 44 * k))  # indigo -> purple dusk
    sd.line([(0, y), (W, y)], fill=col + (255,))
sd.ellipse([1560, 90, 1690, 220], fill=(238, 230, 205, 255))      # moon (preview only)
comp = sky.copy()
for f in ("far-mountains.png", "mid-bamboo-forest.png", "near-trees.png"):
    comp.alpha_composite(Image.open(f"{OUT}/{f}"))
comp.convert("RGB").save(f"{OUT}/_preview-composite.png")

chk = Image.new("RGBA", (512, 256), (232, 232, 238, 255))
cd = ImageDraw.Draw(chk)
for y in range(0, 256, 16):
    for x in range(0, 512, 16):
        if (x // 16 + y // 16) % 2: cd.rectangle([x, y, x + 15, y + 15], fill=(196, 198, 210, 255))
chk.alpha_composite(tiles_img)
for gx in range(9): cd.line([(gx * 64, 0), (gx * 64, 256)], fill=(120, 120, 140), width=1)
for gy in range(5): cd.line([(0, gy * 64), (512, gy * 64)], fill=(120, 120, 140), width=1)
chk.convert("RGB").save(f"{OUT}/_preview-tileset.png")
print("previews saved")

#!/usr/bin/env python3
"""
Professional mobile UI icon set for Shadow Ninja (2026 polish)
-------------------------------------------------------------
Each phone button gets its OWN 256x256 transparent PNG: a dark glass
disc with a glowing accent ring and a crisp vector icon, drawn at 4x
and downscaled. Also HUD icons (heart/coin/key/mask) and a menu emblem.

Files: btn-left, btn-right, btn-down, btn-jump, btn-sword,
btn-shuriken, btn-dash, btn-pause, btn-restart, btn-sound-on,
btn-sound-off, btn-fullscreen, btn-play,
hud-heart, hud-coin, hud-key, hud-mask, menu-emblem.

Run: python3 generate_ui.py
"""
import math, pathlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 4
SZ = 256
OUT = str(pathlib.Path(__file__).resolve().parent.parent / "assets" / "ui")

WHITE = (240, 244, 255, 255)
SILVER = (205, 212, 232, 255)

def canvas():
    return Image.new("RGBA", (SZ * S, SZ * S), (0, 0, 0, 0))

def P(p): return (p[0] * S, p[1] * S)

def line(d, pts, color, w=10):
    xy = [P(p) for p in pts]
    d.line(xy, fill=color, width=int(w * S), joint="curve")
    for p in xy:
        r = w * S / 2
        d.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=color)

def poly(d, pts, color): d.polygon([P(p) for p in pts], fill=color)

def ellipse(d, c, rx, ry, color):
    d.ellipse([P((c[0]-rx, c[1]-ry)), P((c[0]+rx, c[1]+ry))], fill=color)

def rrect(d, box, r, color):
    d.rounded_rectangle([P((box[0], box[1])), P((box[2], box[3]))], radius=r * S, fill=color)

def finish(img, name):
    img = img.resize((SZ, SZ), Image.LANCZOS)
    img.save(f"{OUT}/{name}.png")
    print(name + ".png")

# ------------------------------------------------------------- button skin
def button_base(accent):
    """Dark glass disc: vertical gradient, accent ring, top gloss."""
    img = Image.new("RGBA", (SZ * S, SZ * S), (0, 0, 0, 0))
    # vertical gradient clipped to a circle
    grad = Image.new("RGBA", (SZ * S, SZ * S))
    gd = ImageDraw.Draw(grad)
    for y in range(SZ * S):
        k = y / (SZ * S)
        col = (int(38 - 26 * k), int(46 - 32 * k), int(78 - 52 * k), 255)
        gd.line([(0, y), (SZ * S, y)], fill=col)
    mask = Image.new("L", (SZ * S, SZ * S), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([10*S, 10*S, 246*S, 246*S], fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([10*S, 10*S, 246*S, 246*S], outline=(0, 0, 0, 160), width=3*S)          # outer shade
    d.ellipse([16*S, 16*S, 240*S, 240*S], outline=accent, width=7*S)                  # accent ring
    d.ellipse([26*S, 26*S, 230*S, 230*S], outline=(255, 255, 255, 42), width=2*S)     # inner rim
    d.arc([16*S, 16*S, 240*S, 240*S], start=195, end=320, fill=(255, 255, 255, 120), width=5*S)  # top light
    # gloss blob
    gloss = Image.new("RGBA", (SZ * S, SZ * S), (0, 0, 0, 0))
    gd2 = ImageDraw.Draw(gloss)
    gd2.ellipse([52*S, 26*S, 204*S, 108*S], fill=(255, 255, 255, 34))
    img.alpha_composite(gloss.filter(ImageFilter.GaussianBlur(10 * S)))
    return img

def icon_button(name, accent, draw_icon):
    img = button_base(accent)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    draw_icon(sd, (0, 0, 0, 170), dy=5)                      # drop shadow pass
    img.alpha_composite(shadow)
    d = ImageDraw.Draw(img, "RGBA")
    draw_icon(d, WHITE, dy=0)
    finish(img, name)

# ------------------------------------------------------------- icons (256-space)
def i_left(d, col, dy=0):
    line(d, [(158, 74+dy), (96, 128+dy), (158, 182+dy)], col, 24)

def i_right(d, col, dy=0):
    line(d, [(98, 74+dy), (160, 128+dy), (98, 182+dy)], col, 24)

def i_down(d, col, dy=0):
    line(d, [(76, 92+dy), (128, 150+dy), (180, 92+dy)], col, 22)
    line(d, [(76, 128+dy), (128, 186+dy), (180, 128+dy)], (col[0], col[1], col[2], 150), 22)

def i_jump(d, col, dy=0):
    line(d, [(74, 116+dy), (128, 58+dy), (182, 116+dy)], col, 24)
    line(d, [(74, 152+dy), (128, 94+dy), (182, 152+dy)], (col[0], col[1], col[2], 150), 24)
    line(d, [(72, 198+dy), (184, 198+dy)], col, 13)

def i_sword(d, col, dy=0):
    blade = [(92, 178+dy), (196, 66+dy), (204, 58+dy), (200, 84+dy), (108, 190+dy)]  # blade silhouette
    poly(d, blade, SILVER if col == WHITE else col)
    line(d, [(88, 182+dy), (64, 206+dy)], (235, 48, 66, 255) if col == WHITE else col, 15)   # handle
    line(d, [(104, 160+dy), (84, 180+dy)], (200, 160, 60, 255) if col == WHITE else col, 13)  # guard

def i_shuriken(d, col, dy=0):
    cx, cy = 128, 128 + dy
    pts = []
    for i in range(8):
        ang = i / 8 * 2 * math.pi - math.pi / 2
        r = 66 if i % 2 == 0 else 26
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    poly(d, pts, SILVER if col == WHITE else col)
    ellipse(d, (cx, cy), 14, 14, (16, 18, 32, 255) if col == WHITE else col)

def i_dash(d, col, dy=0):
    c = (103, 216, 255, 255) if col == WHITE else col
    line(d, [(52, 92+dy), (150, 92+dy)], c, 17)
    line(d, [(36, 128+dy), (168, 128+dy)], c, 20)
    line(d, [(58, 164+dy), (146, 164+dy)], c, 15)
    line(d, [(168, 92+dy), (196, 128+dy), (168, 164+dy)], c, 18)

def i_pause(d, col, dy=0):
    rrect(d, (94, 76+dy, 116, 180+dy), 9, col)
    rrect(d, (140, 76+dy, 162, 180+dy), 9, col)

def i_restart(d, col, dy=0):
    d.arc([64*S, 64*S, 192*S, 192*S], start=300, end=205, fill=col, width=17*S)
    poly(d, [(70, 66+dy), (104, 44+dy), (100, 84+dy)], col)

def i_sound_on(d, col, dy=0):
    poly(d, [(66, 108+dy), (92, 108+dy), (122, 82+dy), (122, 174+dy), (92, 148+dy), (66, 148+dy)], col)
    d.arc([118*S, (88+dy)*S, 178*S, (168+dy)*S], start=-55, end=55, fill=col, width=11*S)
    d.arc([134*S, (72+dy)*S, 210*S, (184+dy)*S], start=-55, end=55, fill=(col[0], col[1], col[2], 160), width=10*S)

def i_sound_off(d, col, dy=0):
    poly(d, [(66, 108+dy), (92, 108+dy), (122, 82+dy), (122, 174+dy), (92, 148+dy), (66, 148+dy)], col)
    line(d, [(146, 102+dy), (192, 154+dy)], (255, 84, 96, 255) if col == WHITE else col, 14)
    line(d, [(192, 102+dy), (146, 154+dy)], (255, 84, 96, 255) if col == WHITE else col, 14)

def i_fullscreen(d, col, dy=0):
    for (x, y, sx, sy) in [(66, 66, 1, 1), (190, 66, -1, 1), (66, 190, 1, -1), (190, 190, -1, -1)]:
        line(d, [(x, y + 36*sy + dy), (x, y + dy), (x + 36*sx, y + dy)], col, 15)

def i_play(d, col, dy=0):
    poly(d, [(100, 74+dy), (100, 182+dy), (178, 128+dy)], col)

ACC_CYAN = (103, 216, 255, 255)
ACC_RED = (255, 84, 96, 255)
ACC_GOLD = (255, 196, 84, 255)
ACC_STEEL = (168, 186, 230, 255)
ACC_GREEN = (94, 234, 176, 255)
ACC_PURPLE = (178, 156, 255, 255)

icon_button("btn-left", ACC_STEEL, i_left)
icon_button("btn-right", ACC_STEEL, i_right)
icon_button("btn-down", ACC_PURPLE, i_down)
icon_button("btn-jump", ACC_GREEN, i_jump)
icon_button("btn-sword", ACC_RED, i_sword)
icon_button("btn-shuriken", ACC_CYAN, i_shuriken)
icon_button("btn-dash", ACC_CYAN, i_dash)
icon_button("btn-pause", ACC_STEEL, i_pause)
icon_button("btn-restart", ACC_GOLD, i_restart)
icon_button("btn-sound-on", ACC_GOLD, i_sound_on)
icon_button("btn-sound-off", ACC_RED, i_sound_off)
icon_button("btn-fullscreen", ACC_STEEL, i_fullscreen)
icon_button("btn-play", ACC_RED, i_play)

# ------------------------------------------------------------- HUD icons (no disc)
def bare(name, draw):
    img = canvas(); d = ImageDraw.Draw(img, "RGBA")
    draw(d)
    finish(img, name)

def d_heart(d):
    d.ellipse([P((52, 58)), P((122, 128))], fill=(255, 84, 96, 255))
    d.ellipse([P((134, 58)), P((204, 128))], fill=(235, 48, 66, 255))
    poly(d, [(56, 108), (200, 108), (128, 204)], (226, 38, 58, 255))
    ellipse(d, (88, 84), 17, 12, (255, 190, 198, 200))

def d_coin(d):
    ellipse(d, (128, 128), 74, 74, (198, 140, 30, 255))
    ellipse(d, (128, 128), 63, 63, (255, 205, 84, 255))
    ellipse(d, (128, 128), 46, 46, (255, 222, 130, 255))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 74 * S)
    except Exception:
        font = ImageFont.load_default()
    d.text((128*S, 126*S), "¥", font=font, anchor="mm", fill=(176, 118, 22, 255))

def d_key(d):
    d.ellipse([P((52, 88)), P((122, 158))], outline=(255, 205, 84, 255), width=13*S)
    line(d, [(112, 128), (198, 128)], (255, 205, 84, 255), 13)
    line(d, [(172, 128), (172, 156)], (255, 205, 84, 255), 13)
    line(d, [(198, 128), (198, 164)], (255, 205, 84, 255), 13)

def d_mask(d):
    ellipse(d, (128, 128), 76, 82, (14, 14, 24, 255))
    poly(d, [(72, 92), (128, 34), (184, 94)], (14, 14, 24, 255))
    line(d, [(104, 122), (158, 118)], (255, 64, 74, 255), 11)

bare("hud-heart", d_heart)
bare("hud-coin", d_coin)
bare("hud-key", d_key)
bare("hud-mask", d_mask)

# ------------------------------------------------------------- menu emblem
def d_emblem(d):
    ellipse(d, (128, 138), 84, 90, (12, 12, 22, 255))
    poly(d, [(58, 104), (128, 22), (198, 106)], (12, 12, 22, 255))                      # hood
    poly(d, [(66, 104), (128, 40), (190, 106), (128, 92)], (30, 24, 52, 255))            # hood shade
    line(d, [(98, 132), (166, 126)], (255, 64, 74, 255), 13)                            # eye slit
    ellipse(d, (112, 130), 6, 4, (255, 190, 195, 255))
    # scarf streaming left
    line(d, [(76, 168), (40, 176), (14, 168)], (235, 48, 66, 255), 15)
    line(d, [(76, 178), (44, 192), (22, 190)], (176, 26, 44, 255), 11)
    # crossed katana behind
    line(d, [(188, 196), (222, 236)], (219, 224, 240, 255), 9)
    line(d, [(70, 200), (40, 238)], (219, 224, 240, 255), 9)

bare("menu-emblem", d_emblem)

# ------------------------------------------------------------- QA contact sheet
names = ["btn-left", "btn-right", "btn-down", "btn-jump", "btn-sword", "btn-shuriken",
         "btn-dash", "btn-pause", "btn-restart", "btn-sound-on", "btn-sound-off", "btn-fullscreen",
         "hud-heart", "hud-coin", "hud-key", "hud-mask", "menu-emblem"]
cols = 6
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 190, rows * 190), (16, 18, 30))
for i, n in enumerate(names):
    im = Image.open(f"{OUT}/{n}.png").resize((150, 150), Image.LANCZOS)
    bg = Image.new("RGB", (150, 150), (28, 31, 48))
    sheet.paste(bg, ((i % cols) * 190 + 20, (i // cols) * 190 + 8))
    sheet.paste(im, ((i % cols) * 190 + 20, (i // cols) * 190 + 8), im)
sheet.save(f"{OUT}/_preview-contact-sheet.png")
print("contact sheet saved,", len(names), "assets")

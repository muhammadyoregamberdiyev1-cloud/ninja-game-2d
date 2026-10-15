#!/usr/bin/env python3
"""
Sprite sheets V2 — improved models + expanded animation sets.
Same flat-vector silhouette family as v1, upgraded:
  * chunkier proportions (bigger heads/torsos, thicker limbs)
  * purple rim-light pass under every limb, layered scarves/cloaks
  * detailed gear: wrapped katana grips, armour bands, bow, club studs
Frame size stays 128x128, transparent background, 4x supersampling.

  shadow-ninja-v2.png    9x5 = 45f  idle6 run8 jump2 doubleJump3 fall2
                                    wallSlide2 attack5 throw3 dash3
                                    hurt2 land2 crouch2 death5
  samurai-guard-v2.png   6x5 = 30f  idle6 walk8 attack6 hurt2 block2 death6
  shadow-archer-v2.png   6x5 = 30f  idle6 walk6 shoot8 hurt2 dodge2 death6
  oni-boss-v2.png        8x4 = 32f  idle6 walk8 attack7 hurt2 roar3 death6
Run: python3 generate_v2.py
"""
import json, math
from PIL import Image, ImageDraw

S = 4
CELL = 128
OUT = str(pathlib.Path(__file__).resolve().parent.parent / "assets" / "sprites")

INK   = (12, 12, 22, 255)
INK2  = (26, 26, 46, 255)
RIM   = (52, 40, 96, 255)       # purple rim light
RED   = (235, 48, 66, 255)
RED_D = (176, 26, 44, 255)
ORANGE = (255, 140, 46, 255)
ORGLOW = (255, 120, 30, 110)
EYE   = (255, 64, 74, 255)
EYE_O = (255, 166, 48, 255)
BONE  = (218, 210, 192, 255)
STEEL = (219, 224, 240, 255)
STEEL_D = (142, 150, 172, 255)
WOOD  = (26, 19, 28, 255)

# ----------------------------------------------------------------- helpers
def P(ox, oy, p): return ((ox + p[0]) * S, (oy + p[1]) * S)

def limb(d, ox, oy, pts, color=INK, w=8, rim=True):
    if rim:  # rim-light pass: wider, offset down-right, drawn first
        xy = [P(ox, oy, (p[0] + 1.6, p[1] + 1.6)) for p in pts]
        d.line(xy, fill=RIM, width=int((w + 2.6) * S), joint="curve")
        for p in xy:
            r = (w + 2.6) * S / 2
            d.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=RIM)
    xy = [P(ox, oy, p) for p in pts]
    d.line(xy, fill=color, width=int(w * S), joint="curve")
    for p in xy:
        r = w * S / 2
        d.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], fill=color)

def poly(d, ox, oy, pts, color): d.polygon([P(ox, oy, p) for p in pts], fill=color)

def circle(d, ox, oy, c, r, color):
    x, y = P(ox, oy, c)
    d.ellipse([x-r*S, y-r*S, x+r*S, y+r*S], fill=color)

def alpha(c, a): return (c[0], c[1], c[2], int(c[3] * a / 255)) if len(c) > 3 else (c[0], c[1], c[2], a)

def eye_slit(d, ox, oy, head, a, dx=5, col=EYE):
    ex, ey = head[0] + dx, head[1] - 1
    limb(d, ox, oy, [(ex-2, ey+1), (ex+7, ey-1)], alpha((255, 60, 60) if col == EYE else ORGLOW, a), 5.2, rim=False)
    limb(d, ox, oy, [(ex-1, ey+.5), (ex+6, ey-.8)], alpha(col, a), 2.2, rim=False)

def eyes_x(d, ox, oy, head, a, dx=5, col=EYE):
    ex, ey = head[0] + dx, head[1] - 1
    limb(d, ox, oy, [(ex-3, ey-3), (ex+4, ey+4)], alpha(col, a), 2, rim=False)
    limb(d, ox, oy, [(ex+4, ey-3), (ex-3, ey+4)], alpha(col, a), 2, rim=False)

def slash_arc(d, ox, oy, cx, cy, r, a0, a1, a=255, col=(255, 110, 110)):
    box = [((ox+cx-r)*S, (oy+cy-r)*S), ((ox+cx+r)*S, (oy+cy+r)*S)]
    d.arc(box, start=a0, end=a1, fill=alpha(col + (255,), int(80 * a/255)) if len(col) == 3 else col, width=int(8*S))
    d.arc(box, start=a0, end=a1, fill=alpha((240, 248, 255), int(220 * a/255)), width=int(4*S))

def shift(p, dx=0, dy=0):
    q = dict(p)
    for k, v in p.items():
        if isinstance(v, tuple) and len(v) == 2 and all(isinstance(n, (int, float)) for n in v):
            q[k] = (v[0] + dx, v[1] + dy)
    return q

def save_sheet(name, cols, poses, draw_fn, animations):
    rows = math.ceil(len(poses) / cols)
    sheet = Image.new("RGBA", (cols * CELL * S, rows * CELL * S), (0, 0, 0, 0))
    for i, pose in enumerate(poses):
        draw_fn(sheet, i % cols * CELL, i // cols * CELL, pose)
    sheet = sheet.resize((cols * CELL, rows * CELL), Image.LANCZOS)
    sheet.save(f"{OUT}/{name}.png")
    meta = {"image": f"{name}.png", "frameWidth": 128, "frameHeight": 128,
            "columns": cols, "rows": rows, "frames": len(poses),
            "background": "transparent", "version": 2, "animations": animations}
    with open(f"{OUT}/{name}.json", "w") as f: json.dump(meta, f, indent=2)
    Wd, Hd = sheet.size
    chk = Image.new("RGBA", (Wd, Hd), (235, 235, 240, 255))
    cd = ImageDraw.Draw(chk)
    for y in range(0, Hd, 16):
        for x in range(0, Wd, 16):
            if (x//16 + y//16) % 2: cd.rectangle([x, y, x+15, y+15], fill=(198, 200, 212, 255))
    chk.alpha_composite(sheet)
    for gx in range(cols + 1): cd.line([(gx*CELL, 0), (gx*CELL, Hd)], fill=(120, 120, 140), width=1)
    for gy in range(rows + 1): cd.line([(0, gy*CELL), (Wd, gy*CELL)], fill=(120, 120, 140), width=1)
    chk.convert("RGB").save(f"{OUT}/_preview-{name}.png")
    print(f"{name}.png  {Wd}x{Hd}  {len(poses)} frames")

def sword_in_hand(d, ox, oy, hand, tip, a):
    grip = (hand[0] + (tip[0]-hand[0])*.16, hand[1] + (tip[1]-hand[1])*.16)
    limb(d, ox, oy, [hand, grip], (10, 10, 16, a), 3.8, rim=False)
    for i in range(3):  # wrapped grip bands
        gx = hand[0] + (grip[0]-hand[0]) * (0.3 + i*0.22); gy = hand[1] + (grip[1]-hand[1]) * (0.3 + i*0.22)
        circle(d, ox, oy, (gx, gy), 2.1, alpha(RED_D, a))
    limb(d, ox, oy, [grip, tip], alpha(STEEL, a), 3.2, rim=False)
    circle(d, ox, oy, grip, 3, alpha(STEEL_D, a))

# =================================================================
# NINJA V2
# =================================================================
def draw_ninja(sheet, ox, oy, pose):
    layer = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = pose.get("alpha", 255)
    ink, ink2 = alpha(INK, a), alpha(INK2, a)
    head, sho, hip = pose["head"], pose["shoulder"], pose["hip"]
    # layered scarf (behind)
    neck = (sho[0] - 4, sho[1] + 2); wave = pose.get("scarf", 0); ln = pose.get("scarf_len", 28)
    pts = [neck, (neck[0]-ln*.38, neck[1]+3+wave*.5), (neck[0]-ln*.72, neck[1]+1+wave), (neck[0]-ln, neck[1]+5+wave*1.5)]
    for i in range(3):
        limb(d, ox, oy, [pts[i], pts[i+1]], alpha(RED if i % 2 == 0 else RED_D, a), 7 - i*1.5, rim=False)
    limb(d, ox, oy, [sho, pose["b_elbow"], pose["b_hand"]], ink2, 9)
    limb(d, ox, oy, [hip, pose["b_knee"], pose["b_foot"]], ink2, 10)
    # torso with chest strap + belt
    vx, vy = hip[0]-sho[0], hip[1]-sho[1]; L = max(1, math.hypot(vx, vy)); nx, ny = -vy/L, vx/L
    poly(d, ox, oy, [(sho[0]+nx*13, sho[1]+ny*13), (sho[0]-nx*13, sho[1]-ny*13),
                     (hip[0]-nx*9.5, hip[1]-ny*9.5), (hip[0]+nx*9.5, hip[1]+ny*9.5)], ink)
    limb(d, ox, oy, [(sho[0]-9, sho[1]+4), (hip[0]+7, hip[1]-6)], alpha((46, 36, 84), a), 4.5, rim=False)  # strap
    limb(d, ox, oy, [(hip[0]-8.5, hip[1]-2), (hip[0]+8.5, hip[1]-3)], alpha(RED, a), 4.2, rim=False)
    limb(d, ox, oy, [hip, pose["f_knee"], pose["f_foot"]], ink, 10.5)
    circle(d, ox, oy, pose["f_knee"], 5, ink); circle(d, ox, oy, pose["b_knee"], 5, ink2)  # knee guards
    # head: bigger hood, face band, crest
    circle(d, ox, oy, head, 13.5, ink)
    poly(d, ox, oy, [(head[0]-11, head[1]-6), (head[0]+1, head[1]-20), (head[0]+12, head[1]-5)], ink)
    poly(d, ox, oy, [(head[0]-12, head[1]+5), (head[0]-2, head[1]+14), (head[0]+11, head[1]+6)], ink)
    poly(d, ox, oy, [(head[0]-11, head[1]-3), (head[0]+11, head[1]-4), (head[0]+11, head[1]+5), (head[0]-11, head[1]+4)], alpha((24, 20, 44), a))  # mask band
    if pose.get("back_sword", True):
        limb(d, ox, oy, [(sho[0]-4, sho[1]+7), (sho[0]-14, sho[1]-11)], (10, 10, 18, a), 5, rim=False)
        limb(d, ox, oy, [(sho[0]-14, sho[1]-11), (sho[0]-20, sho[1]-20)], alpha(STEEL, a), 2.6, rim=False)
    limb(d, ox, oy, [sho, pose["f_elbow"], pose["f_hand"]], ink, 9)
    if pose.get("sword"): sword_in_hand(d, ox, oy, pose["f_hand"], pose["sword"], a)
    if pose.get("shuriken"):
        hx, hy = pose["shuriken"]
        for i in range(4):
            ang = i * math.pi / 2 + .4
            limb(d, ox, oy, [(hx, hy), (hx + math.cos(ang)*7, hy + math.sin(ang)*7)], alpha(STEEL, a), 2.4, rim=False)
    if pose.get("eyes_x"): eyes_x(d, ox, oy, head, a)
    elif a > 40: eye_slit(d, ox, oy, head, a)
    if pose.get("slash"): slash_arc(d, ox, oy, *pose["slash"], a)
    if pose.get("streaks"):
        for (sx, sy, ln2) in pose["streaks"]:
            limb(d, ox, oy, [(sx, sy), (sx-ln2, sy)], (200, 210, 235, 90), 2.6, rim=False)
    if pose.get("impact"):
        ix, iy = pose["impact"]
        for ang in (0, 60, 120, 180, 240, 300):
            r = math.radians(ang)
            limb(d, ox, oy, [(ix+math.cos(r)*3, iy+math.sin(r)*3), (ix+math.cos(r)*10, iy+math.sin(r)*10)], alpha(EYE, a), 2.2, rim=False)
    if pose.get("wisps"):
        for (wx, wy, wr, wa) in pose["wisps"]:
            circle(d, ox, oy, (wx, wy), wr, (30, 30, 50, int(wa*a/255)))
            circle(d, ox, oy, (wx+2, wy-3), wr*.45, alpha(RED, int(wa*.85*a/255)))
    sheet.alpha_composite(layer)

def nb(**kw):
    p = dict(head=(70, 35), shoulder=(66, 49), hip=(61, 75),
             f_knee=(74, 90), f_foot=(79, 108), b_knee=(54, 91), b_foot=(48, 108),
             f_elbow=(79, 63), f_hand=(85, 78), b_elbow=(53, 63), b_hand=(47, 77), scarf=0)
    p.update(kw); return p

ninja = []
for i, dy in enumerate([0, 1, 2, 3, 2, 1]):                      # idle 0-5
    ninja.append(shift(nb(scarf=i * 1.2), 0, dy))
_FF = [(90, 100), (86, 108), (68, 110), (48, 102), (38, 94), (48, 102), (66, 110), (84, 106)]
_BF = [_FF[(i + 4) % 8] for i in range(8)]
for i in range(8):                                              # run 6-13
    fk = (( _FF[i][0] + 61) / 2 + 7, (_FF[i][1] + 75) / 2 - 15)
    bk = ((_BF[i][0] + 61) / 2 - 6, (_BF[i][1] + 75) / 2 - 14)
    ninja.append(shift(nb(head=(74, 34), shoulder=(70, 48), hip=(63, 73),
                          f_knee=fk, f_foot=_FF[i], b_knee=bk, b_foot=_BF[i],
                          f_elbow=(58, 60), f_hand=(50, 72) if i % 2 == 0 else (86, 62),
                          b_elbow=(80, 58), b_hand=(88, 68) if i % 2 == 0 else (52, 68),
                          scarf=2 + (i % 4), scarf_len=32), 0, [0, 2, 3, 1][i % 4]))
ninja.append(shift(nb(head=(72, 31), shoulder=(68, 45), hip=(62, 67),                 # jump 14-15
                      f_knee=(80, 77), f_foot=(86, 91), b_knee=(52, 79), b_foot=(44, 89),
                      f_elbow=(82, 39), f_hand=(90, 29), b_elbow=(50, 43), b_hand=(40, 33), scarf=-3), 0, -4))
ninja.append(shift(nb(head=(71, 32), shoulder=(67, 46), hip=(62, 69),
                      f_knee=(82, 73), f_foot=(80, 59), b_knee=(54, 75), b_foot=(58, 61),
                      f_elbow=(84, 51), f_hand=(94, 43), b_elbow=(48, 51), b_hand=(38, 45), scarf=-1), 0, -2))
for i, tilt in enumerate([-6, 0, 7]):                            # double jump flip 16-18
    ninja.append(shift(nb(head=(72 + tilt, 34 - abs(tilt)), shoulder=(68, 47), hip=(62, 68),
                          f_knee=(84, 70), f_foot=(78, 56), b_knee=(56, 72), b_foot=(66, 58),
                          f_elbow=(86, 40 - i * 6), f_hand=(96, 32 - i * 8),
                          b_elbow=(46, 44 + i * 5), b_hand=(34, 38 + i * 7), scarf=-5 + i * 3, scarf_len=32), 0, -3))
for i in range(2):                                              # fall 19-20
    ninja.append(nb(head=(69, 37), shoulder=(65, 51), hip=(61, 77),
                    f_knee=(72 + i * 3, 93), f_foot=(78 + i * 2, 110), b_knee=(54, 91 - i * 3), b_foot=(46, 106 - i * 2),
                    f_elbow=(82, 43), f_hand=(92, 33), b_elbow=(48, 45), b_hand=(38, 37), scarf=-6 - i * 2, scarf_len=31))
for i in range(2):                                              # wall slide 21-22
    ninja.append(nb(head=(54, 34), shoulder=(56, 49), hip=(57, 76),
                    f_knee=(76, 67), f_foot=(84, 83), b_knee=(70, 91), b_foot=(84, 103),
                    f_elbow=(70, 35 - i * 3), f_hand=(82, 21 - i * 4), b_elbow=(44, 61), b_hand=(38, 75),
                    scarf=5 + i * 2, eye_dx=3))
for i, (hand, tip, arc) in enumerate([                          # sword attack 23-27
        ((50, 26), (24, 10), None), ((70, 34), (52, 14), None),
        ((94, 54), (114, 26), (70, 54, 44, -75, 55)), ((98, 68), (122, 82), (72, 57, 46, -12, 112)),
        ((84, 78), (104, 92), None)]):
    ninja.append(nb(head=(73, 34), shoulder=(69, 48), hip=(62, 74),
                    f_knee=(77, 89), f_foot=(84, 108), b_knee=(52, 89), b_foot=(41, 108),
                    f_elbow=((hand[0] + 69) / 2, (hand[1] + 48) / 2), f_hand=hand,
                    b_elbow=(55, 63), b_hand=(47, 75), back_sword=False, sword=tip,
                    scarf=2 + i, slash=arc))
for i, hand in enumerate([(44, 40), (76, 44), (92, 56)]):        # throw 28-30
    ninja.append(nb(head=(71, 34), shoulder=(67, 48), hip=(61, 74),
                    f_knee=(75, 89), f_foot=(81, 108), b_knee=(53, 89), b_foot=(45, 108),
                    f_elbow=((hand[0] + 67) / 2 + 4, (hand[1] + 48) / 2), f_hand=hand,
                    b_elbow=(52, 62), b_hand=(45, 74), scarf=3,
                    shuriken=(112, 46) if i == 1 else None))
for i, dy in enumerate([0, 3, 1]):                              # dash 31-33
    ninja.append(shift(nb(head=(92, 51), shoulder=(78, 56), hip=(50, 62),
                          f_knee=(34, 57), f_foot=(14, 49), b_knee=(36, 71), b_foot=(16, 79),
                          f_elbow=(96, 61), f_hand=(104, 67), b_elbow=(66, 71), b_hand=(52, 81),
                          back_sword=False, sword=(123, 59), scarf=-2, scarf_len=38, eye_dx=6,
                          streaks=[(44, 42, 32), (38, 84, 38), (58, 32, 22)]), 0, dy))
for i in range(2):                                              # hurt 34-35
    ninja.append(shift(nb(head=(58, 33), shoulder=(60, 48), hip=(62, 74),
                          f_knee=(76, 89), f_foot=(84, 106), b_knee=(52, 87), b_foot=(42, 100),
                          f_elbow=(48, 39), f_hand=(36, 29), b_elbow=(74, 41), b_hand=(86, 31),
                          scarf=7, scarf_len=31, eye_dx=3, impact=(48, 42) if i == 0 else None), -i * 3, -i * 2))
for i, sq in enumerate([10, 5]):                                # land 36-37 (squash & recover)
    ninja.append(nb(head=(68, 35 + sq), shoulder=(65, 49 + sq), hip=(60, 75 + sq * .6),
                    f_knee=(80, 88), f_foot=(88, 108), b_knee=(48, 88), b_foot=(38, 108),
                    f_elbow=(80, 62 + sq), f_hand=(88, 74), b_elbow=(50, 62 + sq), b_hand=(42, 74), scarf=1))
for i, dy in enumerate([0, 2]):                                 # crouch 38-39
    ninja.append(nb(head=(66, 47), shoulder=(63, 60), hip=(59, 82),
                    f_knee=(78, 92), f_foot=(86, 108), b_knee=(50, 94), b_foot=(42, 108),
                    f_elbow=(76, 72), f_hand=(84, 84), b_elbow=(50, 72), b_hand=(43, 83), scarf=1 + dy))
ninja.append(shift(nb(head=(56, 39), f_elbow=(46, 41), f_hand=(34, 31), b_elbow=(76, 43), b_hand=(88, 33),
                      scarf=8, eye_dx=3), 0, -12))               # death 40-44
ninja.append(shift(nb(head=(50, 55), shoulder=(58, 65), hip=(68, 83),
                      f_knee=(86, 77), f_foot=(98, 87), b_knee=(58, 95), b_foot=(46, 103),
                      f_elbow=(40, 53), f_hand=(28, 45), b_elbow=(72, 51), b_hand=(82, 41), scarf=9, eye_dx=2), 0, -4))
ninja.append(shift(nb(head=(42, 76), shoulder=(53, 84), hip=(68, 94),
                      f_knee=(88, 88), f_foot=(100, 96), b_knee=(58, 102), b_foot=(46, 108),
                      f_elbow=(38, 74), f_hand=(28, 66), b_elbow=(70, 72), b_hand=(80, 62), scarf=8, eye_dx=2), 0, 0))
_ly = dict(head=(34, 96), shoulder=(47, 99), hip=(72, 101),
           f_knee=(90, 94), f_foot=(108, 98), b_knee=(88, 106), b_foot=(104, 110),
           f_elbow=(52, 88), f_hand=(62, 80), b_elbow=(40, 108), b_hand=(28, 112),
           scarf=-2, scarf_len=18, eye_dx=3, back_sword=False, eyes_x=True)
ninja.append(nb(**_ly))
_f = dict(_ly); _f.update(alpha=95, wisps=[(52, 74, 7, 130), (70, 60, 5, 100), (86, 46, 4, 80)])
ninja.append(nb(**_f))
assert len(ninja) == 45, len(ninja)

# =================================================================
# SAMURAI V2
# =================================================================
def draw_samurai(sheet, ox, oy, pose):
    layer = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = pose.get("alpha", 255)
    ink, ink2 = alpha(INK, a), alpha(INK2, a)
    org, bone = alpha(ORANGE, a), alpha(BONE, a)
    head, sho, hip = pose["head"], pose["shoulder"], pose["hip"]
    limb(d, ox, oy, [sho, pose["b_elbow"], pose["b_hand"]], ink2, 9.5)
    limb(d, ox, oy, [hip, pose["b_knee"], pose["b_foot"]], ink2, 11)
    # boxy cuirass with horizontal armour bands + orange trim
    poly(d, ox, oy, [(sho[0]-15, sho[1]-5), (sho[0]+15, sho[1]-5), (hip[0]+13, hip[1]+3), (hip[0]-13, hip[1]+3)], ink)
    for k in range(3):
        yy = sho[1] + 4 + k * 8
        limb(d, ox, oy, [(sho[0]-14 + k, yy), (sho[0]+14 - k, yy)], alpha((58, 50, 96), a), 2.2, rim=False)
    circle(d, ox, oy, (sho[0]-13, sho[1]+1), 8, ink2)   # sode shoulder guards
    circle(d, ox, oy, (sho[0]+13, sho[1]+1), 8, ink)
    poly(d, ox, oy, [(hip[0]-15, hip[1]+1), (hip[0]+15, hip[1]+1), (hip[0]+18, hip[1]+16), (hip[0]-18, hip[1]+16)], ink2)  # tassets
    for gx in (-9, 0, 9):
        limb(d, ox, oy, [(hip[0]+gx, hip[1]+3), (hip[0]+gx*1.3, hip[1]+15)], ink, 2, rim=False)
    limb(d, ox, oy, [(hip[0]-14, hip[1]+1), (hip[0]+14, hip[1]+1)], org, 4.2, rim=False)
    limb(d, ox, oy, [hip, pose["f_knee"], pose["f_foot"]], ink, 11)
    limb(d, ox, oy, [sho, pose["f_elbow"], pose["f_hand"]], ink, 9.5)
    if pose.get("sheath", True):
        limb(d, ox, oy, [(hip[0]-11, hip[1]+2), (hip[0]-26, hip[1]+13)], ink2, 5, rim=False)
    if pose.get("sword"): sword_in_hand(d, ox, oy, pose["f_hand"], pose["sword"], a)
    if pose.get("block_guard"):  # blade held across the body
        limb(d, ox, oy, [(62, 52), (92, 62)], alpha(STEEL, a), 3.4, rim=False)
    circle(d, ox, oy, head, 14, ink)                                     # kabuto
    poly(d, ox, oy, [(head[0]-17, head[1]+3), (head[0]+17, head[1]+3), (head[0]+12, head[1]+10), (head[0]-12, head[1]+10)], ink2)
    limb(d, ox, oy, [(head[0]-16, head[1]-2), (head[0]+16, head[1]-2)], ink, 4.2, rim=False)
    poly(d, ox, oy, [(head[0]-12, head[1]-8), (head[0]-22, head[1]-19), (head[0]-7, head[1]-14)], bone)
    poly(d, ox, oy, [(head[0]+12, head[1]-8), (head[0]+22, head[1]-19), (head[0]+7, head[1]-14)], bone)
    circle(d, ox, oy, (head[0]+1, head[1]-14), 3.8, org)
    if pose.get("eyes_x"): eyes_x(d, ox, oy, head, a, col=EYE_O)
    elif a > 40: eye_slit(d, ox, oy, head, a, col=EYE_O)
    if pose.get("slash"): slash_arc(d, ox, oy, *pose["slash"], a, col=(255, 170, 80))
    if pose.get("impact"):
        ix, iy = pose["impact"]
        for ang in (0, 60, 120, 180, 240, 300):
            r = math.radians(ang)
            limb(d, ox, oy, [(ix+math.cos(r)*3, iy+math.sin(r)*3), (ix+math.cos(r)*10, iy+math.sin(r)*10)], alpha(EYE_O, a), 2.2, rim=False)
    if pose.get("wisps"):
        for (wx, wy, wr, wa) in pose["wisps"]:
            circle(d, ox, oy, (wx, wy), wr, (30, 30, 50, int(wa*a/255)))
            circle(d, ox, oy, (wx+2, wy-3), wr*.45, alpha(ORANGE, int(wa*.85*a/255)))
    sheet.alpha_composite(layer)

def sb(**kw):
    p = dict(head=(66, 32), shoulder=(63, 47), hip=(60, 72),
             f_knee=(73, 88), f_foot=(78, 108), b_knee=(54, 89), b_foot=(48, 108),
             f_elbow=(77, 61), f_hand=(83, 75), b_elbow=(51, 61), b_hand=(45, 74))
    p.update(kw); return p

samurai = []
for dy in [0, 1, 2, 3, 2, 1]: samurai.append(shift(sb(), 0, dy))          # idle 0-5
for i in range(8):                                                        # walk 6-13
    samurai.append(shift(sb(head=(69, 31), shoulder=(66, 46), hip=(61, 71),
                            f_knee=((_FF[i][0]+61)/2+6, (_FF[i][1]+72)/2-13), f_foot=(_FF[i][0]-4, _FF[i][1]),
                            b_knee=((_BF[i][0]+61)/2-5, (_BF[i][1]+72)/2-12), b_foot=(_BF[i][0]-4, _BF[i][1]),
                            f_elbow=(80, 62), f_hand=(88, 78), b_elbow=(52, 60), b_hand=(44, 72),
                            sheath=False, sword=(97, 94)), 0, [0, 2, 3, 1][i % 4]))
for i, (hand, tip, arc) in enumerate([                                    # attack 14-19
        ((46, 24), (22, 10), None), ((58, 28), (36, 8), None),
        ((84, 42), (104, 20), (66, 50, 42, -80, 40)), ((96, 56), (116, 30), (70, 54, 44, -60, 70)),
        ((99, 70), (121, 84), (72, 58, 45, 0, 115)), ((86, 78), (104, 92), None)]):
    samurai.append(sb(head=(69, 33), shoulder=(66, 48), f_elbow=((hand[0]+66)/2, (hand[1]+48)/2), f_hand=hand,
                      b_elbow=(54, 62), b_hand=(46, 74), sheath=False, sword=tip, slash=arc))
for i in range(2):                                                        # hurt 20-21
    samurai.append(shift(sb(head=(57, 34), f_elbow=(45, 40), f_hand=(33, 30), b_elbow=(75, 42), b_hand=(87, 32),
                            eyes_x=False, impact=(50, 44) if i == 0 else None), -i*3, -i*3))
for i in range(2):                                                        # block 22-23
    samurai.append(sb(head=(64, 33), f_elbow=(74, 54), f_hand=(66, 58), b_elbow=(50, 62), b_hand=(44, 74),
                      sheath=False, block_guard=True))
samurai.append(shift(sb(head=(56, 35), f_elbow=(46, 40), f_hand=(34, 30), b_elbow=(74, 42), b_hand=(86, 32), eyes_x=True), 0, -10))  # death 24-29
samurai.append(shift(sb(head=(54, 44), shoulder=(59, 56), hip=(62, 76),
                        f_knee=(78, 84), f_foot=(88, 100), b_knee=(52, 90), b_foot=(42, 102),
                        f_elbow=(42, 46), f_hand=(30, 38), b_elbow=(72, 44), b_hand=(82, 34), eyes_x=True), 0, -4))
samurai.append(shift(sb(head=(52, 58), shoulder=(58, 68), hip=(64, 84),
                        f_knee=(84, 82), f_foot=(94, 92), b_knee=(54, 94), b_foot=(44, 104),
                        f_elbow=(40, 56), f_hand=(28, 48), b_elbow=(72, 54), b_hand=(82, 44), eyes_x=True), 0, 2))
_sly = dict(head=(34, 96), shoulder=(47, 99), hip=(70, 101),
            f_knee=(88, 94), f_foot=(106, 98), b_knee=(86, 106), b_foot=(102, 110),
            f_elbow=(52, 88), f_hand=(62, 80), b_elbow=(40, 108), b_hand=(28, 112), sheath=False, eyes_x=True)
samurai.append(sb(**_sly))
samurai.append(sb(**dict(_sly, alpha=170)))
samurai.append(sb(**dict(_sly, alpha=90, wisps=[(52, 74, 7, 130), (70, 60, 5, 100), (86, 46, 4, 80)])))
assert len(samurai) == 30, len(samurai)

# =================================================================
# ARCHER V2
# =================================================================
def draw_archer(sheet, ox, oy, pose):
    layer = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = pose.get("alpha", 255)
    ink, ink2 = alpha(INK, a), alpha(INK2, a)
    org, bone = alpha(ORANGE, a), alpha(BONE, a)
    head, sho, hip = pose["head"], pose["shoulder"], pose["hip"]
    if pose.get("cloak", True):  # jagged cloak
        poly(d, ox, oy, [(sho[0]-7, sho[1]), (hip[0]-9, hip[1]), (hip[0]-22, hip[1]+36),
                         (hip[0]-14, hip[1]+28), (hip[0]-8, hip[1]+38), (sho[0]-17, sho[1]+10)], ink2)
    limb(d, ox, oy, [(sho[0]-6, sho[1]+4), (sho[0]-17, sho[1]+32)], ink2, 7)          # quiver
    limb(d, ox, oy, [(sho[0]-8, sho[1]-3), (sho[0]-13, sho[1]-14)], alpha(STEEL_D, a), 2.2, rim=False)
    limb(d, ox, oy, [(sho[0]-4, sho[1]-4), (sho[0]-7, sho[1]-15)], alpha(STEEL_D, a), 2.2, rim=False)
    limb(d, ox, oy, [hip, pose["b_knee"], pose["b_foot"]], ink2, 8.5)
    vx, vy = hip[0]-sho[0], hip[1]-sho[1]; L = max(1, math.hypot(vx, vy)); nx, ny = -vy/L, vx/L
    poly(d, ox, oy, [(sho[0]+nx*10, sho[1]+ny*10), (sho[0]-nx*10, sho[1]-ny*10),
                     (hip[0]-nx*7, hip[1]-ny*7), (hip[0]+nx*7, hip[1]+ny*7)], ink)
    limb(d, ox, oy, [(hip[0]-7, hip[1]-2), (hip[0]+7, hip[1]-2)], org, 3.6, rim=False)
    limb(d, ox, oy, [hip, pose["f_knee"], pose["f_foot"]], ink, 9)
    circle(d, ox, oy, head, 12, ink)
    poly(d, ox, oy, [(head[0]-9, head[1]-6), (head[0]+1, head[1]-19), (head[0]+10, head[1]-5)], ink)
    limb(d, ox, oy, [sho, pose["b_elbow"], pose["b_hand"]], ink2, 8)
    limb(d, ox, oy, [sho, pose["f_elbow"], pose["f_hand"]], ink, 8.5)
    state = pose.get("bow", "rest")
    if state != "none":
        bh = pose["f_hand"]; bc = (bh[0] + 16, bh[1] - 4)
        top, bot = (bc[0]-3, bc[1]-32), (bc[0]-3, bc[1]+32)
        box = [((ox+bc[0]-12)*S, (oy+bc[1]-32)*S), ((ox+bc[0]+12)*S, (oy+bc[1]+32)*S)]
        d.arc(box, start=-95, end=95, fill=alpha(WOOD, a), width=int(4*S))
        d.arc(box, start=-95, end=95, fill=alpha((90, 70, 60), a), width=int(1.6*S))
        circle(d, ox, oy, bc, 2.8, org)
        if state in ("draw", "aim"):
            limb(d, ox, oy, [top, pose["b_hand"]], bone, 1.6, rim=False)
            limb(d, ox, oy, [pose["b_hand"], bot], bone, 1.6, rim=False)
            limb(d, ox, oy, [pose["b_hand"], (bc[0]+14, bc[1])], alpha(STEEL, a), 2.2, rim=False)
            poly(d, ox, oy, [(bc[0]+14, bc[1]-3.4), (bc[0]+21, bc[1]), (bc[0]+14, bc[1]+3.4)], alpha(STEEL, a))
        else:
            limb(d, ox, oy, [top, bot], bone, 1.6, rim=False)
        if state == "release":
            ay = bc[1]; ax = min(124, bc[0] + 36)
            limb(d, ox, oy, [(bc[0]+6, ay), (ax, ay)], alpha(STEEL, a), 2.2, rim=False)
            poly(d, ox, oy, [(ax-6, ay-3.4), (ax, ay), (ax-6, ay+3.4)], alpha(STEEL, a))
    if pose.get("eyes_x"): eyes_x(d, ox, oy, head, a, dx=4, col=EYE_O)
    elif a > 40: eye_slit(d, ox, oy, head, a, dx=4, col=EYE_O)
    if pose.get("impact"):
        ix, iy = pose["impact"]
        for ang in (0, 60, 120, 180, 240, 300):
            r = math.radians(ang)
            limb(d, ox, oy, [(ix+math.cos(r)*3, iy+math.sin(r)*3), (ix+math.cos(r)*10, iy+math.sin(r)*10)], alpha(EYE_O, a), 2.2, rim=False)
    if pose.get("wisps"):
        for (wx, wy, wr, wa) in pose["wisps"]:
            circle(d, ox, oy, (wx, wy), wr, (30, 30, 50, int(wa*a/255)))
            circle(d, ox, oy, (wx+2, wy-3), wr*.45, alpha(ORANGE, int(wa*.85*a/255)))
    sheet.alpha_composite(layer)

def ab(**kw):
    p = dict(head=(66, 34), shoulder=(63, 48), hip=(60, 73),
             f_knee=(72, 88), f_foot=(77, 108), b_knee=(54, 89), b_foot=(48, 108),
             f_elbow=(78, 57), f_hand=(84, 65), b_elbow=(52, 61), b_hand=(46, 73), bow="rest")
    p.update(kw); return p

archer = []
for dy in [0, 1, 2, 3, 2, 1]: archer.append(shift(ab(), 0, dy))            # idle 0-5
for i in range(6):                                                          # walk 6-11
    j = [0, 2, 4, 6, 1, 5][i]
    archer.append(shift(ab(f_knee=((_FF[j][0]+60)/2+6, (_FF[j][1]+73)/2-13), f_foot=(_FF[j][0]-3, _FF[j][1]),
                           b_knee=((_BF[j][0]+60)/2-5, (_BF[j][1]+73)/2-12), b_foot=(_BF[j][0]-3, _BF[j][1]),
                           f_elbow=(79, 56), f_hand=(86, 63), b_elbow=(52, 62), b_hand=(45, 74)), 0, [0, 2, 1][i % 3]))
for i, (fh, bh, st) in enumerate([                                          # shoot 12-19
        ((88, 56), (64, 58), "draw"), ((90, 52), (70, 48), "aim"), ((90, 52), (69, 48), "aim"),
        ((90, 52), (70, 49), "aim"), ((90, 52), (88, 58), "release"), ((92, 58), (58, 74), "rest"),
        ((88, 62), (50, 72), "rest"), ((84, 65), (46, 73), "rest")]):
    archer.append(ab(f_elbow=((fh[0]+63)/2+6, (fh[1]+48)/2), f_hand=fh,
                     b_elbow=((bh[0]+63)/2-4, (bh[1]+48)/2), b_hand=bh, bow=st))
for i in range(2):                                                          # hurt 20-21
    archer.append(shift(ab(f_elbow=(44, 38), f_hand=(32, 28), b_elbow=(76, 42), b_hand=(88, 32),
                           bow="none", impact=(50, 42) if i == 0 else None), -i*3, -i*2))
for i in range(2):                                                          # dodge 22-23 (duck & lean back)
    archer.append(ab(head=(60, 44 - i*4), shoulder=(60, 58 - i*4), hip=(58, 78 - i*3),
                     f_knee=(76, 90), f_foot=(86, 108), b_knee=(48, 92), b_foot=(38, 108),
                     f_elbow=(76, 66), f_hand=(82, 76), b_elbow=(48, 68), b_hand=(40, 80), bow="rest"))
archer.append(shift(ab(f_elbow=(44, 38), f_hand=(32, 28), b_elbow=(76, 42), b_hand=(88, 32), bow="none", eyes_x=True), 0, -10))  # death 24-29
archer.append(shift(ab(head=(54, 52), shoulder=(58, 63), hip=(64, 82),
                       f_knee=(84, 80), f_foot=(94, 92), b_knee=(54, 94), b_foot=(44, 104),
                       f_elbow=(40, 52), f_hand=(28, 44), b_elbow=(72, 50), b_hand=(82, 40), bow="none", eyes_x=True), 0, -2))
_aly2 = dict(head=(34, 96), shoulder=(47, 99), hip=(70, 101),
             f_knee=(88, 94), f_foot=(106, 98), b_knee=(86, 106), b_foot=(102, 110),
             f_elbow=(52, 88), f_hand=(62, 80), b_elbow=(40, 108), b_hand=(28, 112), bow="none", eyes_x=True, cloak=False)
archer.append(ab(**_aly2))
archer.append(ab(**dict(_aly2, alpha=170)))
archer.append(ab(**dict(_aly2, alpha=120)))
archer.append(ab(**dict(_aly2, alpha=90, wisps=[(52, 74, 7, 130), (70, 60, 5, 100), (86, 46, 4, 80)])))
assert len(archer) == 30, len(archer)

# =================================================================
# ONI BOSS V2
# =================================================================
def draw_oni(sheet, ox, oy, pose):
    layer = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = pose.get("alpha", 255)
    ink, ink2 = alpha(INK, a), alpha(INK2, a)
    org, bone = alpha(ORANGE, a), alpha(BONE, a)
    head, sho, hip = pose["head"], pose["shoulder"], pose["hip"]
    limb(d, ox, oy, [sho, pose["b_elbow"], pose["b_hand"]], ink2, 15)
    limb(d, ox, oy, [hip, pose["b_knee"], pose["b_foot"]], ink2, 16)
    # barrel torso with pectoral shading + glowing cracks
    poly(d, ox, oy, [(sho[0]-27, sho[1]-9), (sho[0]+27, sho[1]-9), (hip[0]+20, hip[1]+4), (hip[0]-20, hip[1]+4)], ink)
    poly(d, ox, oy, [(sho[0]-27, sho[1]-9), (sho[0]+2, sho[1]-9), (hip[0]-2, hip[1]+4), (hip[0]-20, hip[1]+4)], ink2)
    for crack in [[(sho[0]-9, sho[1]+2), (sho[0]-4, sho[1]+13), (sho[0]-10, sho[1]+24)],
                  [(sho[0]+11, sho[1]+6), (sho[0]+6, sho[1]+17)], [(sho[0]+1, sho[1]+22), (sho[0]+7, sho[1]+32)]]:
        limb(d, ox, oy, crack, alpha((255, 120, 30), int(210*a/255)), 2.2, rim=False)
    poly(d, ox, oy, [(hip[0]-21, hip[1]+2), (hip[0]+21, hip[1]+2), (hip[0]+16, hip[1]+19), (hip[0]-16, hip[1]+19)], ink2)
    limb(d, ox, oy, [(hip[0]-20, hip[1]+1), (hip[0]+20, hip[1]+1)], org, 6, rim=False)
    limb(d, ox, oy, [hip, pose["f_knee"], pose["f_foot"]], ink, 17)
    for toe in (-5, 3):
        limb(d, ox, oy, [(pose["f_foot"][0]+5, pose["f_foot"][1]), (pose["f_foot"][0]+12, pose["f_foot"][1]+toe)], bone, 2.4, rim=False)
    def club(hand, end):
        limb(d, ox, oy, [hand, end], alpha(WOOD, a), 8.5, rim=False)
        circle(d, ox, oy, end, 12.5, alpha((18, 14, 22), a))
        circle(d, ox, oy, end, 9, ink2)
        for (sx2, sy2) in [(-7, -7), (6, -8), (8, 5), (-8, 6), (0, 0)]:
            circle(d, ox, oy, (end[0]+sx2, end[1]+sy2), 2.5, org)
    if pose.get("club"): club(pose["f_hand"], pose["club"])
    if pose.get("club_drop"): club(pose["club_drop"][0], pose["club_drop"][1])
    limb(d, ox, oy, [sho, pose["f_elbow"], pose["f_hand"]], ink, 15)
    circle(d, ox, oy, head, 19, ink)
    poly(d, ox, oy, [(head[0]-16, head[1]-9), (head[0]-30, head[1]-27), (head[0]-9, head[1]-19)], bone)
    poly(d, ox, oy, [(head[0]+14, head[1]-11), (head[0]+25, head[1]-29), (head[0]+5, head[1]-19)], bone)
    poly(d, ox, oy, [(head[0]-13, head[1]-13), (head[0]-4, head[1]-27), (head[0]+3, head[1]-14)], ink2)
    poly(d, ox, oy, [(head[0]-5, head[1]+11), (head[0]+18, head[1]+10), (head[0]+15, head[1]+19), (head[0]-2, head[1]+18)], ink)
    for fx in (4, 12):
        poly(d, ox, oy, [(head[0]+fx, head[1]+17), (head[0]+fx+3.4, head[1]+17), (head[0]+fx+1.7, head[1]+8)], bone)
    poly(d, ox, oy, [(head[0]+9, head[1]+6), (head[0]+13, head[1]+6), (head[0]+11, head[1]+13)], bone)
    if pose.get("roar_marks"):
        for (rx, ry) in [(18, 22), (108, 20), (24, 44), (102, 46)]:
            limb(d, ox, oy, [(rx-5, ry), (rx+5, ry)], alpha(EYE_O, a), 2.2, rim=False)
    if pose.get("eyes_x"): eyes_x(d, ox, oy, head, a, dx=6, col=EYE_O)
    elif a > 40:
        eye_slit(d, ox, oy, head, a, dx=4, col=EYE_O)
        eye_slit(d, ox, oy, (head[0]+9, head[1]+1), a, dx=3, col=EYE_O)
    if pose.get("slam"):
        sx2, sy2 = pose["slam"]
        for (dx, dy, ln2) in [(-18, 0, 13), (18, 0, 13), (-11, -9, 10), (12, -10, 10)]:
            limb(d, ox, oy, [(sx2+dx, sy2+dy), (sx2+dx+(ln2 if dx > 0 else -ln2), sy2+dy)], alpha(EYE_O, a), 2.4, rim=False)
    if pose.get("impact"):
        ix, iy = pose["impact"]
        for ang in (0, 60, 120, 180, 240, 300):
            r = math.radians(ang)
            limb(d, ox, oy, [(ix+math.cos(r)*4, iy+math.sin(r)*4), (ix+math.cos(r)*13, iy+math.sin(r)*13)], alpha(EYE_O, a), 2.6, rim=False)
    if pose.get("wisps"):
        for (wx, wy, wr, wa) in pose["wisps"]:
            circle(d, ox, oy, (wx, wy), wr, (30, 30, 50, int(wa*a/255)))
            circle(d, ox, oy, (wx+2, wy-3), wr*.45, alpha(ORANGE, int(wa*.85*a/255)))
    sheet.alpha_composite(layer)

def ob(**kw):
    p = dict(head=(64, 32), shoulder=(62, 54), hip=(60, 83),
             f_knee=(76, 97), f_foot=(84, 114), b_knee=(48, 97), b_foot=(40, 114),
             f_elbow=(86, 67), f_hand=(96, 79), b_elbow=(40, 69), b_hand=(30, 85), club=(106, 32))
    p.update(kw); return p

oni = []
for i, dy in enumerate([0, 2, 3, 3, 2, 0]): oni.append(shift(ob(club=(106 - i % 3, 32 - (i % 2) * 4)), 0, dy))   # idle 0-5
_WO = [((80, 95), (94, 107), (46, 95), (32, 109)), ((72, 99), (70, 114), (54, 97), (44, 111)),
       ((56, 95), (40, 107), (78, 95), (94, 109)), ((58, 99), (46, 114), (72, 99), (76, 114))]
for i in range(8):                                                                                              # walk 6-13
    fk, ff, bk, bf = _WO[i % 4]
    oni.append(shift(ob(f_knee=fk, f_foot=ff, b_knee=bk, b_foot=bf, club=(104, 34 + (i % 2) * 5)), 0, [0, 2, 0, 2][i % 4]))
for i, (hand, club, slam) in enumerate([                                                                        # attack 14-20
        ((92, 56), (66, 8), None), ((86, 48), (42, 6), None), ((90, 44), (38, 14), None),
        ((102, 64), (122, 78), None), ((103, 86), (122, 112), (120, 116)), ((100, 84), (118, 96), None),
        ((97, 79), (110, 46), None)]):
    oni.append(ob(f_elbow=((hand[0]+62)/2+8, (hand[1]+54)/2), f_hand=hand, club=club, slam=slam,
                  head=(62 - i, 33) if i < 3 else (66 + i, 34)))
for i in range(2):                                                                                              # hurt 21-22
    oni.append(shift(ob(head=(55, 33), f_elbow=(42, 46), f_hand=(28, 36), club=(34, 70),
                        b_elbow=(76, 48), b_hand=(88, 38), impact=(44, 52) if i == 0 else None), -i*3, -i*2))
for i in range(3):                                                                                              # roar 23-25
    oni.append(ob(head=(64, 28 - i), f_elbow=(34, 44 - i*3), f_hand=(22, 30 - i*5), club=(16, 8),
                  b_elbow=(88, 46 - i*3), b_hand=(100, 32 - i*5), roar_marks=(i == 1)))
oni.append(shift(ob(head=(54, 33), f_elbow=(40, 44), f_hand=(26, 34), club=(30, 66),                            # death 26-31
                    b_elbow=(78, 46), b_hand=(90, 36), eyes_x=True), 0, -4))
oni.append(shift(ob(head=(58, 45), shoulder=(60, 65), hip=(60, 91),
                    f_knee=(82, 99), f_foot=(92, 114), b_knee=(56, 105), b_foot=(50, 114),
                    f_elbow=(84, 73), f_hand=(94, 87), club=(112, 62), eyes_x=True), 0, 4))
oni.append(shift(ob(head=(48, 61), shoulder=(56, 73), hip=(66, 91),
                    f_knee=(86, 87), f_foot=(98, 95), b_knee=(56, 101), b_foot=(44, 109),
                    f_elbow=(36, 61), f_hand=(24, 51), club=(18, 84), b_elbow=(74, 59), b_hand=(84, 49), eyes_x=True), 0, 2))
_oly3 = dict(head=(30, 94), shoulder=(46, 98), hip=(74, 101),
             f_knee=(92, 94), f_foot=(110, 98), b_knee=(90, 107), b_foot=(106, 112),
             f_elbow=(54, 86), f_hand=(64, 78), b_elbow=(38, 109), b_hand=(24, 114),
             club=None, club_drop=((72, 110), (104, 112)), eyes_x=True)
oni.append(ob(**_oly3))
oni.append(ob(**dict(_oly3, alpha=150)))
oni.append(ob(**dict(_oly3, alpha=90, wisps=[(50, 70, 8, 130), (70, 54, 6, 105), (90, 40, 5, 85)])))
assert len(oni) == 32, len(oni)

# =================================================================
save_sheet("shadow-ninja-v2", 9, ninja, draw_ninja, {
    "idle": {"frames": [0,1,2,3,4,5], "fps": 7, "loop": True},
    "run": {"frames": [6,7,8,9,10,11,12,13], "fps": 14, "loop": True},
    "jump": {"frames": [14,15], "fps": 9, "loop": False},
    "doubleJump": {"frames": [16,17,18], "fps": 12, "loop": False},
    "fall": {"frames": [19,20], "fps": 6, "loop": True},
    "wallSlide": {"frames": [21,22], "fps": 6, "loop": True},
    "swordAttack": {"frames": [23,24,25,26,27], "fps": 20, "loop": False},
    "throw": {"frames": [28,29,30], "fps": 13, "loop": False},
    "dash": {"frames": [31,32,33], "fps": 16, "loop": True},
    "hurt": {"frames": [34,35], "fps": 8, "loop": False},
    "land": {"frames": [36,37], "fps": 11, "loop": False},
    "crouch": {"frames": [38,39], "fps": 5, "loop": True},
    "death": {"frames": [40,41,42,43,44], "fps": 8, "loop": False}})

save_sheet("samurai-guard-v2", 6, samurai, draw_samurai, {
    "idle": {"frames": [0,1,2,3,4,5], "fps": 6, "loop": True},
    "walk": {"frames": [6,7,8,9,10,11,12,13], "fps": 11, "loop": True},
    "attack": {"frames": [14,15,16,17,18,19], "fps": 16, "loop": False},
    "hurt": {"frames": [20,21], "fps": 8, "loop": False},
    "block": {"frames": [22,23], "fps": 6, "loop": True},
    "death": {"frames": [24,25,26,27,28,29], "fps": 8, "loop": False}})

save_sheet("shadow-archer-v2", 6, archer, draw_archer, {
    "idle": {"frames": [0,1,2,3,4,5], "fps": 6, "loop": True},
    "walk": {"frames": [6,7,8,9,10,11], "fps": 10, "loop": True},
    "shoot": {"frames": [12,13,14,15,16,17,18,19], "fps": 14, "loop": False},
    "hurt": {"frames": [20,21], "fps": 8, "loop": False},
    "dodge": {"frames": [22,23], "fps": 8, "loop": False},
    "death": {"frames": [24,25,26,27,28,29], "fps": 8, "loop": False}})

save_sheet("oni-boss-v2", 8, oni, draw_oni, {
    "idle": {"frames": [0,1,2,3,4,5], "fps": 6, "loop": True},
    "walk": {"frames": [6,7,8,9,10,11,12,13], "fps": 9, "loop": True},
    "attack": {"frames": [14,15,16,17,18,19,20], "fps": 13, "loop": False},
    "hurt": {"frames": [21,22], "fps": 8, "loop": False},
    "roar": {"frames": [23,24,25], "fps": 7, "loop": False},
    "death": {"frames": [26,27,28,29,30,31], "fps": 7, "loop": False}})

print("V2 sheets done.")

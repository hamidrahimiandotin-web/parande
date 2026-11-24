#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate placeholder art assets (stand-in for the ZIP originals)."""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter

A = "/workspace/assets"
os.makedirs(A, exist_ok=True)
S = 4  # supersample factor

PURPLE   = (134, 53, 207)     # #8635CF
INK      = (67, 27, 104)      # #431B68
CREAM    = (255, 250, 240)
BODY     = (168, 118, 224)
BODY_D   = (128, 78, 180)
WING     = (196, 158, 240)
BELLY    = (255, 233, 170)
BEAK     = (245, 166, 35)
BEAK_D   = (214, 130, 20)

def canvas(w, h, color):
    img = Image.new("RGB", (w*S, h*S), color)
    return img, ImageDraw.Draw(img)

def save(img, name, quality=82):
    img = img.resize((img.width//S, img.height//S), Image.LANCZOS)
    img.save(os.path.join(A, name), "WEBP", quality=quality)
    print("wrote", name, img.size)

def leaf_shape(d, cx, cy, rx, ry, tilt=0.0):
    pts = []
    for i in range(60):
        t = i/60*2*math.pi
        x = rx*math.cos(t)
        y = ry*math.sin(t)
        if tilt:
            x, y = x*math.cos(tilt)-y*math.sin(tilt), x*math.sin(tilt)+y*math.cos(tilt)
        pts.append((cx+x, cy+y))
    d.polygon(pts)

def draw_book_base(d, W, H):
    """open stitched book on warm background"""
    bg = (246, 236, 220)
    d.rectangle([0, 0, W, H], fill=bg)
    px0, py0 = int(W*0.10), int(H*0.16)
    px1, py1 = int(W*0.90), int(H*0.86)
    d.rounded_rectangle([px0+12, py0+16, px1+12, py1+20], radius=28, fill=(214, 196, 168))
    d.rounded_rectangle([px0, py0, px1, py1], radius=28, fill=CREAM, outline=(222, 205, 178), width=4)
    midx = (px0+px1)//2
    d.line([(midx, py0+10), (midx, py1-10)], fill=(226, 210, 185), width=7)
    fx0, fy0 = int(W*0.17), int(H*0.24)
    fx1, fy1 = int(W*0.83), int(H*0.78)
    step = 30
    col = (196, 176, 146)
    x = fx0
    while x + 16 < fx1:
        d.line([(x, fy0), (x+16, fy0)], fill=col, width=6)
        d.line([(x, fy1), (x+16, fy1)], fill=col, width=6)
        x += step
    y = fy0
    while y + 16 < fy1:
        d.line([(fx0, y), (fx0, y+16)], fill=col, width=6)
        d.line([(fx1, y), (fx1, y+16)], fill=col, width=6)
        y += step
    return (fx0, fy0, fx1, fy1)


def _poly_pts(cx, cy, rx, ry, n=72):
    pts = []
    for i in range(n):
        t = i/n*2*math.pi
        pts.append((cx+rx*math.cos(t), cy+ry*math.sin(t)))
    return pts


def draw_thread_bird(d, field, stage):
    """stage 0..4 : stitched sketch -> eye opens -> wing grows -> lifts off -> flying"""
    fx0, fy0, fx1, fy1 = field
    cx, cy = (fx0+fx1)//2, (fy0+fy1)//2
    R = min(fx1-fx0, fy1-fy0)
    lift = {0: 0, 1: 0, 2: -int(R*0.02), 3: -int(R*0.09), 4: -int(R*0.24)}[stage]
    cy += lift
    body_rx, body_ry = int(R*0.27), int(R*0.21)

    faint = (196, 172, 214)      # pale stitch-only look
    dash  = (150, 120, 180)      # sketch outline colour
    ink   = INK

    def sketch(pts, close=True, color=dash, width=6):
        p = list(pts) + ([pts[0]] if close else [])
        d.line(p, fill=color, width=width, joint="curve")

    # ---- tail -------------------------------------------------------------
    tail = [(cx-body_rx+10, cy-10), (cx-body_rx-int(R*0.17), cy-int(R*0.11)),
            (cx-body_rx-int(R*0.13), cy+int(R*0.03))]
    if stage >= 2:
        d.polygon(tail, fill=BODY_D, outline=ink)
    else:
        sketch(tail)

    # ---- body -------------------------------------------------------------
    bbox = [cx-body_rx, cy-body_ry, cx+body_rx, cy+body_ry]
    if stage >= 1:
        d.ellipse(bbox, fill=BODY, outline=ink, width=7)
        d.ellipse([cx-int(body_rx*0.15), cy-int(body_ry*0.05),
                   cx+int(body_rx*0.78), cy+int(body_ry*0.94)], fill=BELLY)
    else:
        d.ellipse(bbox, fill=None, outline=dash, width=7)
        d.arc([cx-int(body_rx*0.15), cy-int(body_ry*0.05),
               cx+int(body_rx*0.78), cy+int(body_ry*0.94)], 320, 55, fill=dash, width=5)

    # ---- head -------------------------------------------------------------
    hx, hy = cx+int(body_rx*0.74), cy-int(body_ry*0.78)
    hr = int(R*0.14)
    if stage >= 1:
        d.ellipse([hx-hr, hy-hr, hx+hr, hy+hr], fill=BODY, outline=ink, width=7)
    else:
        d.ellipse([hx-hr, hy-hr, hx+hr, hy+hr], fill=None, outline=dash, width=7)

    # crest feathers
    for ang in (-105, -80, -55):
        t = math.radians(ang)
        ex, ey = hx+int(hr*1.1*math.cos(t)), hy+int(hr*1.1*math.sin(t))
        mx, my = hx+int(hr*2.0*math.cos(t+0.22)), hy+int(hr*2.0*math.sin(t+0.22))
        d.line([(ex, ey), (mx, my)], fill=BEAK if stage >= 1 else dash, width=8)

    # beak
    bk = [(hx+hr-6, hy-8), (hx+hr+int(R*0.10), hy+6), (hx+hr-8, hy+14)]
    if stage >= 1:
        d.polygon(bk, fill=BEAK, outline=ink)
    else:
        d.polygon(bk, fill=None, outline=dash)

    # eye
    if stage == 0:
        d.line([(hx+3, hy), (hx+17, hy)], fill=dash, width=6)          # closed stitch
    elif stage == 1:
        d.ellipse([hx+1, hy-9, hx+19, hy+9], fill=(255, 255, 255), outline=ink, width=5)
        d.ellipse([hx+6, hy-4, hx+15, hy+5], fill=ink)                 # newly opened
    else:
        d.ellipse([hx+1, hy-10, hx+19, hy+10], fill=(255, 255, 255), outline=ink, width=5)
        d.ellipse([hx+5, hy-5, hx+16, hy+6], fill=ink)
        d.ellipse([hx+9, hy-3, hx+13, hy+1], fill=(255, 255, 255))     # sparkle

    # ---- wing (grows with stage) -----------------------------------------
    wx, wy = cx-int(body_rx*0.05), cy-int(body_ry*0.30)
    wlen = {0: 0.10, 1: 0.13, 2: 0.20, 3: 0.27, 4: 0.33}[stage] * R
    wang = {0: 0.30, 1: 0.45, 2: 0.80, 3: 1.05, 4: 1.45}[stage]
    tipx = wx - int(wlen*math.cos(wang))
    tipy = wy - int(wlen*math.sin(wang))
    pts = [(wx-22, wy+16), (wx+18, wy+12), (tipx+12, tipy+20), (tipx-16, tipy-8), (wx-34, wy-4)]
    if stage >= 2:
        d.polygon(pts, fill=WING, outline=ink)
        for k in range(3):
            d.line([(wx-10-k*6, wy-2-k*4), (tipx+k*7-8, tipy+12+k*5)], fill=BODY_D, width=5)
    else:
        d.polygon(pts, fill=None, outline=dash)

    # feet: visible only while not yet fully flying
    if stage in (1, 2, 3):
        fyb = cy+body_ry-4
        dyb = (fy0+fy1)//2 + int(R*0.34) - lift if False else None
        for s in (-1, 1):
            fx_ = cx + s*int(body_rx*0.35)
            d.line([(fx_, fyb), (fx_, fyb+int(R*0.10*(1 if stage < 3 else 0.5)))],
                   fill=BEAK_D, width=8)
            d.line([(fx_-10, fyb+int(R*0.10*(1 if stage < 3 else 0.5))),
                    (fx_+12, fyb+int(R*0.10*(1 if stage < 3 else 0.5)))], fill=BEAK_D, width=7)

    # motion marks when flying
    if stage == 4:
        for k in range(3):
            yy = cy + int(R*0.14) + k*20
            d.line([(cx-body_rx-int(R*0.12)-k*16, yy), (cx-body_rx-int(R*0.06)-k*8, yy)],
                   fill=faint, width=7)

    # little flowers embroidered on the cloth
    rnd = random.Random(7)
    for (fx_, fy_) in [(fx0+int(R*0.10), fy0+int(R*0.12)), (fx1-int(R*0.09), fy0+int(R*0.16)),
                       (fx0+int(R*0.13), fy1-int(R*0.12)), (fx1-int(R*0.11), fy1-int(R*0.09))]:
        col = [(240, 150, 180), (120, 170, 235), (245, 200, 90)][rnd.randrange(3)]
        for a in range(5):
            t = a/5*2*math.pi
            d.ellipse([fx_+10*math.cos(t)-6, fy_+10*math.sin(t)-6,
                       fx_+10*math.cos(t)+6, fy_+10*math.sin(t)+6], fill=col)
        d.ellipse([fx_-5, fy_-5, fx_+5, fy_+5], fill=BEAK)


def make_puzzle_frames():
    W, H = 760, 620
    for stage in range(5):
        img, d = canvas(W, H, CREAM)
        field = draw_book_base(d, W*S, H*S)   # already in supersampled coords
        draw_thread_bird(d, field, stage)
        save(img, f"parandeh-storybird-{stage}.webp")


def make_thumb_crops():
    """detail crops from each stage frame used as the 4 small stage indicators"""
    boxes = [  # eye region, wing region, lift-off region, flight region
        (0.52, 0.20, 0.78, 0.42),
        (0.28, 0.22, 0.58, 0.50),
        (0.30, 0.50, 0.70, 0.78),
        (0.18, 0.10, 0.82, 0.62),
    ]
    for i, (a, b, c, dd) in enumerate(boxes, start=1):
        src = Image.open(os.path.join(A, f"parandeh-storybird-{i}.webp")).convert("RGB")
        w, h = src.size
        crop = src.crop((int(a*w), int(b*h), int(c*w), int(dd*h)))
        crop = crop.resize((240, 180), Image.LANCZOS)
        crop.save(os.path.join(A, f"puzzle-detail-{i}.webp"), "WEBP", quality=80)
        print("wrote puzzle-detail-%d.webp" % i)

def make_banner():
    W, H = 1440, 560
    img, d = canvas(W, H, (238, 226, 250))
    Ws, Hs = W*S, H*S
    # sky gradient bands
    for i in range(12):
        f = i/11
        col = tuple(int(238-(238-208)*f*.6), ) if False else (
            int(240-30*f), int(228-10*f), int(252-14*f))
        d.rectangle([0, int(Hs*i/12), Ws, int(Hs*(i+1)/12)+2], fill=col)
    # sun
    d.ellipse([Ws-int(Ws*0.30), int(Hs*0.08), Ws-int(Ws*0.18), int(Hs*0.08)+int(Ws*0.12)],
              fill=(255, 214, 120), outline=(245, 186, 66), width=6)
    # clouds
    for (cxx, cyy, sc) in [(0.16, 0.22, 1.0), (0.45, 0.14, 0.7), (0.70, 0.30, 0.9)]:
        cx, cy = int(Ws*cxx), int(Hs*cyy)
        for (ox, oy, r) in [(-60, 0, 46), (0, -22, 58), (64, 4, 44), (10, 18, 50)]:
            d.ellipse([cx+ox*sc-r*sc, cy+oy*sc-r*sc, cx+ox*sc+r*sc, cy+oy*sc+r*sc], fill=(255, 255, 255))
    # hills
    d.ellipse([-int(Ws*0.2), int(Hs*0.62), int(Ws*0.55), int(Hs*1.5)], fill=(178, 218, 158))
    d.ellipse([int(Ws*0.4), int(Hs*0.68), int(Ws*1.25), int(Hs*1.6)], fill=(150, 200, 140))
    # tree left
    tx, ty = int(Ws*0.08), int(Hs*0.62)
    d.rectangle([tx-10, ty, tx+14, ty+120], fill=(140, 100, 70))
    for (ox, oy, r) in [(-30, -40, 55), (26, -50, 50), (0, -90, 58)]:
        d.ellipse([tx+ox-r, ty+oy-r, tx+ox+r, ty+oy+r], fill=(110, 170, 110))
    # big bird right side (flying)
    bx, by = int(Ws*0.72), int(Hs*0.42)
    R = int(min(Ws, Hs)*0.30)
    class DD: pass
    field = (bx-R, by-R, bx+R, by+R)
    draw_thread_bird(d, (bx-int(R*0.9), by-int(R*0.9), bx+int(R*0.9), by+int(R*0.9)), 4)
    # small birds
    for (sx, sy, ss) in [(0.30, 0.35, 0.35), (0.42, 0.28, 0.25)]:
        cx, cy = int(Ws*sx), int(Hs*sy)
        d.arc([cx-40*ss, cy-30*ss, cx, cy+30*ss], 200, 340, fill=INK, width=max(4,int(10*ss)))
        d.arc([cx, cy-30*ss, cx+40*ss, cy+30*ss], 200, 340, fill=INK, width=max(4,int(10*ss)))
    save(img, "banner-main.webp", quality=80)

def card_art(name, accent, motif):
    W, H = 600, 440
    img, d = canvas(W, H, (255, 255, 255))
    Ws, Hs = W*S, H*S
    d.rectangle([0, 0, Ws, Hs], fill=accent)
    # lighter inner panel
    pad = int(Ws*0.06)
    light = tuple(min(255, c+70) for c in accent)
    d.rounded_rectangle([pad, pad, Ws-pad, Hs-pad], radius=40, fill=light)
    cx, cy = Ws//2, Hs//2
    if motif == "cat":
        fur = (250, 214, 130)
        d.ellipse([cx-150, cy-60, cx+150, cy+130], fill=fur, outline=(190, 140, 60), width=6)
        d.ellipse([cx-90, cy-160, cx+90, cy+10], fill=fur, outline=(190, 140, 60), width=6)
        for s in (-1, 1):
            d.polygon([(cx+s*70, cy-140), (cx+s*110, cy-220), (cx+s*20, cy-160)], fill=fur, outline=(190, 140, 60))
        for s in (-1, 1):
            d.ellipse([cx+s*45-12, cy-90, cx+s*45+12, cy-66], fill=INK)
        d.polygon([(cx-12, cy-40), (cx+12, cy-40), (cx, cy-22)], fill=(230, 120, 120))
        # puff bubbles
        for (bx, by, br) in [(-190, -140, 46), (200, -120, 38), (170, 120, 30)]:
            d.ellipse([cx+bx-br, cy+by-br, cx+bx+br, cy+by+br], outline=(255, 255, 255), width=6)
    elif motif == "windmill":
        gr = (150, 205, 150)
        d.rectangle([0, Hs-int(Hs*0.22), Ws, Hs], fill=gr)
        d.polygon([(cx-70, cy+150), (cx+70, cy+150), (cx+34, cy-90), (cx-34, cy-90)], fill=(240, 240, 245), outline=INK)
        d.polygon([(cx-34, cy-90), (cx+34, cy-90), (cx, cy-160)], fill=(215, 90, 90))
        for a in range(4):
            t = a*math.pi/2 + 0.5
            d.line([(cx, cy-110), (cx+int(150*math.cos(t)), cy-110+int(150*math.sin(t)))], fill=(255, 255, 255), width=16)
        d.ellipse([cx-14, cy-124, cx+14, cy-96], fill=BEAK, outline=INK, width=4)
    elif motif == "firefly":
        d.rectangle([0, 0, Ws, Hs], fill=(60, 40, 90))
        d.rounded_rectangle([pad, pad, Ws-pad, Hs-pad], radius=40, fill=(84, 60, 120))
        for (gx, gy, gr) in [(-160, -110, 10), (-60, -170, 7), (150, -60, 9), (90, 130, 8), (-140, 120, 7), (30, -40, 12)]:
            g = Image.new("RGBA", (gr*10, gr*10), (0, 0, 0, 0))
            gd = ImageDraw.Draw(g)
            gd.ellipse([0, 0, gr*10, gr*10], fill=(255, 240, 150, 90))
            gd.ellipse([gr*3, gr*3, gr*7, gr*7], fill=(255, 250, 200, 255))
            img.paste(g, (cx+gx-gr*5, cy+gy-gr*5), g)
            d = ImageDraw.Draw(img)
        # cream character
        d.ellipse([cx-90, cy-40, cx+90, cy+120], fill=(250, 235, 210), outline=(210, 180, 140), width=6)
        d.ellipse([cx-60, cy-120, cx+60, cy+10], fill=(250, 235, 210), outline=(210, 180, 140), width=6)
        for s in (-1, 1):
            d.ellipse([cx+s*32-10, cy-80, cx+s*32+10, cy-60], fill=INK)
    elif motif == "pencil":
        cols = [(240, 120, 120), (120, 170, 235), (245, 200, 90), (140, 200, 140)]
        for i, c in enumerate(cols):
            x0 = int(Ws*0.18) + i*int(Ws*0.16)
            d.polygon([(x0, Hs-80), (x0+50, Hs-80), (x0+25, Hs-140)], fill=(240, 200, 150))
            d.polygon([(x0+13, Hs-110), (x0+37, Hs-110), (x0+25, Hs-140)], fill=INK)
            d.rectangle([x0, int(Hs*0.22), x0+50, Hs-80], fill=c, outline=tuple(max(0, v-40) for v in c), width=4)
            d.rectangle([x0, int(Hs*0.22), x0+50, int(Hs*0.22)+26], fill=(200, 200, 210))
    save(img, name, quality=80)

def make_logos():
    # main bird logo (header, right in RTL)
    W = H = 200
    img = Image.new("RGBA", (W*S, H*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = W*S//2
    R = int(W*S*0.34)
    d.ellipse([cx-R, cy-int(R*0.6), cx+int(R*0.8), cy+R], fill=BODY, outline=INK, width=8)
    hx, hy = cx+int(R*0.55), cy-int(R*0.55)
    hr = int(R*0.45)
    d.ellipse([hx-hr, hy-hr, hx+hr, hy+hr], fill=BODY, outline=INK, width=8)
    d.polygon([(hx+hr-8, hy-6), (hx+hr+int(R*0.45), hy+10), (hx+hr-8, hy+22)], fill=BEAK, outline=INK)
    d.ellipse([hx+4, hy-14, hx+26, hy+8], fill=(255, 255, 255), outline=INK, width=5)
    d.ellipse([hx+10, hy-8, hx+22, hy+4], fill=INK)
    pts = [(cx-30, cy-20), (cx+30, cy-30), (cx-int(R*0.7), cy-int(R*0.9)), (cx-int(R*0.9), cy-int(R*0.6))]
    d.polygon(pts, fill=WING, outline=INK)
    d.rectangle([cx-10, cy+R-6, cx+16, cy+R+40], fill=BEAK, outline=INK)
    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(A, "logo-parandeh.webp"), "WEBP", quality=90)
    print("wrote logo-parandeh.webp")
    # zipad wordmark-style logo (header, left)
    W, H = 220, 90
    img, d = canvas(W, H, (255, 255, 255))
    Ws, Hs = W*S, H*S
    d.rounded_rectangle([6, 6, Ws-6, Hs-6], radius=Hs//3, outline=PURPLE, width=8)
    d.ellipse([int(Ws*0.10), Hs//2-24, int(Ws*0.10)+48, Hs//2+24], fill=PURPLE)
    d.ellipse([int(Ws*0.10)+14, Hs//2-10, int(Ws*0.10)+38, Hs//2+14], fill=(255, 255, 255))
    for i in range(3):
        x0 = int(Ws*0.30) + i*int(Ws*0.20)
        d.rounded_rectangle([x0, Hs//2-18, x0+int(Ws*0.13), Hs//2+18], radius=14,
                            fill=[PURPLE, (120, 170, 235), (245, 190, 90)][i])
    save(img, "logo-zipad.webp", quality=90)

if __name__ == "__main__":
    make_puzzle_frames()
    make_thumb_crops()
    make_banner()
    card_art("story-pishipufaki.webp", (216, 190, 245), "cat")
    card_art("story-dalwind.webp", (176, 214, 248), "windmill")
    card_art("story-florence.webp", (248, 186, 216), "firefly")
    card_art("story-medad.webp, ", (250, 232, 160), "pencil") if False else card_art("story-medad.webp", (250, 232, 160), "pencil")
    make_logos()
    print("done")

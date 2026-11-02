#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visual language: archive / newsprint / torn-paper motion graphics.

All artwork is generated in code from the skill's OFL fonts and 8 generated
photographs. Design space is 720x1280; plates are rendered at x1.12 so the
camera can drift/zoom without losing resolution.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageChops
import numpy as np, math, random, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMG = ROOT / "assets" / "img"
FONTDIR = ROOT / "fonts"

W, H = 720, 1280
S = 1.12
BW, BH = int(W * S), int(H * S)

BG    = (13, 15, 18)
BG2   = (21, 24, 27)
PAPER = (231, 219, 190)
PAPER2= (211, 195, 160)
INK   = (26, 25, 23)
CREAM = (244, 237, 219)
MUT   = (148, 140, 122)
RED   = (199, 56, 42)
RED2  = (231, 88, 62)
AMBER = (226, 172, 76)
TEAL  = (61, 91, 90)
BLACK = (8, 9, 11)

FONTS = {
    "black": "Tajawal-Black.ttf",
    "bold":  "Tajawal-Bold.ttf",
    "reg":   "Tajawal-Regular.ttf",
    "body":  "IBMPlexSansArabic-Regular.ttf",
    "bodyb": "IBMPlexSansArabic-Bold.ttf",
    "num":   "Inter-VF.ttf",
    "disp":  "Lalezar-Regular.ttf",
    "ruqaa": "ArefRuqaa-Regular.ttf",
}
_fcache = {}
def F(key, size):
    k = (key, int(size))
    if k not in _fcache:
        _fcache[k] = ImageFont.truetype(str(FONTDIR / FONTS[key]), max(6, int(size * S)))
    return _fcache[k]

def sc(v): return int(round(v * S))
def rgba(c, a=255): return (c[0], c[1], c[2], a)

# ---------------------------------------------------------------- primitives
def draw(im):
    return ImageDraw.Draw(im, "RGBA")

def text_len(txt, f, direction="rtl"):
    d = ImageDraw.Draw(Image.new("L", (8, 8)))
    return d.textlength(txt, font=f, direction=direction)

def rtl(im, xy, txt, f, fill, anchor="rt", spacing=10, stroke=0, stroke_fill=None,
        direction="rtl"):
    d = draw(im)
    d.text((sc(xy[0]), sc(xy[1])), txt, font=f, fill=fill, direction=direction,
           anchor=anchor, spacing=sc(spacing), stroke_width=sc(stroke),
           stroke_fill=stroke_fill)

def wrap(txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_len(t, f) <= sc(maxw) or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def textblock(im, xy, txt, f, fill, maxw, line_h=1.35, align="right", leading=0,
              stroke=0, stroke_fill=None):
    """xy = top-right anchor for RTL text."""
    lines = wrap(txt, f, maxw)
    lh = sc(f.size / S * line_h)
    for i, line in enumerate(lines):
        rtl(im, (xy[0], xy[1] + i * lh / S), line, f, fill, anchor="rt",
            stroke=stroke, stroke_fill=stroke_fill)
    return len(lines)

def fit(path, size, crop_anchor=0.5):
    im = Image.open(path).convert("RGB")
    w, h = size
    r = max(w / im.width, h / im.height)
    im = im.resize((max(w, int(im.width * r)), max(h, int(im.height * r))), Image.LANCZOS)
    x = int((im.width - w) * crop_anchor); y = int((im.height - h) * crop_anchor)
    return im.crop((x, y, x + w, y + h))

def grade(im, darkness=1.0, sepia=0.0, contrast=1.1, cold=0.0):
    im = ImageEnhance.Contrast(im).enhance(contrast)
    a = np.asarray(im).astype(np.float32)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    if sepia:
        a[..., 0] = lum * (1 + 0.10 * sepia) + 12 * sepia
        a[..., 1] = lum * (1 + 0.01 * sepia) + 4 * sepia
        a[..., 2] = lum * (1 - 0.13 * sepia) - 8 * sepia
    if cold:
        a[..., 2] += 12 * cold; a[..., 0] -= 6 * cold
    a *= darkness
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

_ht_patterns = None
def _halftone_patterns():
    global _ht_patterns
    if _ht_patterns is None:
        # 3x3 dot clusters, from light to dark
        order = [(1, 1), (0, 0), (2, 2), (2, 0), (0, 2), (1, 0), (0, 1), (2, 1), (1, 2)]
        pats = []
        for n in range(10):
            p = np.zeros((3, 3), np.uint8)
            for (y, x) in order[:n]: p[y, x] = 1
            pats.append(p)
        _ht_patterns = np.array(pats)
    return _ht_patterns

def halftone(im, dot=3, ink=INK, paper=PAPER, gamma=1.15):
    g = ImageOps.grayscale(im)
    g = ImageEnhance.Contrast(g).enhance(1.25)
    w, h = g.size
    gw, gh = max(1, math.ceil(w / dot)), max(1, math.ceil(h / dot))
    small = np.asarray(g.resize((gw, gh), Image.LANCZOS)).astype(np.float32) / 255.0
    lvl = np.clip(((1.0 - small) ** gamma * 9.6), 0, 9).astype(np.int32)
    pats = _halftone_patterns()
    grid = pats[lvl]                                    # (gh, gw, 3, 3)
    mask = grid.transpose(0, 2, 1, 3).reshape(gh * 3, gw * 3)[:h, :w]
    out = np.empty((h, w, 3), np.uint8)
    out[:] = np.array(paper, np.uint8)
    out[mask > 0] = np.array(ink, np.uint8)
    return Image.fromarray(out, "RGB")

def noise_overlay(size, seed=0, amp=9):
    rng = np.random.default_rng(seed)
    w, h = size
    n = rng.normal(0, amp, (h, w)).astype(np.int16)
    return n

def paper_tex(w, h, seed=1, base=PAPER, grain=True, stains=True):
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w, 3), np.float32)
    a[:] = np.array(base, np.float32)
    if grain:
        a += rng.normal(0, 5.5, (h, w, 1))
        # paper fibres
        for _ in range(int(h / 14)):
            y = rng.integers(0, h); x = rng.integers(0, w); ln = rng.integers(20, 140)
            a[y, x:min(w, x + ln)] += rng.uniform(-7, 7)
    if stains:
        yy, xx = np.mgrid[0:h, 0:w]
        for _ in range(4):
            cx, cy = rng.integers(0, w), rng.integers(0, h)
            r = rng.uniform(w * .18, w * .6)
            blob = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r))
            a -= blob[..., None] * rng.uniform(6, 18)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

def torn_mask(w, h, seed=1, jag=7, edges="all"):
    rng = np.random.default_rng(seed)
    m = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(m)
    if "t" in edges or edges == "all":
        pts = [(0, 0)] + [(x, int(rng.uniform(0, jag))) for x in range(0, w + 20, 11)] + [(w, 0)]
        d.polygon([(0, 0)] + pts[1:] + [(w, 0)], fill=0)
    if "b" in edges or edges == "all":
        pts = [(x, h - int(rng.uniform(0, jag))) for x in range(0, w + 20, 11)]
        d.polygon([(0, h)] + pts + [(w, h)], fill=0)
    if "l" in edges or edges == "all":
        pts = [(int(rng.uniform(0, jag)), y) for y in range(0, h + 20, 11)]
        d.polygon([(0, 0)] + pts + [(0, h)], fill=0)
    if "r" in edges or edges == "all":
        pts = [(w - int(rng.uniform(0, jag)), y) for y in range(0, h + 20, 11)]
        d.polygon([(w, 0)] + pts + [(w, h)], fill=0)
    return m.filter(ImageFilter.GaussianBlur(0.7))

def card(w, h, seed=1, base=PAPER, edges="all", newspaper=False):
    if newspaper:
        p = fit(IMG / "newspaper_blank.jpg", (w, h), (seed % 7) / 10)
        p = Image.blend(p, Image.new("RGB", (w, h), base), 0.18)
    else:
        p = paper_tex(w, h, seed, base)
    out = p.convert("RGBA")
    out.putalpha(torn_mask(w, h, seed, edges=edges))
    return out

def paste_sprite(im, sp, x, y, angle=0, shadow=10, opacity=1.0):
    """x,y = top-left in design coords; sp is RGBA in plate pixels."""
    if angle:
        sp = sp.rotate(angle, Image.BICUBIC, expand=True)
    if opacity < 1.0:
        a = sp.getchannel("A").point(lambda v: int(v * opacity))
        sp = sp.copy(); sp.putalpha(a)
    if shadow:
        al = sp.getchannel("A").filter(ImageFilter.GaussianBlur(sc(shadow)))
        al = al.point(lambda v: int(v * 0.62))
        sh = Image.new("RGBA", sp.size, (0, 0, 0, 0)); sh.putalpha(al)
        im.paste(sh, (sc(x) + sc(7), sc(y) + sc(11)), sh)
    im.paste(sp, (sc(x), sc(y)), sp)

def tape(im, x, y, w=118, h=30, angle=-8, color=(226, 213, 176), alpha=175):
    sp = Image.new("RGBA", (sc(w), sc(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp, "RGBA")
    d.rectangle((0, 0, sc(w), sc(h)), fill=rgba(color, alpha))
    for i in range(0, sc(w), sc(9)):
        d.line((i, 0, i, sc(h)), fill=(255, 255, 255, 26), width=1)
    sp = sp.rotate(angle, Image.BICUBIC, expand=True)
    im.paste(sp, (sc(x), sc(y)), sp)

def pin(im, x, y, r=8, color=RED):
    d = draw(im)
    d.ellipse((sc(x - r), sc(y - r), sc(x + r), sc(y + r)), fill=rgba(color, 235),
              outline=(60, 20, 16, 220), width=sc(2))
    d.ellipse((sc(x - r * .35), sc(y - r * .45), sc(x - r * .05), sc(y - r * .15)),
              fill=(255, 235, 225, 150))

def stamp(im, x, y, txt, w=None, size=30, color=RED, angle=-11, kind="box"):
    f = F("bold", size)
    tw = int(text_len(txt, f)) + sc(38)
    w = w or tw / S
    h = size * 1.75
    sp = Image.new("RGBA", (sc(w), sc(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp, "RGBA")
    if kind == "box":
        d.rectangle((sc(3), sc(3), sc(w - 3), sc(h - 3)), outline=rgba(color, 215), width=sc(4))
        d.rectangle((sc(9), sc(9), sc(w - 9), sc(h - 9)), outline=rgba(color, 110), width=sc(1))
    else:
        d.ellipse((sc(3), sc(3), sc(w - 3), sc(h - 3)), outline=rgba(color, 215), width=sc(4))
    d.text((sc(w) - sc(19), sc(h) / 2), txt, font=f, fill=rgba(color, 225),
           direction="rtl", anchor="rm")
    # distress
    rng = np.random.default_rng(abs(hash(txt)) % 9999)
    a = np.asarray(sp.getchannel("A")).copy()
    for _ in range(70):
        xx, yy = rng.integers(0, a.shape[1]), rng.integers(0, a.shape[0])
        a[yy:yy + 2, xx:xx + 3] = 0
    sp.putalpha(Image.fromarray(a, "L"))
    sp = sp.rotate(angle, Image.BICUBIC, expand=True)
    im.paste(sp, (sc(x), sc(y)), sp)

def red_string(im, pts, color=RED, width=3):
    d = draw(im)
    p = [(sc(x), sc(y)) for x, y in pts]
    d.line(p, fill=rgba(color, 205), width=sc(width), joint="curve")
    for x, y in (p[0], p[-1]):
        d.ellipse((x - sc(5), y - sc(5), x + sc(5), y + sc(5)), fill=rgba(color, 230))

def ruled(im, x, y, w, n=6, gap=26, color=(70, 62, 48, 70)):
    d = draw(im)
    for i in range(n):
        yy = sc(y + i * gap)
        d.line((sc(x), yy, sc(x + w), yy), fill=color, width=sc(1))

def frame_lines(im, color=(226, 213, 180, 70), m=34):
    d = draw(im)
    d.rectangle((sc(m), sc(m), sc(W - m), sc(H - m)), outline=color, width=sc(1))
    for cx, cy in ((m, m), (W - m, m), (m, H - m), (W - m, H - m)):
        d.line((sc(cx - 10), sc(cy), sc(cx + 10), sc(cy)), fill=color, width=sc(2))
        d.line((sc(cx), sc(cy - 10), sc(cx), sc(cy + 10)), fill=color, width=sc(2))

def tag(im, x, y, txt, bg=RED, fg=CREAM, size=20, pad=12):
    f = F("bodyb", size)
    tw = text_len(txt, f) / S + pad * 2
    th = size * 1.7
    d = draw(im)
    d.rounded_rectangle((sc(x), sc(y), sc(x + tw), sc(y + th)), radius=sc(4),
                        fill=rgba(bg, 235))
    rtl(im, (x + tw - pad, y + th * .18), txt, f, rgba(fg, 245), anchor="rt")

def big_num(im, x, y, txt, size=110, color=CREAM, sub=None, subcolor=MUT, align="right"):
    f = F("num", size)
    d = draw(im)
    rtl(im, (x, y), txt, F("num", size), rgba(color), anchor="rt", direction="ltr")
    if sub:
        rtl(im, (x, y + size * 1.08), sub, F("bodyb", 22), rgba(subcolor), anchor="rt")

def waveform_static(im, x, y, w, h, n=52, seed=3, color=(196, 74, 55, 175)):
    rng = np.random.default_rng(seed)
    d = draw(im)
    bw = w / n
    for i in range(n):
        env = 0.25 + 0.75 * abs(math.sin(i * 0.21 + seed))
        bh = h * (0.12 + 0.85 * rng.random() * env)
        xx = sc(x + i * bw)
        d.rounded_rectangle((xx, sc(y + (h - bh) / 2), xx + max(1, sc(bw * .45)),
                             sc(y + (h + bh) / 2)), radius=sc(1), fill=color)

# ------------------------------------------------------------------ plate base
class Plate:
    def __init__(self, bg=BG):
        self.im = Image.new("RGB", (BW, BH), bg)

    def photo(self, path, alpha=255, darkness=0.62, sepia=0.0, cold=0.0, contrast=1.12,
              crop=0.5, blur=0):
        p = fit(IMG / path, (BW, BH), crop)
        p = grade(p, darkness=darkness, sepia=sepia, cold=cold, contrast=contrast)
        if blur: p = p.filter(ImageFilter.GaussianBlur(sc(blur)))
        if alpha < 255:
            p = Image.blend(Image.new("RGB", (BW, BH), BG), p, alpha / 255)
        self.im = p
        return self

    def wash(self, color=BG, a=120, y0=0, y1=H):
        d = draw(self.im)
        d.rectangle((0, sc(y0), sc(W), sc(y1)), fill=rgba(color, a))

    def gradient(self, top=(10, 12, 15, 215), bottom=(10, 12, 15, 60)):
        ov = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        arr = np.zeros((BH, BW, 4), np.uint8)
        for c in range(4):
            arr[..., c] = np.linspace(top[c], bottom[c], BH, dtype=np.uint8)[:, None]
        ov = Image.fromarray(arr, "RGBA")
        self.im = Image.alpha_composite(self.im.convert("RGBA"), ov).convert("RGB")

    def vignette(self, strength=0.55):
        yy, xx = np.mgrid[0:BH, 0:BW]
        cx, cy = BW / 2, BH / 2
        r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / 1.35
        v = np.clip(1 - strength * np.clip(r, 0, 1) ** 2, 0, 1)[..., None]
        a = (np.asarray(self.im).astype(np.float32) * v).astype(np.uint8)
        self.im = Image.fromarray(a, "RGB")

    def grain(self, amp=7, seed=0):
        a = np.asarray(self.im).astype(np.int16)
        a += noise_overlay((BW, BH), seed, amp)[..., None]
        self.im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")

    def finish(self, vig=0.5, grain=6, seed=0):
        self.vignette(vig); self.grain(grain, seed)
        return self.im.copy()

# ------------------------------------------------------------------ clips
def make_clip(photo, w=300, h=350, caption="", seed=1, ht=True, paper_base=PAPER,
              label="", stamp_txt=None, border=True):
    """A torn newspaper/paper clipping with a halftone photograph."""
    w, h = sc(w), sc(h)
    c = card(w, h, seed, paper_base, newspaper=True)
    ph = fit(IMG / photo, (w - sc(26), int(h * .64)), (seed % 5) / 8)
    ph = grade(ph, darkness=.92, sepia=.18, contrast=1.18)
    if ht:
        ph = halftone(ph, dot=3, ink=(44, 38, 31), paper=(214, 199, 165))
    c.paste(ph, (sc(13), sc(15)))
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle((sc(13), sc(15), w - sc(13), sc(15) + int(h * .64)),
                outline=(70, 58, 42, 130), width=sc(1))
    yy = sc(24) + int(h * .64)
    if label:
        d.text((w - sc(20), yy), label, font=F("bodyb", 15), fill=(120, 62, 48, 210),
               direction="rtl", anchor="rt")
        yy += sc(26)
    if caption:
        f = F("body", 17)
        for line in wrap(caption, f, (w - sc(34)) / S)[:3]:
            d.text((w - sc(20), yy), line, font=f, fill=(46, 40, 33, 235),
                   direction="rtl", anchor="rt")
            yy += sc(24)
    if stamp_txt:
        stamp(c, sc(38), h - sc(74), stamp_txt, size=17, angle=-14)
    c.putalpha(ImageChops.multiply(c.getchannel("A"), torn_mask(w, h, seed + 91, jag=6)))
    return c

def photo_card(photo, w=300, h=390, seed=2, tint=None):
    w, h = sc(w), sc(h)
    c = card(w, h, seed, PAPER2)
    ph = fit(IMG / photo, (w - sc(20), h - sc(20)), (seed % 5) / 8)
    ph = grade(ph, darkness=.88, sepia=.12, contrast=1.15)
    c.paste(ph, (sc(10), sc(10)))
    c.putalpha(ImageChops.multiply(c.getchannel("A"), torn_mask(w, h, seed + 7, jag=9)))
    return c

# ------------------------------------------------------------------ builders
def b_hero(p, *, photo="plane_storm.jpg", kicker="ملف رقم 01 / وثائقي",
           title="الثواني\nالأخيرة", sub="الرحلة التي سقطت قبل الوصول إلى البهاما",
           stamp_txt="سري", darkness=.52, top_band=True):
    p.photo(photo, darkness=darkness, sepia=.05, cold=.15, contrast=1.2)
    p.wash(BG, 92); p.gradient()
    d = draw(p.im)
    # red vertical rule
    d.rectangle((sc(62), sc(190), sc(67), sc(690)), fill=rgba(RED, 230))
    rtl(p.im, (640, 150), kicker, F("bodyb", 21), rgba(AMBER, 235), anchor="rt")
    lines = title.split("\n")
    f = F("black", 112)
    for i, line in enumerate(lines):
        rtl(p.im, (650, 235 + i * 128), line, f, rgba(CREAM), anchor="rt",
            stroke=sc(1), stroke_fill=(0, 0, 0, 120))
    d.line((sc(150), sc(505), sc(650), sc(505)), fill=rgba(RED, 220), width=sc(3))
    textblock(p.im, (650, 535), sub, F("bodyb", 30), rgba(CREAM, 225), 500, line_h=1.45)
    stamp(p.im, 80, 555, stamp_txt, size=30, angle=-12)
    rtl(p.im, (650, 760), "1 NOV 2026 — AUSTIN / NORTH ELEUTHERA", F("num", 19),
        rgba(MUT, 210), anchor="rt", direction="ltr")
    return p.finish(vig=.55, grain=7, seed=11)

def b_chapter(p, *, num="01", title="بداية الرحلة", sub="", photo="chart.jpg",
              quote=""):
    p.photo(photo, darkness=.30, sepia=.12, contrast=1.1, blur=1.2)
    p.wash(BG, 185)
    d = draw(p.im)
    d.rectangle((0, 0, sc(W), sc(H)), outline=rgba(CREAM, 40), width=sc(14))
    rtl(p.im, (650, 210), "فصل", F("ruqaa", 34), rgba(AMBER, 230), anchor="rt")
    rtl(p.im, (110, 180), num, F("num", 150), rgba(RED, 190), anchor="lt", direction="ltr")
    d.line((sc(100), sc(370), sc(620), sc(370)), fill=rgba(CREAM, 110), width=sc(2))
    rtl(p.im, (650, 440), title, F("black", 82), rgba(CREAM), anchor="rt")
    if sub: textblock(p.im, (650, 570), sub, F("body", 27), rgba(MUT, 225), 520)
    if quote:
        textblock(p.im, (650, 720), quote, F("bodyb", 26), rgba(AMBER, 220), 500)
    stamp(p.im, 92, 780, "ملف مفتوح", size=24, angle=-9)
    return p.finish(vig=.45, grain=6, seed=22)

def b_clips(p, items, *, kicker="", title="", bg_photo=None, darkness=.42):
    if bg_photo:
        p.photo(bg_photo, darkness=.22, sepia=.08)
    p.wash(BG, 208 if bg_photo else 255)
    if kicker: rtl(p.im, (650, 130), kicker, F("bodyb", 20), rgba(AMBER, 220), anchor="rt")
    if title:
        textblock(p.im, (650, 168), title, F("black", 52), rgba(CREAM), 560, line_h=1.2)
    for it in items:
        c = make_clip(it["photo"], it.get("w", 250), it.get("h", 300),
                      it.get("caption", ""), it.get("seed", 1),
                      ht=it.get("ht", True), label=it.get("label", ""),
                      stamp_txt=it.get("stamp"))
        paste_sprite(p.im, c, it["x"], it["y"], it.get("rot", 0), shadow=14)
        if it.get("tape", True):
            tape(p.im, it["x"] + it.get("w", 250) * .35, it["y"] - 12, 90, 26,
                 angle=it.get("rot", 0) + 8)
        if it.get("pin"):
            pin(p.im, it["x"] + it.get("w", 250) * .5, it["y"] + 8)
    return p.finish(vig=.42, grain=6, seed=33)

def b_dossier(p, *, title="", fields=(), photo=None, num=None, note=""):
    p.im = Image.new("RGB", (BW, BH), BG2)
    d = draw(p.im)
    for i in range(0, BH, sc(28)):
        d.line((0, i, BW, i), fill=(255, 255, 255, 5), width=1)
    # big paper form
    form = card(sc(560), sc(590), 4, PAPER)
    paste_sprite(p.im, form, 80, 210, -1.5, shadow=18)
    rtl(p.im, (610, 250), "وثيقة / تقرير ميداني", F("bodyb", 22), rgba((110, 62, 44)), anchor="rt")
    if title:
        textblock(p.im, (610, 295), title, F("black", 44), rgba(INK), 470, line_h=1.25)
    d = draw(p.im)
    d.line((sc(120), sc(400), sc(600), sc(400)), fill=(90, 72, 52, 120), width=sc(2))
    yy = 420
    for k, v in fields:
        rtl(p.im, (600, yy), k, F("body", 20), rgba((120, 105, 80)), anchor="rt")
        rtl(p.im, (600, yy + 27), v, F("bodyb", 25), rgba(INK), anchor="rt")
        d.line((sc(120), sc(yy + 66), sc(600), sc(yy + 66)), fill=(90, 72, 52, 55), width=1)
        yy += 82
    if num:
        rtl(p.im, (110, 235), num, F("num", 92), rgba(RED, 205), anchor="lt", direction="ltr")
    if photo:
        c = photo_card(photo, 210, 250, 9)
        paste_sprite(p.im, c, 430, 620, 7, shadow=14)
        tape(p.im, 500, 610, 80, 24, 12)
    if note:
        textblock(p.im, (650, 850), note, F("body", 22), rgba(MUT), 540)
    stamp(p.im, 110, 740, "غير مكتمل", size=24, angle=8)
    return p.finish(vig=.5, grain=6, seed=44)

def b_radio(p, *, speaker="الطيار", text="", temp="-47°C", photo="radar.jpg",
            alert=False, index="01"):
    p.photo(photo, darkness=.32, sepia=0, cold=.25, contrast=1.2)
    p.wash(BG, 170)
    d = draw(p.im)
    d.rounded_rectangle((sc(48), sc(180), sc(672), sc(790)), radius=sc(18),
                        fill=(10, 14, 15, 205), outline=rgba(TEAL, 170), width=sc(2))
    # header strip
    d.rectangle((sc(48), sc(180), sc(672), sc(238)), fill=(18, 28, 27, 235))
    rtl(p.im, (645, 193), "التسجيل الصوتي / قمرة القيادة ⇄ البرج", F("bodyb", 19),
        rgba((150, 210, 190)), anchor="rt")
    rtl(p.im, (80, 193), "REC  ●", F("num", 17), rgba(RED2, 230), anchor="lt", direction="ltr")
    waveform_static(p.im, 80, 275, 560, 110, 56, seed=int(index) + 3,
                    color=(90, 190, 160, 150))
    tag(p.im, 80, 430, speaker, bg=RED if speaker == "الطيار" else TEAL, size=24)
    textblock(p.im, (645, 495), text, F("bodyb", 38), rgba(CREAM), 540, line_h=1.5)
    d.line((sc(80), sc(700), sc(640), sc(700)), fill=(140, 200, 180, 90), width=sc(1))
    rtl(p.im, (640, 720), "الحرارة الخارجية", F("body", 20), rgba(MUT, 220), anchor="rt")
    rtl(p.im, (95, 720), temp, F("num", 20), rgba(MUT, 220), anchor="lt", direction="ltr")
    if alert:
        stamp(p.im, 420, 800, "MAYDAY", size=38, angle=-8, color=RED)
    return p.finish(vig=.48, grain=7, seed=55)

def b_stat(p, *, value="35,000", unit="قدم", caption="", photo="cockpit_instruments.jpg",
           red=False, small="", kicker=""):
    p.photo(photo, darkness=.36, sepia=.08, contrast=1.2)
    p.wash(BG, 150)
    d = draw(p.im)
    d.rectangle((sc(60), sc(250), sc(660), sc(720)), outline=rgba(CREAM, 70), width=sc(2))
    if kicker: rtl(p.im, (630, 200), kicker, F("bodyb", 21), rgba(AMBER, 225), anchor="rt")
    rtl(p.im, (620, 320), value, F("num", 128), rgba(RED2 if red else CREAM),
        anchor="rt", direction="ltr")
    rtl(p.im, (620, 480), unit, F("black", 46), rgba(CREAM, 235), anchor="rt")
    d.line((sc(90), sc(570), sc(630), sc(570)), fill=rgba(RED if red else AMBER, 220), width=sc(3))
    textblock(p.im, (630, 600), caption, F("bodyb", 28), rgba(CREAM, 225), 540, line_h=1.4)
    if small: rtl(p.im, (630, 780), small, F("body", 19), rgba(MUT), anchor="rt", direction="rtl")
    return p.finish(vig=.5, grain=6, seed=66)

def b_question(p, *, text="", sub="", photo="plane_storm.jpg"):
    p.photo(photo, darkness=.28, sepia=.05)
    p.wash(BG, 200)
    d = draw(p.im)
    rtl(p.im, (650, 220), "؟", F("black", 270), rgba(RED, 52), anchor="rt")
    for x, y, sz in ((110, 180, 74), (150, 250, 58), (620, 700, 92)):
        rtl(p.im, (x, y), "؟", F("black", sz), rgba(RED, 40), anchor="rt")
    textblock(p.im, (650, 420), text, F("black", 64), rgba(CREAM), 560, line_h=1.3)
    if sub: textblock(p.im, (650, 700), sub, F("body", 26), rgba(MUT), 540)
    return p.finish(vig=.52, grain=7, seed=77)

def b_map(p, *, highlight="", photo="chart.jpg"):
    p.photo(photo, darkness=.72, sepia=.28, contrast=1.1)
    p.wash((18, 20, 18), 110)
    d = draw(p.im)
    # dotted route Austin -> Eleuthera -> Palm Beach
    pts = [(120, 700), (250, 620), (385, 565), (520, 505), (610, 430)]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        n = 16
        for j in range(n):
            if j % 2: continue
            f0, f1 = j / n, (j + .75) / n
            d.line((sc(a[0] + (b[0] - a[0]) * f0), sc(a[1] + (b[1] - a[1]) * f0),
                    sc(a[0] + (b[0] - a[0]) * f1), sc(a[1] + (b[1] - a[1]) * f1)),
                   fill=rgba(RED, 230), width=sc(4))
    for (x, y), lab, tx in zip([pts[0], pts[-1]],
                               ["أوستن، تكساس", "نورث إليوثيرا"], [330, 660]):
        d.ellipse((sc(x - 9), sc(y - 9), sc(x + 9), sc(y + 9)), fill=rgba(RED, 240),
                  outline=(255, 235, 215, 220), width=sc(2))
        rtl(p.im, (tx, y - 46), lab, F("bodyb", 21), rgba(INK), anchor="rt",
            stroke=2, stroke_fill=(232, 219, 190, 220))
    # Palm Beach marker
    d.ellipse((sc(445 - 13), sc(760 - 13), sc(445 + 13), sc(760 + 13)),
              outline=rgba(RED, 235), width=sc(4))
    d.line((sc(432), sc(747), sc(458), sc(773)), fill=rgba(RED, 235), width=sc(3))
    d.line((sc(458), sc(747), sc(432), sc(773)), fill=rgba(RED, 235), width=sc(3))
    rtl(p.im, (430, 790), "بالم بيتش، فلوريدا", F("bodyb", 20), rgba(RED, 235), anchor="rt")
    rtl(p.im, (650, 160), highlight, F("black", 46), rgba(INK), anchor="rt",
        stroke=2, stroke_fill=(232, 219, 190, 220))
    stamp(p.im, 80, 850, "مسار الرحلة", size=24, angle=-7)
    return p.finish(vig=.35, grain=6, seed=88)

def b_evidence(p, *, title="", items=(), note=""):
    p.im = Image.new("RGB", (BW, BH), BG)
    d = draw(p.im)
    for x in range(0, BW, sc(40)):
        d.line((x, 0, x, BH), fill=(255, 255, 255, 7), width=1)
    for y in range(0, BH, sc(40)):
        d.line((0, y, BW, y), fill=(255, 255, 255, 7), width=1)
    if title:
        rtl(p.im, (650, 150), title, F("black", 56), rgba(CREAM), anchor="rt")
        d.line((sc(90), sc(240), sc(630), sc(240)), fill=rgba(RED, 220), width=sc(3))
    for i, it in enumerate(items):
        x = 60 + (i % 2) * 310
        y = 300 + (i // 2) * 330
        c = card(sc(270), sc(250), 20 + i, PAPER)
        cd = ImageDraw.Draw(c, "RGBA")
        cd.text((sc(250), sc(24)), it["n"], font=F("num", 30), fill=rgba(RED, 220),
                direction="ltr", anchor="rt")
        cd.text((sc(250), sc(78)), it["t"], font=F("black", 34), fill=rgba(INK),
                direction="rtl", anchor="rt")
        for j, line in enumerate(wrap(it.get("d", ""), F("body", 17), 235)[:3]):
            cd.text((sc(250), sc(140) + j * sc(24)), line, font=F("body", 17),
                    fill=(70, 60, 46, 225), direction="rtl", anchor="rt")
        paste_sprite(p.im, c, x, y, it.get("rot", (-4, 3, -2)[i % 3]), shadow=14)
    if note:
        textblock(p.im, (650, 970), note, F("body", 23), rgba(MUT), 560)
    return p.finish(vig=.5, grain=6, seed=99)

def b_clock(p, *, time="12:50", caption="", photo="smoke_suburb.jpg"):
    p.photo(photo, darkness=.42, sepia=.22)
    p.wash(BG, 130)
    d = draw(p.im)
    d.rounded_rectangle((sc(90), sc(230), sc(630), sc(470)), radius=sc(12),
                        fill=(8, 9, 11, 210), outline=rgba(RED, 190), width=sc(3))
    rtl(p.im, (360, 275), time, F("num", 132), rgba(CREAM), anchor="mt", direction="ltr")
    rtl(p.im, (360, 415), "بالتوقيت المحلي", F("bodyb", 22), rgba(AMBER, 220), anchor="mt")
    textblock(p.im, (650, 540), caption, F("black", 52), rgba(CREAM), 560, line_h=1.3)
    return p.finish(vig=.5, grain=7, seed=111)

def b_note(p, *, text="", title="ملاحظة"):
    p.im = Image.new("RGB", (BW, BH), BG2)
    d = draw(p.im)
    c = card(sc(580), sc(360), 6, PAPER2)
    paste_sprite(p.im, c, 70, 340, -1, shadow=18)
    rtl(p.im, (610, 380), title, F("black", 42), rgba(RED), anchor="rt")
    d.line((sc(110), sc(450), sc(610), sc(450)), fill=(110, 90, 65, 120), width=sc(2))
    textblock(p.im, (610, 480), text, F("body", 24), rgba(INK), 480, line_h=1.6)
    stamp(p.im, 110, 650, "ترجمة", size=22, angle=9)
    return p.finish(vig=.55, grain=6, seed=123)

def b_signal(p, *, photo="recorder.jpg"):
    p.photo(photo, darkness=.45, sepia=.15)
    p.wash(BG, 175)
    d = draw(p.im)
    for i in range(0, BH, sc(7)):
        d.line((0, i, BW, i), fill=(255, 255, 255, 12 if i % 21 else 28), width=1)
    rtl(p.im, (360, 300), "انقطع الاتصال", F("black", 88), rgba(CREAM), anchor="mt")
    rtl(p.im, (360, 420), "SIGNAL LOST", F("num", 30), rgba(RED2, 230), anchor="mt",
        direction="ltr")
    waveform_static(p.im, 90, 540, 540, 90, 44, 12, color=(220, 80, 60, 150))
    return p.finish(vig=.6, grain=9, seed=222)

def b_end(p, *, title="الثواني الأخيرة", sub="", photo="plane_storm.jpg"):
    p.photo(photo, darkness=.30, sepia=.1)
    p.wash(BG, 205)
    d = draw(p.im)
    d.rectangle((sc(70), sc(300), sc(650), sc(760)), outline=rgba(CREAM, 90), width=sc(2))
    rtl(p.im, (360, 250), "وثائقي", F("ruqaa", 40), rgba(AMBER, 230), anchor="mt")
    rtl(p.im, (360, 390), title, F("black", 84), rgba(CREAM), anchor="mt")
    d.line((sc(180), sc(520), sc(540), sc(520)), fill=rgba(RED, 225), width=sc(3))
    textblock(p.im, (540, 560), sub, F("bodyb", 28), rgba(CREAM, 225), 470, line_h=1.5)
    rtl(p.im, (360, 830), "انتهت قبل الوصول", F("body", 24), rgba(MUT), anchor="mt")
    stamp(p.im, 470, 700, "ملف مغلق", size=24, angle=-10)
    return p.finish(vig=.6, grain=7, seed=333)

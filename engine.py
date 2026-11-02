#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Frame engine: camera drift, dynamic FX, transitions, karaoke captions, HUD."""
import json, math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import visuals as V

ROOT = Path(__file__).resolve().parent
W, H = V.W, V.H
FONTDIR = V.FONTDIR
T = json.loads((ROOT / "assets" / "timeline.json").read_text(encoding="utf-8"))
LINES = T["lines"]
INTRO, OUTRO = 2.4, 3.0
TOTAL = T["duration"] + INTRO + OUTRO
FPS = 25

_cf = {}
def CF(key, size):
    k = (key, size)
    if k not in _cf:
        _cf[k] = ImageFont.truetype(str(FONTDIR / V.FONTS[key]), size)
    return _cf[k]

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def smooth(v):
    v = clamp(v); return v * v * (3 - 2 * v)
def ease(v):
    v = clamp(v); return 1 - (1 - v) ** 3

# ------------------------------------------------------------------ word sprites
class Captions:
    STATES = ("dim", "said", "hot")
    COLORS = {"dim": (166, 158, 140, 150), "said": (245, 238, 220, 255),
              "hot": (255, 252, 244, 255)}

    def __init__(self):
        self.lines = []
        for L in LINES:
            if L["kind"] != "spoken" or not L["words"]:
                self.lines.append(None); continue
            words = L["words"]
            text = L["body"]
            # pick largest font keeping <=3 lines
            chosen = None
            for size in (34, 32, 30, 28, 26, 24, 22):
                f = CF("bodyb", size)
                adv = [int(V.text_len(w["w"], f)) + 9 for w in words]
                rows, cur, x = [], [], 0
                for i, a in enumerate(adv):
                    if cur and x + a > 604:
                        rows.append(cur); cur, x = [], 0
                    cur.append(i); x += a
                if cur: rows.append(cur)
                if len(rows) <= 3:
                    chosen = (f, size, adv, rows); break
            if chosen is None:
                f = CF("bodyb", 22); adv = [int(V.text_len(w["w"], f)) + 9 for w in words]
                chosen = (f, 22, adv, [list(range(len(words)))])
            f, size, adv, rows = chosen
            sprites = []
            for w in words:
                tw = int(V.text_len(w["w"], f))
                sw, sh = tw + 18, int(size * 1.30) + 12
                trio = {}
                for st in self.STATES:
                    sp = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
                    d = ImageDraw.Draw(sp, "RGBA")
                    if st == "hot":
                        d.rounded_rectangle((2, 1, sw - 2, sh - 3), radius=7,
                                            fill=(196, 52, 38, 238))
                    d.text((sw - 9, sh / 2 + 2), w["w"], font=f, fill=(0, 0, 0, 165),
                           direction="rtl", anchor="rm")
                    d.text((sw - 9, sh / 2), w["w"], font=f, fill=self.COLORS[st],
                           direction="rtl", anchor="rm")
                    trio[st] = sp
                sprites.append(trio)
            self.lines.append({"L": L, "f": f, "size": size, "adv": adv,
                               "rows": rows, "sprites": sprites,
                               "label": L.get("label")})

    def draw(self, frame, td):
        """td = design time (audio-relative)."""
        active = None
        for c in self.lines:
            if c and c["L"]["show_start"] <= td <= c["L"]["show_end"]:
                active = c; break
        if active is None:
            return frame
        L = active["L"]
        # panel
        d = ImageDraw.Draw(frame, "RGBA")
        a_in = smooth((td - L["show_start"]) / .22)
        a_out = smooth((L["show_end"] - td) / .28)
        alpha = int(212 * min(a_in, a_out))
        d.rounded_rectangle((28, 848, 692, 1058), radius=12,
                            fill=(9, 11, 14, alpha), outline=(232, 219, 190, int(alpha * .34)),
                            width=1)
        d.rectangle((684, 860, 688, 1046), fill=(199, 56, 42, min(255, alpha + 30)))
        # speaker label
        if active["label"]:
            lab = active["label"]
            lf = CF("bodyb", 19)
            lw = int(V.text_len(lab, lf)) + 22
            col = (199, 56, 42, 235) if lab == "الطيار" else (61, 91, 90, 235)
            d.rounded_rectangle((42, 858, 42 + lw, 894), radius=5, fill=col)
            d.text((42 + lw - 11, 866), lab, font=lf, fill=(250, 245, 232, 255),
                   direction="rtl", anchor="rt")
        # words
        y0 = 902 if len(active["rows"]) <= 2 else 884
        lh = 66 if len(active["rows"]) <= 2 else 58
        # exactly one highlighted word at any instant
        hot_i = -1
        for wi, w in enumerate(L["words"]):
            if w["s"] <= td:
                hot_i = wi
        for ri, row in enumerate(active["rows"]):
            x = 660.0
            y = y0 + ri * lh
            for wi in row:
                w = L["words"][wi]
                adv = active["adv"][wi]
                sp = active["sprites"][wi]
                if td < w["s"] - .02:
                    st = "dim"
                elif wi == hot_i and td <= w["e"] + .12:
                    st = "hot"
                else:
                    st = "said"
                rise = 0
                if st == "hot":
                    rise = int(9 * (1 - ease((td - w["s"]) / .16)))
                sw = sp[st].width
                px = int(x - sw + 10); py = int(y - 9 + rise)
                frame.paste(sp[st], (px, py), sp[st])
                if st == "hot" and w["e"] > w["s"]:
                    p = clamp((td - w["s"]) / (w["e"] - w["s"]))
                    d.rectangle((int(x - adv + 10), int(y + active["size"] * 1.16),
                                 int(x - adv + 10 + (adv - 12) * p),
                                 int(y + active["size"] * 1.16) + 3),
                                fill=(226, 172, 76, 235))
                x -= adv
        # line progress
        p = clamp((td - L["start"]) / max(.1, L["end"] - L["start"]))
        d.rectangle((40, 1050, 40 + 640 * p, 1052), fill=(199, 56, 42, 175))
        return frame

# ------------------------------------------------------------------ FX layers
class FX:
    def __init__(self):
        rng = np.random.default_rng(7)
        # rain: tall layer, scrolled
        rain = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rain, "RGBA")
        for _ in range(230):
            x = int(rng.integers(0, W)); y = int(rng.integers(0, H * 2))
            ln = int(rng.integers(18, 64)); al = int(rng.integers(18, 70))
            rd.line((x, y, x - 3, y + ln), fill=(205, 218, 225, al), width=1)
        self.rain = rain
        # scan band
        band = Image.new("RGBA", (W, 110), (0, 0, 0, 0))
        ba = np.zeros((110, W, 4), np.uint8)
        for y in range(110):
            k = math.exp(-((y - 55) / 26) ** 2)
            ba[y, :, 0] = 230; ba[y, :, 1] = 210; ba[y, :, 2] = 170
            ba[y, :, 3] = int(26 * k)
        self.band = Image.fromarray(ba, "RGBA")
        # light leak
        leak = np.zeros((H, W, 4), np.uint8)
        yy, xx = np.mgrid[0:H, 0:W]
        g = np.exp(-(((xx - W) / (W * .8)) ** 2 + ((yy - 0) / (H * .6)) ** 2))
        leak[..., 0] = 240; leak[..., 1] = 170; leak[..., 2] = 100
        leak[..., 3] = (g * 26).astype(np.uint8)
        self.leak = Image.fromarray(leak, "RGBA")
        # alarm red pulse
        al = np.zeros((H, W, 4), np.uint8)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * .42) / (H * .62)) ** 2)
        al[..., 0] = 220; al[..., 1] = 35; al[..., 2] = 25
        al[..., 3] = np.clip((r - .30) * 52, 0, 34).astype(np.uint8)
        self.alarm = Image.fromarray(al, "RGBA")
        # grain variants
        self.grains = []
        for i in range(5):
            n = np.random.default_rng(100 + i).normal(0, 10, (H, W)).astype(np.int16)
            g = np.zeros((H, W, 4), np.uint8)
            g[..., 0] = g[..., 1] = g[..., 2] = np.clip(128 + n, 0, 255).astype(np.uint8)
            g[..., 3] = 11
            self.grains.append(Image.fromarray(g, "RGBA"))
        # plane sprite (simple paper-plane marker) rotated
        base = Image.new("RGBA", (64, 48), (0, 0, 0, 0))
        dd = ImageDraw.Draw(base, "RGBA")
        dd.polygon([(60, 24), (4, 8), (20, 24), (4, 40)], fill=(238, 226, 198, 235))
        dd.line((20, 24, 60, 24), fill=(199, 56, 42, 235), width=2)
        self.plane = [base.rotate(a, Image.BICUBIC, expand=True) for a in range(0, 360, 10)]
        # paper strips
        self.strips = []
        for i in range(2):
            s = V.card(int(74), int(26), 300 + i, V.PAPER2)
            s.putalpha(s.getchannel("A").point(lambda v: int(v * .58)))
            self.strips.append([s.rotate(a, Image.BICUBIC, expand=True) for a in range(-25, 26, 5)])

    def apply(self, frame, name, lt, td, scene_i):
        d = ImageDraw.Draw(frame, "RGBA")
        # ---- always: drifting dust motes
        for i in range(30):
            ph = i * 0.618
            x = (W * ((0.13 * i + 0.037 * td * (1 + (i % 3) * .3)) % 1.0))
            y = (H * ((0.21 * i + 0.021 * td * (0.6 + (i % 5) * .16)) % 1.0))
            r = 1 + (i % 3) * .6
            a = 22 + int(22 * (0.5 + 0.5 * math.sin(td * 1.4 + ph * 9)))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 228, 198, a))
        # ---- scan line sweep (skill: خط المسح)
        sy = int((td * 190 + scene_i * 130) % (H + 220)) - 110
        frame.paste(self.band, (0, sy), self.band)
        # ---- subtle light leak
        if int(td * .7) % 3 == 0:
            frame.paste(self.leak, (0, 0), self.leak)

        if name in ("storm", "rain"):
            off = int((td * 420) % H)
            tile = self.rain.crop((0, off, W, off + H))
            frame.paste(tile, (0, 0), tile)
        if name == "storm":
            # lightning: brief cold flashes
            ph = (td % 5.7)
            if ph < .12:
                k = (1 - ph / .12) * 46
                d.rectangle((0, 0, W, H), fill=(210, 225, 245, int(k)))
        if name in ("storm", "dust", "smoke", "plane"):
            for i, strip in enumerate(self.strips):
                k = (td * (.12 + .04 * i) + i * .31) % 1.0
                y = int(120 + k * 700)
                x = int(90 + ((i * 213 + td * (14 + 6 * i)) % 540))
                idx = int((td * 9 + i * 3) % len(strip))
                frame.paste(strip[idx], (x, y), strip[idx])
        if name == "plane":
            # plane glides along the route
            k = (td * .085) % 1.0
            x = int(110 + k * 500); y = int(690 - k * 260)
            ang = int((math.degrees(math.atan2(-260, 500)) + 360) % 360) // 10
            sp = self.plane[ang % len(self.plane)]
            frame.paste(sp, (x, y), sp)
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(199, 56, 42, 190))
        if name == "radiofx":
            # live waveform bottom of the console
            for i in range(48):
                v = abs(math.sin(td * 7.5 + i * .55) * math.sin(td * 2.1 + i * .13))
                bh = 6 + 44 * v
                xx = 80 + i * 11.7
                d.rounded_rectangle((xx, 742 - bh / 2, xx + 5, 742 + bh / 2), radius=2,
                                    fill=(96, 200, 168, 125))
            if int(td * 1.6) % 2 == 0:
                d.ellipse((96, 200, 108, 212), fill=(231, 88, 62, 230))
        if name == "alarm":
            pulse = .45 + .55 * (0.5 + 0.5 * math.sin(td * 8.0))
            ov = self.alarm.copy()
            ov.putalpha(self.alarm.getchannel("A").point(lambda v: int(v * pulse)))
            frame.paste(ov, (0, 0), ov)
            if int(td * 2.3) % 2 == 0:
                d.rounded_rectangle((44, 660, 240, 706), radius=5, fill=(199, 56, 42, 220))
                d.text((230, 669), "نداء استغاثة", font=CF("bodyb", 21),
                       fill=(255, 245, 236, 255), direction="rtl", anchor="rt")
        if name == "static":
            # horizontal glitch slices + noise bursts
            r = random.Random(int(td * 12))
            for _ in range(9):
                y = r.randint(0, H - 12); hh = r.randint(4, 22)
                dx = r.randint(-30, 30)
                band = frame.crop((0, y, W, y + hh))
                frame.paste(band, (dx, y))
            if int(td * 8) % 3 == 0:
                d.rectangle((0, 0, W, H), fill=(190, 200, 210, 16))
        if name == "smoke":
            for i in range(22):
                ph = i * .77
                x = (W * (.2 + .6 * ((math.sin(ph) + 1) / 2)) +
                     18 * math.sin(td * .7 + ph * 4))
                y = (H * ((1 - (td * .05 + ph * .13) % 1.0)))
                rr = 2 + (i % 4)
                d.ellipse((x - rr, y - rr, x + rr, y + rr),
                          fill=(214, 186, 140, 36))
        # ---- animated film grain (very light, cheap bitrate)
        frame.paste(self.grains[int(td * 12) % 5], (0, 0),
                    self.grains[int(td * 12) % 5])
        return frame

# ------------------------------------------------------------------ HUD + cards
def hud(frame, t_abs, td, chapter_name):
    d = ImageDraw.Draw(frame, "RGBA")
    # top progress rail
    d.rectangle((34, 44, 686, 46), fill=(232, 219, 190, 45))
    d.rectangle((34, 44, 34 + 652 * clamp(t_abs / TOTAL), 46), fill=(199, 56, 42, 215))
    mins, secs = divmod(int(t_abs), 60)
    d.text((40, 58), f"{mins:02d}:{secs:02d}", font=CF("num", 16),
           fill=(232, 219, 190, 150), direction="ltr", anchor="lt")
    d.text((682, 58), "ARCHIVE · FILE 01", font=CF("num", 14),
           fill=(232, 219, 190, 130), direction="ltr", anchor="rt")
    if chapter_name:
        d.rounded_rectangle((34, 92, 34 + 190, 124), radius=4, fill=(16, 18, 20, 190))
        d.text((216, 99), chapter_name, font=CF("bodyb", 16),
               fill=(226, 172, 76, 225), direction="rtl", anchor="rt")

def interstitials(frame, td):
    """Show the four connective sentences + chapter chip as typed strips."""
    d = ImageDraw.Draw(frame, "RGBA")
    for L in LINES:
        if L["kind"] == "connective" and L["card_start"] <= td <= L["card_end"]:
            k = ease((td - L["card_start"]) / .42)
            txt = L["line"]
            f = CF("bodyb", 25)
            tw = int(V.text_len(txt, f)) + 40
            d.rounded_rectangle((int(360 - tw / 2), 762, int(360 + tw / 2), 820),
                                radius=6, fill=(12, 14, 16, 205),
                                outline=(226, 172, 76, 130), width=1)
            shown = txt[:max(1, int(len(txt) * k))]
            d.text((360, 774), shown, font=f, fill=(244, 237, 219, 245),
                   direction="rtl", anchor="mt")
        if L["kind"] == "chapter" and L["card_start"] <= td <= L["card_end"]:
            k = clamp((td - L["card_start"]) / .3)
            d.rounded_rectangle((34, 130, 34 + 220, 166), radius=4,
                                fill=(199, 56, 42, int(225 * k)))
            d.text((246, 137), "فصل · " + L["chapter"], font=CF("bodyb", 17),
                   fill=(255, 246, 236, int(250 * k)), direction="rtl", anchor="rt")
    return frame

# ------------------------------------------------------------------ transitions
def transition(A, B, k, typ):
    k = clamp(k)
    if typ == "fade" or typ == "dip":
        if typ == "dip":
            m = max(0.0, 1 - abs(k - .5) * 2)
            A = Image.blend(A, Image.new("RGB", (W, H), (5, 6, 8)), m * .8)
            B = Image.blend(B, Image.new("RGB", (W, H), (5, 6, 8)), m * .8)
        return Image.blend(A, B, smooth(k))
    if typ == "wipe":
        mask = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mask)
        x = int(W * (1 - ease(k)))
        d.polygon([(x, 0), (W, 0), (W, H), (x, H)], fill=255)
        # torn leading edge
        for y in range(0, H, 9):
            j = int(9 * math.sin(y * .13 + k * 8))
            d.line((x + j, y, x + j + 12, y + 4), fill=255, width=9)
        out = Image.composite(B, A, mask)
        ImageDraw.Draw(out, "RGBA").line((x, 0, x, H), fill=(199, 56, 42, 190), width=3)
        return out
    if typ == "scan":
        mask = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mask)
        yy = int(H * ease(k))
        d.rectangle((0, 0, W, yy), fill=255)
        out = Image.composite(B, A, mask)
        dd = ImageDraw.Draw(out, "RGBA")
        dd.rectangle((0, yy - 3, W, yy + 3), fill=(226, 172, 76, 160))
        dd.rectangle((0, yy - 14, W, yy - 4), fill=(226, 172, 76, 45))
        return out
    if typ == "push":
        out = Image.new("RGB", (W, H), (5, 6, 8))
        dx = int(W * ease(k))
        out.paste(A, (-dx, 0))
        out.paste(B, (W - dx, 0))
        ImageDraw.Draw(out, "RGBA").line((W - dx, 0, W - dx, H),
                                         fill=(226, 172, 76, 170), width=3)
        return out
    if typ == "iris":
        mask = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mask)
        r = int(math.hypot(W, H) * ease(k) / 2)
        d.ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=255)
        return Image.composite(B, A, mask.filter(ImageFilter.GaussianBlur(2)))
    if typ == "flash":
        if k < .5:
            m = smooth(k * 2)
            return Image.blend(A, Image.new("RGB", (W, H), (245, 238, 220)), m * .92)
        m = smooth((k - .5) * 2)
        return Image.blend(Image.new("RGB", (W, H), (245, 238, 220)), B, m)
    if typ == "glitch":
        out = Image.blend(A, B, smooth(k))
        rng = random.Random(int(k * 1000))
        for _ in range(12):
            y = rng.randint(0, H - 18); hh = rng.randint(6, 30)
            band = B.crop((0, y, W, y + hh))
            out.paste(band, (rng.randint(-30, 30), y))
        return out
    return Image.blend(A, B, smooth(k))

# ------------------------------------------------------------------ frame render
def camera(plate, lt, seed):
    """Slow drift + gentle zoom from an oversized plate."""
    z = 1.0 + .035 * (0.5 + 0.5 * math.sin(lt * .23 + seed))
    cw, ch = int(W / z), int(H / z)
    cx = (plate.width - cw) / 2 + 26 * math.sin(lt * .17 + seed * .7)
    cy = (plate.height - ch) / 2 + 34 * math.sin(lt * .13 + seed * 1.3)
    cx = clamp(cx, 0, plate.width - cw); cy = clamp(cy, 0, plate.height - ch)
    crop = plate.crop((int(cx), int(cy), int(cx) + cw, int(cy) + ch))
    return crop.resize((W, H), Image.LANCZOS) if (cw, ch) != (W, H) else crop

def plate_at(scene, td):
    ps = scene["plates"]
    cur = ps[0]
    for p in ps[1:]:
        if td >= p["at"]: cur = p
        else: break
    nxt = next((p for p in ps if p["at"] > cur["at"]), None)
    im = cur["im"]
    if nxt and td >= cur["at"]:
        k = smooth((td - nxt["at"] + .62) / .62)
        if k > 0:
            im = Image.blend(cur["im"], nxt["im"], k)
    return im

def scene_frame(scene, td, scene_i, fx, anim_t):
    im = plate_at(scene, td)
    lt = max(0.0, td - scene["start"])
    frame = camera(im, lt, scene_i * 1.7)
    frame = fx.apply(frame, scene["fx"], lt, anim_t, scene_i)
    return frame

TR = {"flash": .52, "wipe": .60, "scan": .62, "fade": .58, "dip": .68,
      "glitch": .46, "iris": .62, "push": .58}

def render_frame(t_abs, scenes, caps, fx):
    td = t_abs - INTRO
    if td < 0:
        td = 0.0
    elif td > T["duration"]:
        td = T["duration"] - .001
    # locate current scene
    i = 0
    for j, s in enumerate(scenes):
        if s["start"] <= td < s["end"]:
            i = j; break
        if td >= s["end"]: i = j
    s = scenes[i]
    cur = scene_frame(s, td, i, fx, t_abs)
    base = cur
    # full symmetric transition centred on each scene boundary
    tr_prev = TR.get(s["tr"], .55) if i > 0 else 0
    if i > 0 and td < s["start"] + tr_prev / 2:
        t0 = s["start"] - tr_prev / 2
        prev = scene_frame(scenes[i - 1], td, i - 1, fx, t_abs)
        base = transition(prev, cur, (td - t0) / tr_prev, s["tr"])
    elif i + 1 < len(scenes):
        nx = scenes[i + 1]
        tr = TR.get(nx["tr"], .55)
        t0 = nx["start"] - tr / 2
        if td >= t0:
            other = scene_frame(nx, td, i + 1, fx, t_abs)
            base = transition(cur, other, (td - t0) / tr, nx["tr"])
    # non-spoken text cards
    base = interstitials(base, td)
    # captions (only while narration is actually running)
    if INTRO <= t_abs <= INTRO + T["duration"] + .25:
        base = caps.draw(base, td)
    # chapter name chip
    cname = None
    for L in LINES:
        if L["kind"] == "chapter" and L["card_start"] <= td <= L["card_end"] + 1.5:
            cname = L["chapter"]
    hud(base, t_abs, td, cname)
    # outro fade
    if t_abs > TOTAL - 1.5:
        k = (TOTAL - t_abs) / 1.5
        base = Image.blend(Image.new("RGB", (W, H), (4, 5, 7)), base, clamp(k))
    return base

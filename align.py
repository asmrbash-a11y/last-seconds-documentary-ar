#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Align the spoken words of the canonical script to Whisper word timings.

The narration omits: chapter headings, the translator's note, speaker labels and
four connective sentences. Those become designed visual cards, not captions.
"""
import json, re, unicodedata, difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / "assets" / "transcript.json").read_text(encoding="utf-8"))
SCRIPT = D["script"]

# 1-based line numbers that are NOT spoken
CHAPTERS = {5: "بداية الرحلة", 12: "بداية الكارثة",
            16: "التسجيل الصوتي", 33: "لحظة الاصطدام", 46: "الخاتمة"}
NONSPOKEN = set(CHAPTERS) | {17, 21, 26, 30, 32}
SPEAKER_RE = re.compile(r"^(الطيار|برج المراقبة):\s*")

TASHKEEL = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u0640]")
def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = TASHKEEL.sub("", s)
    s = re.sub(r"[أإآٱ]", "ا", s)
    s = re.sub(r"[ىي]", "ي", s)
    s = s.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "").replace("ة", "ه")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()

# ---- build canonical spoken words -------------------------------------------
canon = []          # {li, w, n}
meta = []           # per line: label, kind, words
for li, line in enumerate(SCRIPT):
    n = li + 1
    m = SPEAKER_RE.match(line)
    label = m.group(1) if m else None
    body = SPEAKER_RE.sub("", line).strip()
    kind = ("chapter" if n in CHAPTERS else
            "note" if n == 17 else
            "connective" if n in (21, 26, 30, 32) else "spoken")
    ws = []
    if kind == "spoken":
        for w in body.split():
            ws.append({"w": w, "n": norm(w)})
            canon.append({"li": li, "w": w, "n": norm(w)})
    meta.append({"i": li, "line": line, "body": body, "label": label,
                 "kind": kind, "chapter": CHAPTERS.get(n), "words": ws})

whisp = [{"w": x["w"], "s": x["s"], "e": x["e"], "n": norm(x["w"])} for x in D["words"]]
A = [c["n"] for c in canon]
B = [w["n"] for w in whisp]
sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
pairs = {}
for a, b, k in sm.get_matching_blocks():
    for j in range(k):
        pairs[a + j] = b + j
print(f"spoken canonical words={len(A)}  whisper={len(B)}  matched={len(pairs)} "
      f"({100*len(pairs)/len(A):.1f}%)")

def lerp_time(i):
    if i in pairs:
        w = whisp[pairs[i]]
        return w["s"], w["e"]
    lo = max((j for j in pairs if j < i), default=None)
    hi = min((j for j in pairs if j > i), default=None)
    if lo is not None and hi is not None:
        s0, e0 = whisp[pairs[lo]]["s"], whisp[pairs[lo]]["e"]
        s1 = whisp[pairs[hi]]["s"]
        gap = max(0.05, s1 - e0)
        f = (i - lo) / (hi - lo)
        s = e0 + gap * f
        return s, s + gap / (hi - lo) * 0.9
    if lo is not None:
        e0 = whisp[pairs[lo]]["e"]
        return e0 + 0.08, e0 + 0.36
    if hi is not None:
        s1 = whisp[pairs[hi]]["s"]
        return max(0, s1 - 0.36), max(0.05, s1 - 0.08)
    return 0.0, 0.3

for i, c in enumerate(canon):
    c["s"], c["e"] = lerp_time(i)
for i in range(1, len(canon)):
    if canon[i]["s"] < canon[i-1]["e"] + 0.005:
        canon[i]["s"] = canon[i-1]["e"] + 0.005
    if canon[i]["e"] <= canon[i]["s"] + 0.04:
        canon[i]["e"] = canon[i]["s"] + 0.12
# attach times back to lines
ci = 0
for m in meta:
    if m["kind"] != "spoken":
        continue
    for w in m["words"]:
        w["s"], w["e"] = round(canon[ci]["s"], 3), round(canon[ci]["e"], 3)
        ci += 1

# ---- line display windows ----------------------------------------------------
lines = []
for m in meta:
    ws = m["words"]
    if ws:
        s, e = ws[0]["s"], ws[-1]["e"]
    else:
        s = e = None
    lines.append({**{k: m[k] for k in ("i", "line", "body", "label", "kind", "chapter")},
                  "start": s, "end": e, "words": ws})

# non-spoken cards live in the quiet margin just before the next spoken line
for i, L in enumerate(lines):
    if L["kind"] == "spoken":
        continue
    nxt = next((x for x in lines[i+1:] if x["kind"] == "spoken" and x["start"]), None)
    prv = next((x for x in reversed(lines[:i]) if x["kind"] == "spoken" and x["end"]), None)
    if nxt:
        anchor = nxt["start"]
        dur = 2.0 if L["kind"] == "chapter" else 1.3
        L["card_start"] = round(max(prv["end"] if prv else 0, anchor - dur), 3)
        L["card_end"] = round(anchor + (1.2 if L["kind"] == "chapter" else 0.5), 3)
        L["start"], L["end"] = L["card_start"], L["card_end"]
    else:
        L["card_start"] = L["card_end"] = L["start"] = L["end"] = (prv["end"] if prv else 0)

# caption show windows: never overlap the next caption, keep >=0.55 s on screen
spoken = [L for L in lines if L["kind"] == "spoken"]
for j, L in enumerate(spoken):
    nxt_s = spoken[j+1]["start"] if j+1 < len(spoken) else D["duration"]
    L["show_start"] = round(max(0, L["start"] - 0.14), 3)
    L["show_end"] = round(min(nxt_s - 0.04, max(L["end"] + 0.42, L["start"] + 0.7)), 3)
    if L["show_end"] <= L["show_start"]:
        L["show_end"] = L["show_start"] + 0.6

print("\n #  KIND        START    END   WORDS  TEXT")
for L in lines:
    print(f"{L['i']+1:2d}  {L['kind']:<10} {L['start']:7.2f} {L['end']:7.2f} "
          f"{len(L['words']):5d}  {L['line'][:52]}")

out = {"duration": D["duration"], "lines": lines,
       "matched": len(pairs), "spoken_words": len(A)}
(ROOT / "assets" / "timeline.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nWROTE timeline.json")

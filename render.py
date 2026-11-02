#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the vertical motion-graphics documentary.

  python3 render.py preview             -> contact sheet of key frames
  python3 render.py sample --start 0 --end 30 --crf 24   -> size/quality test
  python3 render.py full --crf 24       -> final silent video
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
import imageio_ffmpeg
from PIL import Image, ImageDraw
import scenes, engine

ROOT = Path(__file__).resolve().parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = engine.W, engine.H, engine.FPS

def build_all():
    print("building plates ...", flush=True)
    sc = scenes.build()
    print("building caption sprites ...", flush=True)
    caps = engine.Captions()
    print("building FX layers ...", flush=True)
    fx = engine.FX()
    return sc, caps, fx

def contact_sheet(sc, caps, fx, times, out):
    tw, th = 240, 427
    cols = 4; rows = (len(times) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), (15, 16, 18))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        f = engine.render_frame(t, sc, caps, fx)
        f = f.resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 24)
        sheet.paste(f, (x, y))
        d.text((x + 6, y + th + 4), f"{t:.1f}s", fill=(235, 228, 210))
    sheet.save(out, quality=91)
    print("contact sheet:", out)

def ffmpeg_cmd(out, crf, maxrate, seconds=None):
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "pipe:0", "-an",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
           "-maxrate", maxrate, "-bufsize", "1000k",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
           "-g", "50", "-movflags", "+faststart", "-r", str(FPS)]
    if seconds: cmd += ["-t", f"{seconds:.3f}"]
    cmd += [out]
    return cmd

def encode(sc, caps, fx, out, t0, t1, crf, maxrate):
    n = int((t1 - t0) * FPS)
    cmd = ffmpeg_cmd(out, crf, maxrate, (t1 - t0))
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    start = time.time()
    try:
        for i in range(n):
            t = t0 + i / FPS
            frame = engine.render_frame(t, sc, caps, fx)
            p.stdin.write(frame.tobytes())
            if i % 250 == 0:
                el = time.time() - start
                print(f"  frame {i:5d}/{n}  {i/max(1,el):.1f} fps  "
                      f"elapsed {el:.0f}s", flush=True)
        p.stdin.close()
    except BrokenPipeError:
        pass
    err = p.stderr.read().decode("utf-8", "replace")
    rc = p.wait()
    print("ffmpeg rc", rc, err[-600:] if rc else "")
    if rc: raise RuntimeError("ffmpeg failed")
    el = time.time() - start
    sz = os.path.getsize(out) / 1024 / 1024
    print(f"DONE {out}  {n} frames  {el:.0f}s  {sz:.2f} MB video "
          f"({sz*8/(t1-t0):.0f} kbps)", flush=True)
    return sz

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["preview", "sample", "full"])
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=30)
    ap.add_argument("--crf", type=int, default=24)
    ap.add_argument("--maxrate", default="440k")
    ap.add_argument("--out", default=str(ROOT / "renders" / "video.mp4"))
    a = ap.parse_args()
    (ROOT / "renders").mkdir(exist_ok=True)
    sc, caps, fx = build_all()
    if a.mode == "preview":
        times = [1.2, 6, 16, 30, 46, 55, 70, 88, 100, 120, 135, 150,
                 163, 168, 190, 205, 215, 240, 258, 275, 288, 293]
        contact_sheet(sc, caps, fx, times, str(ROOT / "assets" / "frames_sheet.jpg"))
        # also single full-size frames
        for t in (1.2, 30, 70, 135, 168, 293):
            engine.render_frame(t, sc, caps, fx).save(
                str(ROOT / "assets" / f"frame_{int(t):03d}.jpg"), quality=92)
    elif a.mode == "sample":
        encode(sc, caps, fx, a.out, a.start, a.end, a.crf, a.maxrate)
    else:
        encode(sc, caps, fx, a.out, 0, engine.TOTAL, a.crf, a.maxrate)

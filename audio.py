#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Narration + archival SFX (no music bed) -> padded, normalised soundtrack."""
import json, subprocess, wave
from pathlib import Path
import numpy as np
import imageio_ffmpeg
import scenes

ROOT = Path(__file__).resolve().parent
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
INTRO, OUTRO = 2.4, 3.0
T = json.loads((ROOT / "assets" / "timeline.json").read_text(encoding="utf-8"))
DUR = T["duration"] + INTRO + OUTRO

def read_mp3(path):
    p = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-i", str(path),
                        "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()

def env(n, a=0.02, d=0.5, attack=0.01):
    e = np.ones(n, np.float32)
    ai = max(1, int(SR * attack)); di = max(1, int(SR * d))
    e[:ai] = np.linspace(0, 1, ai)
    if di < n:
        e[n - di:] *= np.exp(-np.linspace(0, 5, di))
    return e

def lp(x, cutoff=900):
    # one-pole low pass
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = a * acc + (1 - a) * v; y[i] = acc
    return y

def noise(n, seed=1, cutoff=1200):
    rng = np.random.default_rng(seed)
    return lp(rng.normal(0, 1, n).astype(np.float32), cutoff)

def whoosh(dur=0.9, seed=1, cutoff=700):
    n = int(SR * dur)
    x = noise(n, seed, cutoff)
    return x / (np.max(np.abs(x)) + 1e-6) * env(n, d=dur * .8)

def paper(dur=0.45, seed=2):
    n = int(SR * dur)
    x = noise(n, seed, 4200) * (0.4 + 0.6 * np.sin(np.linspace(0, 22, n)) ** 2)
    return x / (np.max(np.abs(x)) + 1e-6) * env(n, d=dur * .9)

def static(dur=1.1, seed=3):
    n = int(SR * dur)
    x = noise(n, seed, 6500)
    x *= (0.35 + 0.65 * (np.sin(np.linspace(0, 70, n)) > 0))
    return x / (np.max(np.abs(x)) + 1e-6) * env(n, d=dur * .7)

def beep(freq=880, dur=.18, seed=0):
    n = int(SR * dur); t = np.linspace(0, dur, n, dtype=np.float32)
    x = np.sin(2 * np.pi * freq * t) * .7 + np.sin(2 * np.pi * freq * 2 * t) * .2
    return x * env(n, d=dur * .8)

def boom(dur=2.2, seed=4):
    n = int(SR * dur); t = np.linspace(0, dur, n, dtype=np.float32)
    f = 95 * np.exp(-t * 2.1) + 32
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * .8
    x += noise(n, seed, 380) * np.exp(-t * 3.2) * .7
    return x * env(n, d=dur * .7) * .9

def tapestop(dur=.9):
    n = int(SR * dur); t = np.linspace(0, dur, n, dtype=np.float32)
    f = 430 * np.exp(-t * 3.4) + 55
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * .6
    return x * env(n, d=dur * .8)

def drone(dur=2.6):
    n = int(SR * dur); t = np.linspace(0, dur, n, dtype=np.float32)
    x = (np.sin(2 * np.pi * 55 * t) * .5 + np.sin(2 * np.pi * 82.5 * t) * .25)
    return x * env(n, d=dur * .75) * .5

def add(buf, sig, at, gain):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < 0 or j <= i: return
    buf[i:j] += sig[:j - i] * gain

def main():
    vo = read_mp3(ROOT / "assets" / "narration.mp3")
    vo /= (np.max(np.abs(vo)) + 1e-6)
    vo *= .86
    n = int(DUR * SR)
    mix = np.zeros(n, np.float32)
    add(mix, vo, INTRO, 1.0)
    # cinematic opening
    add(mix, whoosh(1.7, 11, 420), .25, .16)
    add(mix, paper(.5, 12), 1.35, .075)
    add(mix, whoosh(1.2, 13, 300), 1.7, .08)
    # soft transition whooshes at every scene boundary
    for i, s in enumerate(scenes.build()):
        if i == 0: continue
        add(mix, whoosh(.75, 30 + i, 800 + i * 40), INTRO + s["start"] - .25, .055)
    # radio / ATC
    add(mix, static(1.3, 41), INTRO + 118.8, .075)
    add(mix, static(.9, 42), INTRO + 126.1, .05)
    add(mix, static(.8, 43), INTRO + 132.2, .065)
    # emergency beeps
    for k in range(4):
        add(mix, beep(920, .16), INTRO + 133.0 + k * 1.15, .075)
    for k in range(3):
        add(mix, beep(760, .14), INTRO + 149.0 + k * .9, .06)
    # tape stop + impact
    add(mix, tapestop(.85), INTRO + 163.4, .11)
    add(mix, static(.7, 44), INTRO + 164.4, .085)
    add(mix, boom(2.4, 45), INTRO + 167.15, .25)
    add(mix, paper(.7, 46), INTRO + 178.0, .045)
    # closing
    add(mix, drone(2.8), INTRO + T["duration"] - .1, .085)
    # gentle limiter
    mix = np.tanh(mix * 1.12) * .94
    # tiny fade in/out
    fi, fo = int(SR * .12), int(SR * .35)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo)
    wav = ROOT / "assets" / "soundtrack.wav"
    with wave.open(str(wav), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    m4a = ROOT / "assets" / "soundtrack.m4a"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav),
                    "-c:a", "aac", "-b:a", "96k", "-ac", "1", "-ar", "44100",
                    "-movflags", "+faststart", str(m4a)], check=True)
    print(f"soundtrack: {DUR:.2f}s  wav={wav.stat().st_size/1024/1024:.2f}MB  "
          f"m4a={m4a.stat().st_size/1024/1024:.2f}MB")

if __name__ == "__main__":
    main()

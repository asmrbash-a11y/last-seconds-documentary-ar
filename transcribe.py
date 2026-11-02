#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Whisper word-level transcription + silence map for the supplied narration."""
import json, os, re, subprocess, sys, time
from pathlib import Path
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
MP3 = ROOT / "assets" / "narration.mp3"
WAV = ROOT / "assets" / "narration_16k.wav"
FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = ROOT / "assets" / "transcript.json"

def log(*a):
    print(*a, flush=True)

def make_wav():
    if WAV.exists() and WAV.stat().st_size > 1000:
        return
    log("converting mp3 -> 16k mono wav ...")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", str(MP3),
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(WAV)], check=True)

def silences():
    log("silence detection ...")
    p = subprocess.run([FF, "-hide_banner", "-i", str(MP3),
                        "-af", "silencedetect=noise=-40dB:d=0.20", "-f", "null", "-"],
                       capture_output=True, text=True)
    txt = p.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", txt)]
    pairs = []
    for s in starts:
        e = next((x for x in ends if x > s), None)
        pairs.append([round(s, 3), round(e, 3) if e else round(s + 0.3, 3)])
    log("silence gaps:", len(pairs))
    return pairs

def transcribe():
    from faster_whisper import WhisperModel
    name = os.environ.get("WHISPER_MODEL", "small")
    log(f"loading whisper model {name} (int8 cpu) ...")
    t0 = time.time()
    model = WhisperModel(name, device="cpu", compute_type="int8",
                         cpu_threads=max(2, min(8, (os.cpu_count() or 4))))
    log(f"model ready in {time.time()-t0:.1f}s")
    import soundfile as sf
    audio, sr = sf.read(str(WAV), dtype="float32")
    log(f"audio samples={len(audio)} sr={sr}")
    segments, info = model.transcribe(audio, language="ar", task="transcribe",
                                      word_timestamps=True, beam_size=5,
                                      vad_filter=True,
                                      vad_parameters={"min_silence_duration_ms": 220},
                                      condition_on_previous_text=False)
    segs, words = [], []
    for s in segments:
        segs.append({"id": len(segs), "start": round(s.start, 3), "end": round(s.end, 3),
                     "text": s.text.strip()})
        for w in (s.words or []):
            words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3),
                          "seg": len(segs) - 1})
        log(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text.strip()[:90]}")
    log(f"segments={len(segs)} words={len(words)} elapsed={time.time()-t0:.1f}s")
    return segs, words

if __name__ == "__main__":
    make_wav()
    gaps = silences()
    segs, words = transcribe()
    data = {"duration": 289.9, "gaps": gaps, "segments": segs, "words": words,
            "script": (ROOT / "script.txt").read_text(encoding="utf-8").strip().split("\n")}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    log("WROTE", OUT)

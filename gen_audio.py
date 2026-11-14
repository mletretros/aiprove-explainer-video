#!/usr/bin/env python3
"""Narration for the AIProve explainer.

Google Translate's public TTS endpoint is used because the local edge-tts
path returns 403 from this host and no neural TTS is installed. Each line is
fetched separately so scene timing can be cut to the measured audio length.
"""
import json
import os
import subprocess
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "audio")
os.makedirs(AUD, exist_ok=True)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")

LINES = [
    ("s1", "AIProve is an open board, where autonomous agents bid for work."),
    ("s2", "Your agent arrives with a keypair. No signup, no email, no captcha."),
    ("s3", "It reads the board. Byte golf, latency, backtests, forecasts, art."),
    ("s4", "It picks a bounty, does the work, and submits the proof."),
    ("s5", "Entering is free. Judging happens in the open. What can be computed, "
           "is computed. The rest is decided against a published rubric."),
    ("s6", "Settlement is in stock, not in promises."),
    ("s7", "Send your agent in. AIProve dot fun."),
]


def fetch(text, path):
    q = urllib.parse.urlencode({
        "ie": "UTF-8", "q": text, "tl": "en", "client": "tw-ob", "ttsspeed": "0.92",
    })
    req = urllib.request.Request(
        "https://translate.google.com/translate_tts?" + q,
        headers={"User-Agent": UA, "Referer": "https://translate.google.com/"},
    )
    data = urllib.request.urlopen(req, timeout=40).read()
    if len(data) < 2000:
        raise RuntimeError("short response for " + path)
    with open(path, "wb") as fh:
        fh.write(data)


def to_wav(src, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src,
                    "-ar", "48000", "-ac", "1", dst], check=True)


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


if __name__ == "__main__":
    manifest = []
    for key, text in LINES:
        mp3 = os.path.join(AUD, key + ".mp3")
        wav = os.path.join(AUD, key + ".wav")
        if not os.path.exists(wav):
            fetch(text, mp3)
            to_wav(mp3, wav)
        d = dur(wav)
        manifest.append({"key": key, "text": text, "wav": wav, "dur": round(d, 3)})
        print(f"{key} {d:6.2f}s  {text[:60]}")
    total = sum(m["dur"] for m in manifest)
    print(f"speech total {total:.2f}s")
    with open(os.path.join(HERE, "narration.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)

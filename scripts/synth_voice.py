#!/usr/bin/env python3
"""
synth_voice.py
Genererer norsk voiceover med edge-tts fra narration-linjene.
Lager en samlet voice.mp3 + timings.json (lengde per linje for tekst-sync).
"""
import os, json, sys, asyncio
import edge_tts
from mutagen.mp3 import MP3

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "config.json")))
VOICE = CFG["voice"]["voice_id"]
RATE = CFG["voice"]["rate"]


async def synth_line(text, path):
    com = edge_tts.Communicate(text, VOICE, rate=RATE)
    await com.save(path)


async def main(job_id):
    outdir = f"build/{job_id}"
    script = json.load(open(f"{outdir}/script.json"))
    lines = [script["hook"]] + script["narration"]
    parts, timings = [], []
    for i, line in enumerate(lines):
        p = os.path.join(outdir, f"line_{i:02d}.mp3")
        await synth_line(line, p)
        dur = MP3(p).info.length
        timings.append({"text": line, "start": sum(t["dur"] for t in timings), "dur": dur})
        parts.append(p)
    # konkatener med ffmpeg concat
    listfile = os.path.join(outdir, "voice_list.txt")
    with open(listfile, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.basename(p)}'\n")
    os.system(f"cd {outdir} && ffmpeg -y -f concat -safe 0 -i voice_list.txt -c copy voice.mp3 -loglevel error")
    json.dump(timings, open(f"{outdir}/timings.json", "w"), ensure_ascii=False, indent=2)
    print(f"Voiceover: {outdir}/voice.mp3  ({len(lines)} linjer)")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))

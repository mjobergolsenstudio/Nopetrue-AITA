#!/usr/bin/env python3
"""
assemble.py
Setter sammen den ferdige videoen:
  - Visuell base: roterer mellom AI-klipp, stock b-roll og grafikk-bakgrunn
  - Voiceover (voice.mp3) som driver lengden
  - Bakgrunnsmusikk (ducked under voice)
  - Statistikk-grafikk som overlays paa riktig tidspunkt
  - Brente undertekster (caption per linje, TikTok-stil)
  - Watermark @NopeTrue

Bruk: python assemble.py <job_id> <format:shorts|long>
Krever lovlige assets i assets/{ai,stock,graphics,music}. INGEN kampklipp.
"""
import os, json, sys, random, glob, subprocess

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "config.json")))


def pick_visuals(seconds, fmt):
    """Velg nok lovlige klipp/bilder til a dekke varigheten."""
    pool = []
    for d in [CFG["visuals"]["ai_clips_dir"], CFG["visuals"]["stock_dir"]]:
        pool += glob.glob(f"{d}/*.mp4") + glob.glob(f"{d}/*.mov")
    if not pool:
        # fallback: animert gradient-bakgrunn i merkefarger
        return None
    random.shuffle(pool)
    return pool


def srt_from_timings(timings, path):
    def ts(s):
        h = int(s//3600); m = int((s%3600)//60); sec = s%60
        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".", ",")
    with open(path, "w") as f:
        for i, t in enumerate(timings, 1):
            f.write(f"{i}\n{ts(t['start'])} --> {ts(t['start']+t['dur'])}\n{t['text']}\n\n")


def build(job_id, fmt):
    outdir = f"build/{job_id}"
    spec = CFG["output"][fmt]
    W, H = spec["w"], spec["h"]
    timings = json.load(open(f"{outdir}/timings.json"))
    total = sum(t["dur"] for t in timings) + 1.0
    if fmt == "shorts":
        total = min(total, spec["max_seconds"])

    srt = f"{outdir}/captions.srt"; srt_from_timings(timings, srt)
    visuals = pick_visuals(total, fmt)
    music = glob.glob(f"{CFG['visuals']['music_dir']}/*.mp3")
    wm = CFG["brand"]["watermark"]

    # Bygg visuell base
    inputs, filt = [], []
    if visuals:
        # konkatener visuals, skaler/crop til format, loop til lengde
        concat_list = f"{outdir}/vis_list.txt"
        with open(concat_list, "w") as f:
            for v in visuals:
                f.write(f"file '{os.path.abspath(v)}'\n")
        base = f"{outdir}/base.mp4"
        subprocess.run(["ffmpeg","-y","-stream_loop","-1","-f","concat","-safe","0",
                        "-i",concat_list,"-t",str(total),
                        "-vf",f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={spec['fps']}",
                        "-an", base,"-loglevel","error"], check=True)
        vbase = base
    else:
        vbase = None  # gradient genereres i hovedkommandoen

    cmd = ["ffmpeg","-y"]
    if vbase:
        cmd += ["-i", vbase]
    else:
        cmd += ["-f","lavfi","-i",
                f"color=c={CFG['brand']['primary_color']}:s={W}x{H}:d={total}:r={spec['fps']}"]
    cmd += ["-i", f"{outdir}/voice.mp3"]
    music_idx = None
    if music:
        cmd += ["-i", music[0]]; music_idx = 2

    # filter: ducking + captions + watermark
    fc = []
    if music_idx is not None:
        fc.append("[1:a]volume=1.0[v0]")
        fc.append("[2:a]volume=0.18[m0]")
        fc.append("[v0][m0]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        amap = "[aout]"
    else:
        amap = "1:a"
    vf = (f"subtitles={srt}:force_style='FontName=Anton,FontSize=22,"
          f"PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,Outline=4,Alignment=2,MarginV=160',"
          f"drawtext=text='{wm}':fontcolor=white@0.7:fontsize=34:x=w-tw-40:y=60")
    fc.append(f"[0:v]{vf}[vout]")
    cmd += ["-filter_complex", ";".join(fc), "-map","[vout]","-map",amap,
            "-t",str(total),"-c:v","libx264","-preset","medium","-crf","20",
            "-c:a","aac","-b:a","192k","-pix_fmt","yuv420p",
            f"{outdir}/final_{fmt}.mp4","-loglevel","error"]
    subprocess.run(cmd, check=True)
    print(f"Ferdig: {outdir}/final_{fmt}.mp4  ({total:.1f}s, {W}x{H})")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "shorts")

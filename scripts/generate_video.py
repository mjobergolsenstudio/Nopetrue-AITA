import subprocess
import json
import os
import random
import shutil
from pathlib import Path

VIDEO_SOURCE = 'assets/minecraft.mp4'
AUDIO_PATH = '/tmp/aita_audio.mp3'
OUTPUT_PATH = 'output/aita_short.mp4'
COPY_PATH = 'output/video_copy/aita_short.mp4'
WIDTH, HEIGHT = 1080, 1920

def get_audio_duration():
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', AUDIO_PATH],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)['format']['duration'])

def get_video_duration():
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', VIDEO_SOURCE],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)['format']['duration'])

def generate_video():
    os.makedirs('output/video_copy', exist_ok=True)

    audio_dur = get_audio_duration()
    video_dur = get_video_duration()

    # Random start point in minecraft video
    max_start = max(0, video_dur - audio_dur - 2)
    start_time = random.uniform(0, max_start)

    print(f"Audio: {audio_dur:.1f}s, Video start: {start_time:.1f}s")

    # Load script for subtitle
    with open('/tmp/aita_script.txt') as f:
        script = f.read().strip()

    # Load story for title
    with open('/tmp/aita_story.json') as f:
        story = json.load(f)

    # AITA label at top
    title_filter = (
        "drawtext=text='Am I The Asshole?':"
        "fontsize=52:fontcolor=white:borderw=4:bordercolor=black:"
        "x=(w-text_w)/2:y=80:"
        "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    )

    # Split script into subtitle chunks (max 6 words per line)
    words = script.split()
    chunks = []
    chunk = []
    for word in words:
        chunk.append(word)
        if len(chunk) >= 5:
            chunks.append(' '.join(chunk))
            chunk = []
    if chunk:
        chunks.append(' '.join(chunk))

    # Time each chunk
    time_per_chunk = audio_dur / len(chunks)
    subtitle_filters = []
    for i, chunk in enumerate(chunks):
        t_start = i * time_per_chunk
        t_end = t_start + time_per_chunk
        safe_chunk = chunk.replace("'", "\\'").replace(":", "\\:")
        subtitle_filters.append(
            f"drawtext=text='{safe_chunk}':"
            f"fontsize=68:fontcolor=white:borderw=5:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"enable='between(t,{t_start:.2f},{t_end:.2f})'"
        )

    # Bottom CTA
    cta_filter = (
        f"drawtext=text='Comment your verdict! 👇':"
        f"fontsize=44:fontcolor=yellow:borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:y=h-120:"
        f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"enable='gte(t,{audio_dur-3:.1f})'"
    )

    all_filters = ",".join([
        f"crop=ih*9/16:ih",
        f"scale={WIDTH}:{HEIGHT}",
        title_filter,
        *subtitle_filters,
        cta_filter
    ])

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', VIDEO_SOURCE,
        '-i', AUDIO_PATH,
        '-vf', all_filters,
        '-t', str(audio_dur + 0.5),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-shortest',
        OUTPUT_PATH
    ]

    print("Assembling video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg error:", result.stderr[-2000:])
        raise RuntimeError("FFmpeg failed")

    shutil.copy2(OUTPUT_PATH, COPY_PATH)
    print(f"Video: {OUTPUT_PATH}")
    print(f"Copy for TT/IG: {COPY_PATH}")
    return OUTPUT_PATH

if __name__ == '__main__':
    generate_video()

import subprocess
import json
import os
import random
import shutil

ASSETS_DIR = 'assets'
AUDIO_PATH = '/tmp/aita_audio.mp3'
OUTPUT_PATH = 'output/aita_short.mp4'
COPY_PATH = 'output/video_copy/aita_short.mp4'
WIDTH, HEIGHT = 1080, 1920

def get_random_video():
    videos = [f for f in os.listdir(ASSETS_DIR)
              if f.lower().endswith(('.mp4', '.mov', '.webm'))]
    if not videos:
        raise FileNotFoundError(f"Ingen videoer i {ASSETS_DIR}/")
    chosen = random.choice(videos)
    print(f"Bakgrunnsvideo: {chosen}")
    return os.path.join(ASSETS_DIR, chosen)

def get_duration(filepath):
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', filepath],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)['format']['duration'])

def safe_text(text):
    # Fjern/erstatt tegn som ødelegger FFmpeg drawtext
    return (text
        .replace("'", "\u2019")
        .replace('"', '\u201c')
        .replace(':', ' -')
        .replace('\\', '')
        .replace('%', 'pct')
        .replace('[', '(')
        .replace(']', ')')
    )

def make_chunks(script, words_per_chunk=4):
    words = script.split()
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunks.append(' '.join(words[i:i+words_per_chunk]))
    return chunks

def generate_video():
    os.makedirs('output/video_copy', exist_ok=True)

    video_source = get_random_video()
    audio_dur = get_duration(AUDIO_PATH)
    video_dur = get_duration(video_source)

    max_start = max(0, video_dur - audio_dur - 2)
    start_time = random.uniform(0, max_start)
    print(f"Audio: {audio_dur:.1f}s | Start: {start_time:.1f}s")

    with open('/tmp/aita_script.txt') as f:
        script = f.read().strip()

    with open('/tmp/aita_story.json') as f:
        story = json.load(f)

    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

    # AITA label øverst — mindre font
    title_filter = (
        f"drawtext="
        f"text='Am I The Asshole\\?':"
        f"fontfile={font}:"
        f"fontsize=48:"
        f"fontcolor=white:"
        f"borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:"
        f"y=60"
    )

    # Tekst chunks — 4 ord per linje, sentrert i midten
    chunks = make_chunks(script, words_per_chunk=4)
    time_per_chunk = audio_dur / len(chunks)

    subtitle_filters = []
    for i, chunk in enumerate(chunks):
        t_start = i * time_per_chunk
        t_end = t_start + time_per_chunk
        safe = safe_text(chunk)
        subtitle_filters.append(
            f"drawtext="
            f"text='{safe}':"
            f"fontfile={font}:"
            f"fontsize=80:"
            f"fontcolor=white:"
            f"borderw=6:bordercolor=black:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"enable='between(t,{t_start:.2f},{t_end:.2f})'"
        )

    # CTA på slutten
    cta_filter = (
        f"drawtext="
        f"text='Comment your verdict! 👇':"
        f"fontfile={font}:"
        f"fontsize=44:"
        f"fontcolor=yellow:"
        f"borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:"
        f"y=h-140:"
        f"enable='gte(t,{max(0, audio_dur-4):.1f})'"
    )

    all_filters = ",".join([
        "crop=ih*9/16:ih",
        f"scale={WIDTH}:{HEIGHT}",
        title_filter,
        *subtitle_filters,
        cta_filter
    ])

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', video_source,
        '-i', AUDIO_PATH,
        '-filter_complex',
        # Mute bakgrunnsvideo, bruk kun voiceover-audio
        f'[0:v]{all_filters}[outv]',
        '-map', '[outv]',
        '-map', '1:a',          # Kun voiceover audio
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-t', str(audio_dur + 0.3),
        '-r', '30',
        '-pix_fmt', 'yuv420p',
        OUTPUT_PATH
    ]

    print("Assemblerer video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFmpeg stderr:", result.stderr[-3000:])
        raise RuntimeError("FFmpeg feilet")

    shutil.copy2(OUTPUT_PATH, COPY_PATH)
    print(f"✅ Video: {OUTPUT_PATH}")
    print(f"📱 Kopi: {COPY_PATH}")
    return OUTPUT_PATH

if __name__ == '__main__':
    generate_video()

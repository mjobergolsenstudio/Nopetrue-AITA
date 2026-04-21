import sys, os, json, random
sys.path.insert(0, os.path.dirname(__file__))

from fetch_story import pick_random_story
from summarize import summarize_story
from generate_tts import run as generate_tts
from generate_video import generate_video
from upload_youtube import upload_to_youtube

def run():
    print("=" * 50)
    print("AITA Shorts Pipeline starting...")
    print("=" * 50)

    timeframe = random.choice(['week', 'month'])
    print(f"\nStep 1: Fetching AITA story ({timeframe})...")
    story = pick_random_story(timeframe=timeframe)
    with open('/tmp/aita_story.json', 'w') as f:
        json.dump(story, f, ensure_ascii=False)

    print("\nStep 2: Generating script with Claude...")
    script = summarize_story(story)
    with open('/tmp/aita_script.txt', 'w') as f:
        f.write(script)

    print("\nStep 3: Generating TTS audio...")
    generate_tts()

    print("\nStep 4: Assembling video...")
    video_path = generate_video()

    print("\nStep 5: Uploading to YouTube...")
    upload_to_youtube(video_path, story, script)

    print("\n" + "=" * 50)
    print("Pipeline complete!")

if __name__ == '__main__':
    run()

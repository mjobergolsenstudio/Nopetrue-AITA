import asyncio
import edge_tts
import os

VOICE = 'en-US-ChristopherNeural'  # Deep, storytelling voice
AUDIO_PATH = '/tmp/aita_audio.mp3'
SCRIPT_PATH = '/tmp/aita_script.txt'

async def _generate(text):
    communicate = edge_tts.Communicate(text, VOICE, rate='+8%')
    await communicate.save(AUDIO_PATH)

def run():
    with open(SCRIPT_PATH) as f:
        text = f.read().strip()
    asyncio.run(_generate(text))
    print(f"Audio saved: {AUDIO_PATH}")

if __name__ == '__main__':
    run()

import requests
import json
import os
import random
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
}
USED_FILE = 'used_posts.json'

def load_used():
    if os.path.exists(USED_FILE):
        with open(USED_FILE) as f:
            return json.load(f)
    return []

def save_used(used):
    with open(USED_FILE, 'w') as f:
        json.dump(used[-50:], f)

def fetch_posts(timeframe='week'):
    url = f'https://www.reddit.com/r/AmItheAsshole/top.json?t={timeframe}&limit=50'
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"Reddit status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                return data['data']['children']
            time.sleep(2)
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return []

def pick_random_story(timeframe='week'):
    used = load_used()
    posts = fetch_posts(timeframe)

    if not posts:
        # Fallback til måned hvis uke feiler
        posts = fetch_posts('month')

    if not posts:
        raise RuntimeError("Kunne ikke hente Reddit-innlegg")

    # Filtrer og velg
    valid = []
    for post in posts:
        p = post['data']
        if p['id'] in used:
            continue
        if p.get('selftext', '') in ['', '[removed]', '[deleted]']:
            continue
        word_count = len(p['selftext'].split())
        if word_count < 80 or word_count > 2000:
            continue
        valid.append(p)

    if not valid:
        # Ignorer used-filter hvis ingen gyldige
        valid = [p['data'] for p in posts
                 if p['data'].get('selftext', '') not in ['', '[removed]', '[deleted]']
                 and 80 <= len(p['data']['selftext'].split()) <= 2000]

    if not valid:
        raise RuntimeError("Ingen gyldige AITA-innlegg funnet")

    chosen = random.choice(valid)
    used.append(chosen['id'])
    save_used(used)

    print(f"Story: {chosen['title'][:70]}...")
    print(f"Words: {len(chosen['selftext'].split())}, Score: {chosen['score']}")

    return {
        'id': chosen['id'],
        'title': chosen['title'],
        'body': chosen['selftext'],
        'score': chosen['score'],
        'url': f"https://reddit.com{chosen['permalink']}"
    }

if __name__ == '__main__':
    story = pick_random_story()
    print(json.dumps(story, indent=2)[:500])

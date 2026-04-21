import requests
import json
import os
import random

HEADERS = {'User-Agent': 'AITAShorts/1.0 (by /u/nopetrue)'}
USED_FILE = 'used_posts.json'

def load_used():
    if os.path.exists(USED_FILE):
        with open(USED_FILE) as f:
            return json.load(f)
    return []

def save_used(used):
    with open(USED_FILE, 'w') as f:
        json.dump(used[-50:], f)  # Keep last 50

def pick_random_story(timeframe='week'):
    used = load_used()
    url = f'https://www.reddit.com/r/AmItheAsshole/top.json?t={timeframe}&limit=50'
    r = requests.get(url, headers=HEADERS)
    posts = r.json()['data']['children']

    for _ in range(10):
        post = random.choice(posts)['data']
        if post['id'] in used:
            continue
        if post['selftext'] in ['', '[removed]', '[deleted]']:
            continue
        word_count = len(post['selftext'].split())
        if word_count < 100 or word_count > 2000:
            continue

        used.append(post['id'])
        save_used(used)

        print(f"Story: {post['title'][:60]}...")
        print(f"Words: {word_count}, Score: {post['score']}")
        return {
            'id': post['id'],
            'title': post['title'],
            'body': post['selftext'],
            'score': post['score'],
            'url': f"https://reddit.com{post['permalink']}"
        }

    # Fallback — just pick first valid one
    for post in posts:
        p = post['data']
        if p['selftext'] not in ['', '[removed]', '[deleted]']:
            return {'id': p['id'], 'title': p['title'], 'body': p['selftext'], 'score': p['score'], 'url': ''}

if __name__ == '__main__':
    story = pick_random_story()
    print(json.dumps(story, indent=2))

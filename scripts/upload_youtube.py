import os
import json
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

TOKEN_FILE = 'token.pickle'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_youtube_client():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(video_path, story, script):
    youtube = get_youtube_client()

    title = f"AITA: {story['title'][:60]} #shorts #aita"
    description = (
        f"{script}\n\n"
        f"Original story: {story.get('url', '')}\n\n"
        f"#aita #amitheashole #reddit #shorts #storytime #viral"
    )

    body = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': ['aita', 'amitheashole', 'reddit', 'shorts', 'storytime', 'viral', 'reddit stories'],
            'categoryId': '22',
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload {int(status.progress() * 100)}%")

    video_id = response['id']
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")
    return video_id

if __name__ == '__main__':
    story = json.load(open('/tmp/aita_story.json'))
    script = open('/tmp/aita_script.txt').read()
    upload_to_youtube('output/aita_short.mp4', story, script)

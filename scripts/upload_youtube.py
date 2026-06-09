#!/usr/bin/env python3
"""
upload_youtube.py
Laster opp ferdig video til YouTube via Data API v3.
Gjenbruker monsteret fra SmartNorge Shorts. Henter tittel/desc/tags fra script.json.

Bruk: python upload_youtube.py <job_id> <format>
Krever env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
import os, json, sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    return build("youtube", "v3", credentials=creds)

def upload(job_id, fmt):
    outdir = f"build/{job_id}"
    s = json.load(open(f"{outdir}/script.json"))
    path = f"{outdir}/final_{fmt}.mp4"
    title = s["title"]
    if fmt == "shorts" and "#Shorts" not in title:
        title = (title[:55] + " #Shorts")
    body = {
        "snippet": {
            "title": title[:100],
            "description": s["description"],
            "tags": s.get("tags", [])[:15],
            "categoryId": "17",  # Sports
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = service().videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
    print(f"Lastet opp: https://youtu.be/{resp['id']}")
    return resp["id"]

if __name__ == "__main__":
    upload(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "shorts")

# AITA Shorts Pipeline — NopTrue

Automatisk YouTube Shorts-pipeline som daglig:
1. Henter top AITA-story fra Reddit
2. Komprimerer til ~100 ord med Claude
3. Lager TTS-voiceover (edge-tts, gratis)
4. Legger Minecraft parkour-bakgrunn med undertekster
5. Poster til YouTube automatisk
6. Lagrer kopi i `video_copy/` for manuell TikTok/IG-posting

## Mappestruktur
```
aita-pipeline/
├── assets/
│   └── minecraft.mp4     ← Last opp din Minecraft-video her
├── scripts/
│   ├── fetch_story.py
│   ├── summarize.py
│   ├── generate_tts.py
│   ├── generate_video.py
│   ├── upload_youtube.py
│   └── run_pipeline.py
├── output/
│   └── video_copy/       ← Kopi for TikTok/IG (7 dager artifact)
├── setup_youtube_auth.py ← Kjør én gang på PC
└── .github/workflows/
    └── aita-pipeline.yml
```

## Oppsett

### 1. Last opp Minecraft-video
Legg `minecraft.mp4` i `assets/`-mappen i repoet.

### 2. YouTube auth (én gang på PC)
```bash
pip install google-auth-oauthlib google-api-python-client
python setup_youtube_auth.py
```
Kopier base64-strengen og legg inn som `YOUTUBE_TOKEN_PICKLE` i GitHub Secrets.

### 3. GitHub Secrets
| Secret | Verdi |
|--------|-------|
| `ANTHROPIC_API_KEY` | Fra console.anthropic.com |
| `YOUTUBE_TOKEN_PICKLE` | Fra setup_youtube_auth.py |

### 4. Kjør manuelt første gang
Actions → AITA Shorts Pipeline → Run workflow

## Kostnad
- Reddit API: Gratis
- edge-tts: Gratis
- Claude Haiku: ~$0.01 per video
- GitHub Actions: Gratis
- **Total: ~$0.30/mnd**

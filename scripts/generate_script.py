#!/usr/bin/env python3
"""
generate_script.py
Bruker Claude Haiku til a skrive manus (norsk), tittel, beskrivelse og tags
basert pa kampdata fra API-Football. Henter ogsa statistikk for grafikk.

Output per jobb: build/<job_id>/script.json
  { narration: [...linjer], title, description, tags, hook, stats: {...} }

Krever env: API_FOOTBALL_KEY, ANTHROPIC_API_KEY
"""
import os, json, sys, re
import requests
import anthropic

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "config.json")))
FB_KEY = os.environ["API_FOOTBALL_KEY"]
BASE = CFG["api_football"]["base_url"]
FB_HEADERS = {"x-apisports-key": FB_KEY}
client = anthropic.Anthropic()


def fixture_data(fid):
    r = requests.get(f"{BASE}/fixtures", headers=FB_HEADERS, params={"id": fid}, timeout=30)
    r.raise_for_status()
    return r.json()["response"][0]


def fixture_stats(fid):
    r = requests.get(f"{BASE}/fixtures/statistics", headers=FB_HEADERS, params={"fixture": fid}, timeout=30)
    return r.json().get("response", []) if r.ok else []


def fixture_events(fid):
    r = requests.get(f"{BASE}/fixtures/events", headers=FB_HEADERS, params={"fixture": fid}, timeout=30)
    return r.json().get("response", []) if r.ok else []


SYSTEM = """Du er manusforfatter for en norsk fotball-YouTube-kanal (NopeTrue) som dekker VM 2026.
Stilen er energisk, presis og litt frekk - TikTok-tempo. Du skriver ALDRI pastander
du ikke har data for. Du beskriver ikke kampbilder (vi viser grafikk og atmosfaere, ikke kampklipp).
Du svarer KUN med gyldig JSON, ingen markdown, ingen forklaring."""


def prompt_for(job, fix, stats, events):
    home = fix["teams"]["home"]["name"]; away = fix["teams"]["away"]["name"]
    score = fix["goals"]
    kind = job["type"]
    return f"""Lag manus for en {kind.replace('_',' ')}-video.
Kamp: {home} vs {away}. Resultat: {score['home']}-{score['away']} (status: {fix['fixture']['status']['short']}).
Hendelser: {json.dumps(events[:15], ensure_ascii=False)}
Statistikk: {json.dumps(stats, ensure_ascii=False)[:1500]}

Returner JSON med disse feltene:
{{
  "hook": "forste 3 sekunder, ma stoppe scrollingen",
  "narration": ["linje 1", "linje 2", ...],   // 6-10 linjer for shorts, naturlig norsk tale
  "title": "klikkbar YouTube-tittel under 70 tegn",
  "description": "2-3 setninger + relevante hashtags",
  "tags": ["...10-15 tags..."],
  "graphics": [ {{"type":"stat_bar","label":"Ballbesittelse","home":55,"away":45}} ]  // 2-4 grafikk-kort fra faktiske tall
}}"""


def gen(job):
    fid = job.get("fixture_id") or job["fixture_ids"][0]
    fix = fixture_data(fid)
    stats = fixture_stats(fid)
    events = fixture_events(fid)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt_for(job, fix, stats, events)}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```json|```$", "", raw).strip()
    data = json.loads(raw)
    data["_fixture"] = {"home": fix["teams"]["home"]["name"],
                        "away": fix["teams"]["away"]["name"],
                        "goals": fix["goals"]}
    return data


if __name__ == "__main__":
    jobs = json.load(open("jobs.json"))["jobs"]
    if not jobs:
        sys.exit(0)
    job = jobs[0]  # workflow kjorer en jobb per matrix-entry; her tar vi forste
    job_id = f"{job['type']}_{job.get('fixture_id', 'digest')}"
    os.makedirs(f"build/{job_id}", exist_ok=True)
    script = gen(job)
    json.dump(script, open(f"build/{job_id}/script.json", "w"), ensure_ascii=False, indent=2)
    print(f"Manus skrevet: build/{job_id}/script.json")
    print("Tittel:", script["title"])

#!/usr/bin/env python3
"""
fetch_fixtures.py
Henter VM-kampkalenderen fra API-Football og bestemmer hvilke jobber
som skal kjores i dag: pre-match, post-match og daglig digest.
Skriver jobs.json som resten av pipelinen leser.

Krever env: API_FOOTBALL_KEY
"""
import os, json, datetime as dt, sys
import requests

CFG = json.load(open(os.path.join(os.path.dirname(__file__), "..", "config", "config.json")))
KEY = os.environ["API_FOOTBALL_KEY"]
BASE = CFG["api_football"]["base_url"]
HEADERS = {"x-apisports-key": KEY}

NOW = dt.datetime.now(dt.timezone.utc)


def get_fixtures():
    params = {
        "league": CFG["api_football"]["wc_league_id"],
        "season": CFG["api_football"]["season"],
    }
    r = requests.get(f"{BASE}/fixtures", headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])


def is_focus(fix):
    teams = [fix["teams"]["home"]["name"], fix["teams"]["away"]["name"]]
    return any(t in CFG["focus_teams"] for t in teams)


def build_jobs(fixtures):
    jobs = []
    pre_window = CFG["triggers"]["pre_match_hours_before"]
    post_window = CFG["triggers"]["post_match_minutes_after"]

    for fix in fixtures:
        kickoff = dt.datetime.fromisoformat(fix["fixture"]["date"].replace("Z", "+00:00"))
        status = fix["fixture"]["status"]["short"]
        priority = "high" if is_focus(fix) else "normal"

        # PRE-MATCH: innen X timer for avspark, ikke startet
        hrs_to = (kickoff - NOW).total_seconds() / 3600
        if 0 < hrs_to <= pre_window and status == "NS":
            jobs.append({"type": "pre_match", "fixture_id": fix["fixture"]["id"],
                         "priority": priority, "format": "both"})

        # POST-MATCH: ferdig innen X minutter
        if status == "FT":
            ended = kickoff + dt.timedelta(minutes=120)
            mins_since = (NOW - ended).total_seconds() / 60
            if 0 <= mins_since <= post_window:
                jobs.append({"type": "post_match", "fixture_id": fix["fixture"]["id"],
                             "priority": priority, "format": "both"})

    # DIGEST: en gang i dognet (styres av cron i workflow)
    if os.environ.get("RUN_DIGEST") == "1":
        todays = [f["fixture"]["id"] for f in fixtures
                  if dt.datetime.fromisoformat(f["fixture"]["date"].replace("Z","+00:00")).date() == NOW.date()]
        if todays:
            jobs.append({"type": "digest", "fixture_ids": todays,
                         "priority": "normal", "format": "long"})

    # prioriter Norge-jobber forst
    jobs.sort(key=lambda j: 0 if j["priority"] == "high" else 1)
    return jobs


if __name__ == "__main__":
    fixtures = get_fixtures()
    jobs = build_jobs(fixtures)
    json.dump({"generated": NOW.isoformat(), "jobs": jobs}, open("jobs.json", "w"), indent=2)
    print(f"{len(jobs)} jobb(er) planlagt:")
    for j in jobs:
        print(f"  - {j['type']} ({j['priority']})")
    if not jobs:
        print("Ingen jobber i dag.")
        sys.exit(0)

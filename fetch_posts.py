#!/usr/bin/env python3
"""
Step 1 of the Cowork workflow: fetch posts from Yellowdig and save to posts.json.

Run:  make fetch
Then: let Claude Cowork analyse posts.json and save analysis.json
Then: make publish
"""

import json
import sys
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
POSTS_PATH  = Path(__file__).parent / "posts.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print("ERROR: config.json not found. Please create it from config.example.json.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def fetch_yellowdig_posts(config: dict) -> list[dict]:
    api_key    = config["yellowdig"]["api_key"]
    network    = config["yellowdig"]["network"]
    community  = config["yellowdig"]["community"]
    base_url   = config["yellowdig"]["base_url"]
    lookback_h = config.get("lookback_hours", 24)

    # start_ts is sent as a hint to the API, but it doesn't reliably filter results.
    # Client-side filtering on start_dt is the authoritative cutoff.
    start_dt = datetime.now(timezone.utc) - timedelta(hours=lookback_h)
    start_ts = int(start_dt.timestamp())
    headers  = {"apikey": api_key, "accept": "application/json"}
    url      = f"{base_url}/network/{network}/community/{community}/events"

    print(f"Fetching Yellowdig posts from the last {lookback_h}h (since {start_dt.strftime('%d %b %Y %H:%M UTC')}) …")

    all_events = []
    cursor = None
    while True:
        params: dict = {"start": start_ts, "limit": 250}
        if cursor:
            params["cursor"] = cursor

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            body = response.json()
        except requests.HTTPError as e:
            print(f"ERROR fetching Yellowdig posts: {e}\nResponse: {e.response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

        page_events = body.get("data", [])
        all_events.extend(page_events)

        if body.get("at-end", True) or not page_events:
            break
        cursor = body.get("cursor")
        if not cursor:
            break

    # The API's `start` param doesn't reliably filter by time, so filter client-side.
    seen, posts = set(), []
    for event in all_events:
        if event.get("event/type") != "post":
            continue

        event_id = event.get("event/squuid") or str(event.get("db/id", ""))
        if not event_id or event_id in seen:
            continue
        seen.add(event_id)

        post_ts_str = event.get("date/iso", event.get("system/created-at", ""))
        try:
            post_dt = datetime.fromisoformat(post_ts_str.replace("Z", "+00:00"))
            if post_dt < start_dt:
                continue
        except (ValueError, AttributeError):
            pass  # keep event if timestamp can't be parsed

        actor  = event.get("event/actor", {})
        author = actor.get("name", "Unknown") if isinstance(actor, dict) else str(actor)

        topics = event.get("post/topics", [])
        tags   = [t.get("topic/title", str(t)) if isinstance(t, dict) else str(t) for t in topics]

        print(f"  + [{post_ts_str[:16]}] {event.get('post/title', '(no title)')[:60]}")

        posts.append({
            "id":        event_id,
            "title":     event.get("post/title", "(no title)"),
            "body":      event.get("post/body-text", ""),
            "web_url":   "",
            "tags":      tags,
            "author":    author,
            "timestamp": post_ts_str,
        })

    return posts


if __name__ == "__main__":
    config = load_config()
    posts  = fetch_yellowdig_posts(config)

    output = {
        "fetched_at":    datetime.now(timezone.utc).isoformat(),
        "lookback_hours": config.get("lookback_hours", 24),
        "interests":     config.get("interests", {}),
        "posts":         posts,
    }

    with open(POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  → {len(posts)} post(s) saved to {POSTS_PATH}")
    if not posts:
        print("  No posts found. Try increasing lookback_hours in config.json.")
    else:
        print("  Next step: run 'make publish' after Claude Cowork writes analysis.json")

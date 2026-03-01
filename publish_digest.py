#!/usr/bin/env python3
"""
Step 2 of the Cowork workflow: read analysis.json and publish to Notion.

Claude Cowork analyses posts.json and writes analysis.json.
This script then publishes the digest to Notion.

Run:  make publish
"""

import json
import sys
import requests
from datetime import datetime
from pathlib import Path

CONFIG_PATH   = Path(__file__).parent / "config.json"
ANALYSIS_PATH = Path(__file__).parent / "analysis.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print("ERROR: config.json not found. Please create it from config.example.json.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def build_notion_content(analysis: dict, run_date: str) -> str:
    """Builds Notion-flavoured Markdown content for the digest page."""
    title        = analysis.get("digest_title", "Yellowdig Digest")
    summary      = analysis.get("summary", "")
    need_to_know = analysis.get("need_to_know", [])
    posts        = analysis.get("relevant_posts", [])

    lines = [
        f"> Generated on {run_date}  |  {len(posts)} relevant post(s) found",
        "",
        "## Community Overview",
        summary,
        "",
        "---",
        "",
    ]

    if need_to_know:
        lines += ["## Need to Know", ""]
        for item in need_to_know:
            url        = item.get("web_url", "")
            title_line = f"**[{item['title']}]({url})**" if url else f"**{item['title']}**"
            lines += [
                f"### {title_line}",
                f"{item.get('author', 'Unknown')}",
                "",
                item.get("summary", ""),
                "",
                "---",
                "",
            ]

    lines += ["## Posts Worth Engaging With", ""]

    if not posts:
        lines.append("_No posts matched your interests today. Check back tomorrow!_")
    else:
        for i, post in enumerate(posts, 1):
            ts = post.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts = dt.strftime("%-d %b %Y, %-I:%M %p")
                except Exception:
                    pass

            url        = post.get("web_url", "")
            title_line = f"**[{post['title']}]({url})**" if url else f"**{post['title']}**"

            lines += [
                f"### {i}. {title_line}",
                f"{post.get('author', 'Unknown')}  ·  {ts}",
                "",
                f"**Why it's relevant:** {post.get('relevance_reason', '')}",
                "",
                "**Suggested Comment:**",
                f"> {post.get('suggested_comment', '')}",
                "",
                "---",
                "",
            ]

    draft = analysis.get("draft_post", {})
    if draft:
        lines += [
            "## Your Post for Today",
            "",
            f"**{draft.get('title', '')}**",
            "",
            draft.get("body", ""),
            "",
        ]

    return "\n".join(lines)


def create_notion_page(analysis: dict, config: dict, run_date: str) -> str:
    """Creates a new Notion page under the configured parent page."""
    notion_token   = config["notion"]["api_key"]
    parent_page_id = config["notion"]["parent_page_id"]

    page_title = f"Yellowdig Digest — {run_date}"
    content_md = build_notion_content(analysis, run_date)

    headers = {
        "Authorization":  f"Bearer {notion_token}",
        "Content-Type":   "application/json",
        "Notion-Version": "2022-06-28",
    }

    blocks = []
    for line in content_md.split("\n"):
        if line.startswith("### "):
            blocks.append({"object": "block", "type": "heading_3",
                           "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}})
        elif line.startswith("## "):
            blocks.append({"object": "block", "type": "heading_2",
                           "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}})
        elif line.startswith("> "):
            blocks.append({"object": "block", "type": "quote",
                           "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}})
        elif line.strip() == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.strip() == "":
            blocks.append({"object": "block", "type": "paragraph",
                           "paragraph": {"rich_text": []}})
        else:
            blocks.append({"object": "block", "type": "paragraph",
                           "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}})

    payload = {
        "parent":     {"type": "page_id", "page_id": parent_page_id},
        "properties": {
            "title": {"title": [{"type": "text", "text": {"content": page_title}}]}
        },
        "children": blocks[:100],
    }

    print(f"Creating Notion page: '{page_title}' …")
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        print(f"ERROR creating Notion page: {response.status_code}\n{response.text}")
        sys.exit(1)

    page_url = response.json().get("url", "")

    if len(blocks) > 100:
        page_id   = response.json()["id"]
        remaining = blocks[100:]
        for i in range(0, len(remaining), 100):
            chunk = remaining[i:i + 100]
            append_resp = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
                json={"children": chunk},
                timeout=30,
            )
            if append_resp.status_code != 200:
                print(f"WARNING: Could not append all blocks. {append_resp.text}")

    return page_url


if __name__ == "__main__":
    if not ANALYSIS_PATH.exists():
        print(f"ERROR: {ANALYSIS_PATH} not found.")
        print("  Claude Cowork must analyse posts.json and save analysis.json first.")
        sys.exit(1)

    with open(ANALYSIS_PATH, encoding="utf-8") as f:
        analysis = json.load(f)

    required_keys = {"digest_title", "summary", "relevant_posts"}
    missing = required_keys - set(analysis.keys())
    if missing:
        print(f"ERROR: analysis.json is missing required keys: {missing}")
        sys.exit(1)

    config   = load_config()
    run_date = datetime.now().strftime("%-d %b %Y")
    page_url = create_notion_page(analysis, config, run_date)

    print(f"\n✅ Notion page created: {page_url}")

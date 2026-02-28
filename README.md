# Yellowdig Daily Digest Agent

Fetches today's Yellowdig posts, finds what's relevant to your interests, and drops a structured digest with comment suggestions into Notion — every morning, fully automated.

---

## How it works

```
7:50 AM  Mac Launch Agent  →  make fetch  →  posts.json
8:00 AM  Claude Cowork     →  analyse  →  publish to Notion
```

The fetch runs on your Mac (not inside Cowork) because Cowork's sandbox restricts outbound network access to an allowlist of approved domains — and Yellowdig's API is not on it. A Mac Launch Agent is macOS's built-in task scheduler: it runs `make fetch` automatically at 7:50 AM every day, even after restarts, and retries if your Mac was asleep at the scheduled time.

---

## Setup (one-time)

### 1. Configure credentials

```bash
cp config.example.json config.json
```

Fill in `config.json`:

| Key | Where to find it |
|-----|-----------------|
| `yellowdig.api_key` | Yellowdig → Settings → API Keys |
| `yellowdig.network` | URL-name or UUID of your Yellowdig network (organisation) |
| `yellowdig.community` | UUID of your community (visible in the community URL) |
| `notion.api_key` | notion.so/my-integrations → New integration → Internal Integration Token |
| `notion.parent_page_id` | Target Notion page → ··· → Copy link → 32-char hex ID at end of URL |

### 2. Connect Notion to your page (required)

In Notion: open the parent page → **···** → **Add connections** → select your integration.

### 3. Install the Mac scheduler

```bash
cd [~/repo/path]
chmod +x install_scheduler.sh && ./install_scheduler.sh
```

This installs the Launch Agent and does a live fetch test. After this, everything runs automatically.

### 4. Create the Cowork scheduled task

In the Claude desktop app, open **Cowork** → **New scheduled task** and fill in:

| Field | Value |
|-------|-------|
| **Title** | `Yellowdig Study Assistance` |
| **Schedule** | Daily at 8:00 AM |
| **Description** | Daily scheduled job to analyse yellowdig recent posts, suggest comment, and put it in Notion |
| **Workspace folder** | Select this `mbs-yellowdig-cowork` folder |
| **Prompt** | Paste the block below |

```
posts.json is pre-fetched by a local Mac script that runs at 7:50 AM, before
this task fires.

1. Read posts.json from the workspace folder.
2. Produce two sections and save as analysis.json:
   {
     "digest_title": "Yellowdig Digest — DD Mon YYYY",
     "need_to_know": [
       {
         "id", "title", "author", "timestamp", "web_url",
         "summary"   ← 2-3 sentence summary of what was said and why it matters
       }
     ],
     "relevant_posts": [
       {
         "id", "title", "author", "timestamp", "web_url",
         "relevance_reason", "suggested_comment"
       }
     ]
   }

   need_to_know: posts from instructors or peers that contain important
   information (deadlines, policy changes, assignment clarifications, key
   announcements). Include regardless of your interest topics.

   relevant_posts: posts that match the interests listed in posts.json.
   For each, write a thoughtful 2-4 sentence MBA comment that adds value
   to the discussion.

3. Publish the digest to Notion using the Notion MCP tool (do NOT run
   publish_digest.py — it is blocked by the network proxy). Use the
   notion.parent_page_id from config.json as the parent page. Structure
   the Notion page with two clear sections: "Need to Know" followed by
   "Posts Worth Engaging With".
```

---

## Customising your interests

Edit the `interests` section in `config.json`:

- **`topics`** — subjects you care about (e.g. "AI", "Cybersecurity")
- **`engagement_signal`** — the kinds of discussions you typically jump into

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `401 Unauthorized` from Yellowdig | Check `api_key` in config.json |
| `400 Bad Request` from Yellowdig | Check `network` and `community` values in config.json |
| No posts found | Community may be quiet — try increasing `lookback_hours` in config.json |
| Notion page not created | Make sure the integration is connected to the parent page (step 2) |
| Fetch didn't run this morning | Check `fetch.log` in this folder for errors |

---

## File structure

```
mbs-yellowdig-cowork/
├── fetch_posts.py        ← run by the Mac Launch Agent via make fetch
├── publish_digest.py     ← unused (Cowork publishes via Notion MCP)
├── install_scheduler.sh  ← one-time setup: installs the Mac Launch Agent
├── posts.json            ← written by fetch, read by Cowork (gitignored)
├── analysis.json         ← written by Cowork (gitignored)
├── fetch.log             ← Launch Agent output log (gitignored)
├── config.json           ← your secrets (never commit)
├── config.example.json   ← template (safe to share)
├── requirements.txt
├── Makefile
└── README.md
```

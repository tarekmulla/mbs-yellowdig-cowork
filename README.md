# Yellowdig Daily Digest Agent

Fetches today's Yellowdig posts, finds what's relevant to your interests, and drops a structured digest with comment suggestions into Notion, fully automated.

---

## Prerequisites

Before setting up the agent, make sure you have the following:

| Requirement | Notes |
|-------------|-------|
| **Claude Pro (or Team/Enterprise) subscription** | Cowork mode and scheduled tasks require a paid Claude plan. A free Claude account is not sufficient. |
| **Claude desktop app** | Cowork runs inside the Claude desktop app (macOS). Download from [claude.ai/download](https://claude.ai/download). |
| **"All domains" network access enabled** | Required for Claude to reach the Yellowdig and Notion APIs. See Setup step 1. |
| **Yellowdig account with API access** | You must be a member of a Yellowdig community and have an API key issued for your account (Settings → API Keys). |
| **Yellowdig community UUID** | Visible in the community URL. Required in `config.json`. |
| **Notion account** | A free Notion account is sufficient. You need permission to create an internal integration and connect it to a page. |
| **Python 3.9+** | The fetch and publish scripts require Python 3. Run `python3 --version` to check. Python is pre-installed on macOS; Windows users may need to install it from [python.org](https://www.python.org/downloads/). |
| **Python dependencies installed** | Run `make setup` once from the project folder to create a virtual environment and install all required packages from `requirements.txt`. |

---

## How it works

```
8:00 AM  Claude Cowork  →  fetch_posts.py  →  analyse  →  publish_digest.py  →  Notion
```

Claude handles the entire pipeline end-to-end: fetching posts from the Yellowdig API, analysing them against your interests, and publishing the digest to Notion. No separate Mac scheduler required.


---

## Setup (one-time)

### 1. Enable "All domains" in Claude settings

Open the Claude desktop app → **Settings → Capabilities** → enable **All domains**. This allows Claude to reach the Yellowdig API and Notion API directly.

### 2. Configure credentials

```bash
cp config.example.json config.json
```

Fill in `config.json`:

| Key | Where to find it |
|-----|-----------------|
| `yellowdig.api_key` | Yellowdig → Settings → API Keys |
| `yellowdig.network` | URL-name or UUID of your Yellowdig network (organisation) |
| `yellowdig.community` | UUID of your community (visible in the community URL) |
| `notion.api_key` | notion.so/my-integrations → New internal integration → Internal Integration Secret |
| `notion.parent_page_id` | Target Notion page → ··· → Copy link → 32-char hex ID at end of URL |

### 3. Create a Notion internal integration

1. Go to [notion.so/Internal integrations](https://www.notion.so/profile/integrations/internal) → **New integration**
2. Give it a name (e.g. `Yellowdig Digest`), and select your workspace
3. Click **Save** → copy the **Internal Integration Secret** into `notion.api_key` in `config.json`

### 4. Connect the integration to your Notion page

Open your target Notion page → click **···** (top right) → **Add connections** → select your integration.

> The integration must be connected to the page before Claude can create sub-pages under it.

### 5. Create the Cowork scheduled task

In the Claude desktop app, open **Cowork** → **New scheduled task** and fill in:

| Field | Value |
|-------|-------|
| **Title** | `Yellowdig Study Assistance` |
| **Schedule** | Daily at 8:00 AM |
| **Description** | Daily scheduled job to analyse yellowdig recent posts, suggest comment, and put it in Notion |
| **Workspace folder** | Select this `mbs-yellowdig-cowork` folder |
| **Prompt** | Paste the block below |

```

1. Run fetch_posts.py from the workspace folder to fetch the latest Yellowdig posts.
2. Produce three sections and save as analysis.json:
   {
     "digest_title": "Yellowdig Digest — DD Mon YYYY",
     "summary": "2-3 sentence overview of the community activity this period",
     "need_to_know": [
       {
         "id", "title", "author", "timestamp", "web_url",
         "summary"
       }
     ],
     "relevant_posts": [
       {
         "id", "title", "author", "timestamp", "web_url",
         "relevance_reason", "suggested_comment"
       }
     ],
     "draft_post": {
       "title": "suggested post title",
       "body": "full draft post body (3-5 sentences)"
     }
   }

   need_to_know: posts from instructors or peers that contain important
   information (deadlines, policy changes, assignment clarifications, key
   announcements). Include regardless of your interest topics.

   relevant_posts: posts that match the interests listed in posts.json.
   For each, write a thoughtful 2-4 sentence MBA comment that adds value
   to the discussion.

   draft_post: a single original post you could publish to the community,
   inspired by the trending topics in today's posts. Should spark discussion,
   connect to MBA themes, and reflect the engagement_signal in posts.json.

3. Publish the digest to Notion by running publish_digest.py from the
   workspace folder.
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
| Notion page not created | Make sure the integration is connected to the parent page (steps 3–4) |
| Network error / connection refused | Confirm "All domains" is enabled in Claude Settings → Capabilities |

---

## File structure

```
mbs-yellowdig-cowork/
├── fetch_posts.py        ← run by Claude to fetch posts from Yellowdig API
├── publish_digest.py     ← run by Claude to publish the digest to Notion
├── posts.json            ← written by fetch_posts.py (gitignored)
├── analysis.json         ← written by Claude (gitignored)
├── config.json           ← your secrets (never commit)
├── config.example.json   ← template (safe to share)
├── requirements.txt
├── Makefile
└── README.md
```

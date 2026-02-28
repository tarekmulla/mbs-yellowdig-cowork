# Yellowdig Daily Digest Agent

Fetches today's Yellowdig posts, finds what's relevant to your interests, and drops a structured digest with copy-paste comment suggestions into Notion — every morning, automatically via Claude Cowork.

---

## How it works

```
Yellowdig API → fetch_posts.py → posts.json
      ↓
Claude Cowork → reads posts.json, filters by your interests, writes analysis.json
      ↓
publish_digest.py → Notion page
```

---

## Setup (one-time, ~10 minutes)

### 1. Create your config file

```bash
cp config.example.json config.json
```

Then open `config.json` and fill in:

| Key | Where to find it |
|-----|-----------------|
| `yellowdig.api_key` | Yellowdig → Settings → API Keys |
| `yellowdig.network` | The URL-name or UUID of your Yellowdig network/organisation |
| `yellowdig.community` | The UUID of your community (visible in the community URL) |
| `notion.api_key` | https://www.notion.so/my-integrations → New integration → copy Internal Integration Token |
| `notion.parent_page_id` | Open your target Notion page → click ··· → Copy link → the 32-char hex ID at the end of the URL |

### 2. Connect Notion Integration to your page

In Notion: open the parent page → click **···** (top right) → **Add connections** → select your integration.

### 3. Set up environment and install dependencies

```bash
make setup
```

This creates a `.venv` virtual environment and installs all required packages.

### 4. Test the fetch step

```bash
make fetch
```

You should see `posts.json` created in the project folder. Then follow the Cowork setup below to complete the workflow.

---

## Makefile reference

| Command | Description |
|---------|-------------|
| `make setup` | Create `.venv` virtual environment and install all dependencies (run once) |
| `make install` | Re-install / update dependencies into an existing venv |
| `make fetch` | Fetch posts from Yellowdig → `posts.json` |
| `make publish` | Publish `analysis.json` to Notion |
| `make clean` | Delete the virtual environment |

---

## Scheduling in Claude Cowork

This is the recommended approach if you have a **Claude Pro** subscription. Claude Cowork acts as the AI brain.

### How it works

```
make fetch  →  posts.json  →  Claude Cowork analyses  →  analysis.json  →  make publish  →  Notion
```

### Cowork scheduling prompt

Copy this prompt into the **Cowork** tab of Claude Desktop, replacing `[PROJECT_PATH]` with your actual path (e.g. `/Users/john/mbs-yellowdig-cowork`):

---

> ```
> Every morning at 8:00 AM, run my Yellowdig digest workflow:
>
> PROJECT_PATH=[PROJECT_PATH]
>
> Step 1 — Fetch posts:
>   Run: cd $PROJECT_PATH && make fetch
>   This creates posts.json in the project folder.
>
> Step 2 — Analyse:
>   Read $PROJECT_PATH/posts.json. It contains:
>   - "posts": list of recent Yellowdig posts (id, title, body, author, timestamp, tags)
>   - "interests": the student's topics of interest and engagement signal
>
>   Identify which posts are relevant to the student's interests. For each relevant post,
>   write a thoughtful 2-4 sentence comment they could post (substantive, collegial, adds
>   value — not "Great post!"). Connect to MBA topics where possible.
>
>   Save your analysis to $PROJECT_PATH/analysis.json with EXACTLY this structure:
>   {
>     "digest_title": "short punchy title for today's digest",
>     "summary": "2-3 sentence overview of what's trending in the community",
>     "relevant_posts": [
>       {
>         "id": "post id from posts.json",
>         "title": "post title",
>         "author": "author name",
>         "timestamp": "ISO timestamp",
>         "web_url": "",
>         "relevance_reason": "1-sentence explanation of why this matches the student's interests",
>         "suggested_comment": "the full comment text ready to copy-paste"
>       }
>     ]
>   }
>
> Step 3 — Publish:
>   Run: cd $PROJECT_PATH && make publish
>   This creates the Notion digest page.
>
> After completing, tell me the Notion page URL from the script output.
> If any step fails, save the error to $PROJECT_PATH/error_log.txt and notify me.
> ```

---

## Customising your interests

Edit the `interests` section in `config.json`:

- **`topics`** — list of subjects you care about. Be specific: "Porter's Five Forces and competitive strategy" works better than just "strategy".
- **`engagement_signal`** — a short description of what kinds of discussions you typically jump into. Update this every few weeks as your interests evolve.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `401 Unauthorized` from Yellowdig | Check your `api_key` and that you're an Owner/Facilitator of the community |
| `400 Bad Request` from Yellowdig | Check your `network` and `community` values in `config.json` |
| Notion page not created | Make sure your integration is connected to the parent page (step 2 above) |
| `analysis.json` missing keys | Check the Cowork output — Claude must write all required fields before `make publish` runs |
| No posts found | The community may be quiet, or `lookback_hours` may need to be increased in config.json |

---

## File structure

```
mbs-yellowdig-cowork/
├── fetch_posts.py        ← Step 1: fetches posts → posts.json
├── publish_digest.py     ← Step 2: reads analysis.json → creates Notion page
├── posts.json            ← generated by make fetch (gitignored)
├── analysis.json         ← written by Claude Cowork (gitignored)
├── config.json           ← your secrets (never share/commit this)
├── config.example.json   ← template (safe to share)
├── requirements.txt
├── Makefile
└── README.md
```

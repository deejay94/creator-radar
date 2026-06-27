# CreatorRadar V1 — CLI Reddit Opportunity Radar

A minimal CLI prototype that fetches opportunities from **Reddit** and **Upwork**, and stores normalized opportunities in SQLite.

```
Connectors → normalize → SQLite   |   Reddit → feed filters → console
```

No Notion, no Slack, no web server. **AI classification and scoring are disabled by default.**

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

| Variable | Required | Notes |
|----------|----------|-------|
| `APIFY_API_TOKEN` | Yes | [console.apify.com/account/integrations](https://console.apify.com/account/integrations) |
| `OPENAI_API_KEY` | No | Only if using AI — install with `pip install -r requirements-ai.txt` |
| `APIFY_ACTOR_ID` | No | Defaults to `labrat011/reddit-scraper` (HTTP + old.reddit.com; avoids Puppeteer 403s) |
| `UPWORK_SESSION_PATH` | No | Defaults to `~/.creator-radar/upwork-session.json` |
| `RADAR_AI_ENABLED` | No | Master AI switch (default: off) |

Reddit shut down unauthenticated `.json` access in 2026. CreatorRadar uses Apify's `labrat011/reddit-scraper`, which parses `old.reddit.com` with TLS impersonation instead of the Puppeteer-based actor that often gets 403-blocked.

By default, **r/UGCCreators** is searched for posts with flair **Collab Request 🤝**; **r/ugc** scrapes recent posts (no flair filter — that subreddit doesn't use the same tags). Heuristic feed filters still apply to both. Override with `--flair` or `--subreddit`.

For Upwork, install Playwright's Chromium browser after `pip install`:

```bash
playwright install chromium
```

## Connector architecture

Platform sources implement a shared `OpportunityConnector` interface (`health_check`, `search`, `extract`, `normalize`) under `radar/connectors/`. The Upwork connector is the first implementation; Reddit and other platforms will plug into the same contract later.

## Run

```bash
python -m radar
```

Options:

```bash
python -m radar --limit 25
python -m radar --subreddit UGCCreators
python -m radar --subreddit ugc
python -m radar --subreddit UGCCreators,ugc
python -m radar --flair "Collab Request 🤝"
```

Each run starts an Apify actor job and typically takes 15–60 seconds.

By default (AI off), eligible posts are printed as plain listings (title, link, flair, author) after heuristic feed filters. Set `RADAR_AI_ENABLED=true` to restore GPT A/B/C classification.

### Upwork session auth

Log in once via a **real Chrome window** (default). Upwork often blocks Playwright's bundled Chromium with a CAPTCHA loop — Chrome + a persistent profile avoids that in most cases.

```bash
playwright install chromium   # still needed for headless status checks
python -m radar upwork login  # uses Google Chrome by default
python -m radar upwork status
```

Options:

```bash
python -m radar upwork login --browser chrome     # recommended (default)
python -m radar upwork login --browser chromium   # fallback if Chrome is not installed
python -m radar upwork import-session /path/to/storage_state.json
```

**If CAPTCHA keeps saying "verify you're human":**

1. Make sure [Google Chrome](https://www.google.com/chrome/) is installed, then run `python -m radar upwork login` (defaults to Chrome).
2. Turn off VPN/proxy and retry on a normal home network.
3. Complete login slowly in the opened window — don't switch away during CAPTCHA.
4. If it still loops, log in manually in your normal browser, export a Playwright `storage_state` JSON, then run `python -m radar upwork import-session <file>`.

The login browser keeps a persistent profile at `~/.creator-radar/upwork-browser-profile`. The saved session for headless checks is at `~/.creator-radar/upwork-session.json`.

When authenticated, `status` prints:

```
✔ Upwork session valid
User: Dee Jay
Status: authenticated
```

If the session is missing or expired:

```
✗ Upwork session invalid
Status: reauthentication required
Run: python -m radar upwork login
```

### Upwork job search

Search Upwork with your saved session. Prints one normalized `Opportunity` JSON object per line.

```bash
python -m radar upwork search --query UGC --limit 10
python -m radar upwork search --limit 5          # runs all default PRD queries
python -m radar upwork search --query UGC --debug  # saves screenshot if 0 jobs
```

Search uses **visible Chrome by default** (same as login). Use `--headless` only if you know it works for your account.

Default search terms (when `--query` is omitted): UGC, User Generated Content, TikTok Creator, TikTok Content, Instagram Creator, Content Creator, Product Video, Product Review, Video Testimonial, Social Media Content.

Override defaults via environment (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `RADAR_UPWORK_SEARCH_QUERIES` | Comma-separated query list (overrides defaults) |
| `RADAR_UPWORK_QUERIES_FILE` | Path to file with one query per line (`#` comments OK) |
| `RADAR_UPWORK_LIMIT_PER_QUERY` | Max jobs per query when `--limit` is omitted (default: 20) |

Precedence: `--query` / `--limit` CLI flags > env vars > built-in defaults. Env query list beats query file.

Logs (queries run, jobs found, extraction errors) go to stderr. After a multi-query run, stderr includes a summary like `Search summary: queries=10, total_found=45, unique=38`. JSON output goes to stdout — pipe to a file if needed:

```bash
python -m radar upwork search --query UGC --limit 5 > opportunities.jsonl
```

### Import to SQLite

Persist opportunities (with deduplication) to `~/.creator-radar/opportunities.db`:

```bash
python -m radar import --platform upwork --query UGC --limit 5
python -m radar import --platform reddit --limit 10
```

Re-running import skips duplicates by:

1. `platform + external_id` (primary key)
2. Exact URL match
3. Similar title (≥92% match, same platform)
4. Similar description (≥88% match when both are substantial)

Duplicates within the same import run are caught before hitting the database.

Override database path with `RADAR_DB_PATH` in `.env`.

### AI features (disabled by default)

GPT-based features are **off by default** — no OpenAI calls on import or Reddit scan unless you opt in.

| Feature | When enabled |
|---------|----------------|
| Reddit scan (`python -m radar`) | A/B/C tier classification via GPT |
| Import (`python -m radar import`) | 0–100 opportunity scoring on insert |
| Score command (`python -m radar score`) | Score existing DB rows |

Enable all AI features:

```bash
export RADAR_AI_ENABLED=true
# OPENAI_API_KEY required — get one at platform.openai.com/api-keys
```

Per-feature overrides (optional):

```bash
export RADAR_AI_SCORING=true          # import scoring only
export RADAR_AI_CLASSIFICATION=true   # Reddit classification only
```

When AI is enabled:

```bash
python -m radar import --platform upwork --query UGC --limit 5
python -m radar import --platform upwork --query UGC --limit 5 --no-score  # force skip scoring
python -m radar score --platform upwork --limit 25
python -m radar list --platform upwork --min-score 80
```

When AI is disabled (default), import stores opportunities without scores and `python -m radar score` exits with a message.

## Output

### With AI disabled (default)

Each eligible post:

```
Title: ...
Link: https://reddit.com/r/UGCCreators/comments/...
Flair: Collab Request 🤝
Author: u/brandname
```

Summary:

```
Fetched 25 · filtered out 3 · Showing 5 "Collab Request 🤝" posts (AI classification disabled)
```

### With AI enabled (`RADAR_AI_ENABLED=true`)

For each actionable opportunity (tiers A, B, or C):

```
🔥 TIER A OPPORTUNITY (TIER 1 NICHE)

Title: ...
Niche: ...
Niche Tier: 1
Opportunity Tier: A

Link: https://reddit.com/r/UGCCreators/comments/...
Contact: DM u/brandname

Reason: ...
```

Ends with a summary:

```
Scanned 5 "Collab Request 🤝" posts · 4 opportunities (2 A, 1 B, 1 C)
```

Every opportunity includes a clickable `https://reddit.com/...` link.

## Classification (AI enabled only)

When `RADAR_AI_ENABLED=true`, posts are filtered **before** the AI call to cut cost and noise:

- Job seeker posts (creators looking for work, not brands hiring)
- Memes and discussion threads
- "How do I…" / advice-seeking posts
- Meta subreddit content
- Posts older than 72 hours

The AI assigns:

- **Niche** + **Niche Tier** (1 = highest priority niches like fitness, SaaS, LGBTQ+; 2 = lifestyle, beauty; 3 = gaming, pets, etc.)
- **Opportunity Tier**: `A` (hire now), `B` (pitch later), `C` (weak signal), or `REJECT` (skipped in output)

## Limitations

- Only works for **public** subreddits
- Each scan incurs Apify usage (~$3.40 per 1,000 results on the default actor)
- Actor runs are slower than a direct API call
- Reddit anti-bot changes may occasionally break the scraper until Apify updates the actor

## Render worker (Reddit → Slack)

A Node.js worker fetches Reddit opportunities via the Python CLI, deduplicates with `SeenOpportunityStore` (`seen_opportunities.json`), sends **one batch Slack message** for new opportunities only, and persists seen keys after a successful send. Render Cron triggers it externally — no internal scheduler.

Requires **Node 18+**, **Python 3**, and `bash build.sh` (or `npm install` locally).

### Local development (recommended)

Dedup state lives in **`seen_opportunities.json`** in the repo root (gitignored). No S3/R2 needed locally.

1. Copy env vars into `.env` (`APIFY_API_TOKEN`, `SLACK_WEBHOOK_URL`)
2. Install deps:

```bash
bash build.sh
```

3. Run the worker:

```bash
node worker.js
```

4. Run again — same posts should log `No new opportunities found.` and skip Slack. Check `seen_opportunities.json` for keys like `"reddit:abc123": true`.

To reset dedup locally, delete the file:

```bash
rm seen_opportunities.json
```

### Dedup architecture

- **`SeenOpportunityStore`** ([`seenOpportunityStore.js`](seenOpportunityStore.js)) — only module that reads/writes the JSON store
- Keys: `platform:external_id` (e.g. `reddit:abc123`)
- Opportunities are marked seen **only after Slack succeeds**
- Storage is swappable later (Redis/Postgres) without changing notification logic

**Env vars:** `APIFY_API_TOKEN`, `SLACK_WEBHOOK_URL`, optional `RADAR_REDDIT_SUBREDDITS`, optional `SEEN_OPPORTUNITIES_PATH` (default `seen_opportunities.json`).

Manual fetch:

```bash
python -m radar notify --platform reddit --subreddit UGCCreators,ugc
```

Worker tests:

```bash
npm run test:worker
```

### Render Cron setup

**Without S3/R2 (current):** each cron run starts with an empty seen store, so the same Reddit posts may be sent to Slack again on every run. Use local `seen_opportunities.json` for development; add S3/R2 env vars later for production dedup.

#### Create Cron Job on Render

1. Render Dashboard → **New** → **Cron Job**
2. Connect your GitHub repo
3. Settings:

| Field | Value |
|-------|-------|
| Name | `creator-radar-notify` |
| Branch | `main` |
| Runtime | **Node** |
| Build Command | `bash build.sh` |
| Schedule | `*/30 * * * *` |
| Command | `node worker.js` |

4. **Environment variables** (minimum for now):

| Variable | Required |
|----------|----------|
| `APIFY_API_TOKEN` | Yes |
| `SLACK_WEBHOOK_URL` | Yes |
| `RADAR_REDDIT_SUBREDDITS` | Optional |

Do **not** set S3/R2 vars until you want cross-run dedup on Render.

5. **Manual Trigger** → check logs for `Worker started` … `Worker finished`

## Tests

```bash
pytest
npm run test:worker
```

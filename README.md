# CreatorRadar V1 — CLI Reddit Opportunity Radar

A minimal CLI prototype that fetches posts from **r/UGCCreators** via [Apify's Reddit Scraper](https://apify.com/labrat011/reddit-scraper), classifies them with GPT-4o-mini, and prints actionable creator opportunities to your terminal.

```
Apify Reddit Scraper → AI classification → console output
```

No database, no Notion, no Slack, no web server.

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
| `OPENAI_API_KEY` | Yes | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `APIFY_API_TOKEN` | Yes | [console.apify.com/account/integrations](https://console.apify.com/account/integrations) |
| `APIFY_ACTOR_ID` | No | Defaults to `labrat011/reddit-scraper` (HTTP + old.reddit.com; avoids Puppeteer 403s) |
| `UPWORK_SESSION_PATH` | No | Defaults to `~/.creator-radar/upwork-session.json` |

Reddit shut down unauthenticated `.json` access in 2026. CreatorRadar uses Apify's `labrat011/reddit-scraper`, which parses `old.reddit.com` with TLS impersonation instead of the Puppeteer-based actor that often gets 403-blocked.

By default, only posts with a flair containing **Collab Request 🤝** are scanned. Override with `--flair`.

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
python -m radar --flair "Collab Request 🤝"
```

Each run starts an Apify actor job and typically takes 15–60 seconds.

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

Logs (queries run, jobs found, extraction errors) go to stderr. JSON output goes to stdout — pipe to a file if needed:

```bash
python -m radar upwork search --query UGC --limit 5 > opportunities.jsonl
```

## Output

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

## Classification

Posts are filtered **before** the AI call to cut cost and noise:

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

## Tests

```bash
pytest
```

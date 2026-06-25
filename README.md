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

Reddit shut down unauthenticated `.json` access in 2026. CreatorRadar uses Apify's `labrat011/reddit-scraper`, which parses `old.reddit.com` with TLS impersonation instead of the Puppeteer-based actor that often gets 403-blocked.

By default, only posts with a flair containing **Collab Request 🤝** are scanned. Override with `--flair`.

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

## Output

For each actionable opportunity (tiers A, B, or C):

```
🔥 OPPORTUNITY FOUND

Title: ...
Niche: ...
Tier: A
Niche Tier: 1
Link: https://reddit.com/r/UGCCreators/comments/...
Reason: ...
Contact: DM — u/brandname
```

Ends with a summary:

```
Scanned 5 "Collab Request 🤝" posts · 4 opportunities (2 A, 1 B, 1 C)
```

Every opportunity includes a clickable `https://reddit.com/...` link.

## Classification

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

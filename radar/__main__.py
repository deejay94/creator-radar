"""CLI entry: python -m radar"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from radar.classify import classify_post
from radar.output import print_opportunity, print_summary
from radar.reddit import RedditClient, RedditConfigError


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Scan r/UGCCreators for creator opportunities")
    parser.add_argument("--limit", type=int, default=25, help="Number of posts to fetch (default: 25)")
    parser.add_argument("--subreddit", default="UGCCreators", help="Subreddit to scan (default: UGCCreators)")
    args = parser.parse_args()

    try:
        client = RedditClient()
        posts = client.fetch_posts(subreddit=args.subreddit, limit=args.limit)
    except RedditConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Failed to fetch Reddit posts: {exc}", file=sys.stderr)
        print(
            "If the Apify actor failed, verify APIFY_API_TOKEN at "
            "https://console.apify.com/account/integrations",
            file=sys.stderr,
        )
        return 1

    if not posts:
        print("No posts found.")
        return 0

    results = []
    for post in posts:
        try:
            result = classify_post(post)
            results.append(result)
            if result.is_actionable():
                print_opportunity(result)
        except Exception as exc:
            print(f"Skipped post (classification error): {post.title[:60]} — {exc}", file=sys.stderr)

    print_summary(len(posts), results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

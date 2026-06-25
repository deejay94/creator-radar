"""CLI entry: python -m radar"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from radar.classify import classify_post
from radar.filters import filter_posts_for_classification
from radar.output import print_opportunity, print_summary
from radar.reddit import DEFAULT_FLAIR_FILTER, RedditClient, RedditConfigError


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Scan r/UGCCreators for creator opportunities")
    parser.add_argument("--limit", type=int, default=25, help="Number of posts to fetch (default: 25)")
    parser.add_argument("--subreddit", default="UGCCreators", help="Subreddit to scan (default: UGCCreators)")
    parser.add_argument(
        "--flair",
        default=DEFAULT_FLAIR_FILTER,
        help=f'Only include posts whose flair contains this text (default: "{DEFAULT_FLAIR_FILTER}")',
    )
    args = parser.parse_args()

    try:
        client = RedditClient()
        posts = client.fetch_posts(
            subreddit=args.subreddit,
            limit=args.limit,
            flair_filter=args.flair,
        )
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
        print(f'No posts found with flair matching "{args.flair}".')
        return 0

    eligible, skipped = filter_posts_for_classification(posts)
    for post, reason in skipped:
        print(f"Filtered (pre-AI): {post.title[:60]} — {reason}", file=sys.stderr)

    if not eligible:
        print(f'No posts remained after feed filters ({len(skipped)} skipped).')
        return 0

    results = []
    for post in eligible:
        try:
            result = classify_post(post)
            results.append(result)
            if result.is_actionable():
                print_opportunity(result)
        except Exception as exc:
            print(f"Skipped post (classification error): {post.title[:60]} — {exc}", file=sys.stderr)

    print_summary(
        scanned=len(eligible),
        results=results,
        flair_filter=args.flair,
        fetched=len(posts),
        filtered_out=len(skipped),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

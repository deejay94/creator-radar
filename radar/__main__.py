"""CLI entry: python -m radar"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from radar.ai_config import is_ai_classification_enabled
from radar.classify import classify_post
from radar.filters import filter_posts_for_classification
from radar.import_cmd import main as import_main
from radar.list_cmd import main as list_main
from radar.notify_cmd import main as notify_main
from radar.output import print_opportunity, print_plain_summary, print_reddit_post, print_summary
from radar.reddit import DEFAULT_FLAIR_FILTER, RedditClient, RedditConfigError
from radar.score_cmd import main as score_main
from radar.upwork.cli import main as upwork_main


def run_reddit(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Scan Reddit subreddits for creator opportunities (default: UGCCreators, ugc)"
    )
    parser.add_argument("--limit", type=int, default=25, help="Number of posts to fetch per subreddit (default: 25)")
    parser.add_argument(
        "--subreddit",
        default=None,
        help="Subreddit(s) to scan, comma-separated (default: UGCCreators, ugc)",
    )
    parser.add_argument(
        "--flair",
        default=DEFAULT_FLAIR_FILTER,
        help=f'Only include posts whose flair contains this text (default: "{DEFAULT_FLAIR_FILTER}")',
    )
    args = parser.parse_args(argv)

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

    if not is_ai_classification_enabled():
        for post in eligible:
            print_reddit_post(post)
        print_plain_summary(
            shown=len(eligible),
            flair_filter=args.flair,
            fetched=len(posts),
            filtered_out=len(skipped),
        )
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


def main() -> int:
    load_dotenv()

    argv = sys.argv[1:]
    if not argv:
        return run_reddit(argv)

    command = argv[0]
    if command == "upwork":
        return upwork_main(argv[1:])
    if command == "import":
        return import_main(argv[1:])
    if command == "score":
        return score_main(argv[1:])
    if command == "list":
        return list_main(argv[1:])
    if command == "notify":
        return notify_main(argv[1:])

    return run_reddit(argv)


if __name__ == "__main__":
    raise SystemExit(main())

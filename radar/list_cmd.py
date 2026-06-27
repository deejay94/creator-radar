"""List scored opportunities from the database."""

from __future__ import annotations

import argparse
import sys

from radar.db.repository import OpportunityRepository
from radar.scoring.output import format_scored_opportunity


def cmd_list(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List opportunities from the database")
    parser.add_argument("--platform", choices=["upwork", "reddit"], help="Filter by platform")
    parser.add_argument(
        "--min-score",
        type=int,
        help="Only show opportunities with AI score >= this value",
    )
    parser.add_argument("--limit", type=int, default=25, help="Max rows to show")
    args = parser.parse_args(argv)

    repo = OpportunityRepository()
    try:
        rows = repo.list_opportunities(
            platform=args.platform,
            min_score=args.min_score,
            limit=args.limit,
        )
        if not rows:
            print("No opportunities found.")
            return 0

        for row_id, opportunity in rows:
            print(format_scored_opportunity(row_id, opportunity))
            print()
    finally:
        repo.close()

    return 0


def main(argv: list[str] | None = None) -> int:
    return cmd_list(argv)

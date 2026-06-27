"""Score opportunities in the database with AI."""

from __future__ import annotations

import argparse
import logging
import sys

from radar.db.repository import OpportunityRepository
from radar.scoring.config import is_ai_scoring_enabled
from radar.scoring.scorer import apply_score, score_opportunity


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )


def score_opportunities_in_db(
    repo: OpportunityRepository,
    *,
    platform: str | None = None,
    limit: int = 50,
) -> tuple[int, int]:
    rows = repo.list_opportunities(platform=platform, unscored_only=True, limit=limit)
    scored = 0
    errors = 0

    for row_id, opportunity in rows:
        try:
            result = score_opportunity(opportunity)
            scored_opp = apply_score(opportunity, result)
            repo.update_opportunity(row_id, scored_opp)
            scored += 1
            logging.info(
                "Scored id=%d score=%d priority=%s — %s",
                row_id,
                result.score,
                result.priority,
                opportunity.title[:80],
            )
        except Exception as exc:
            errors += 1
            logging.warning("Scoring failed for id=%d: %s", row_id, exc)

    return scored, errors


def cmd_score(argv: list[str] | None = None) -> int:
    _configure_logging()

    if not is_ai_scoring_enabled():
        print(
            "AI scoring is disabled. Set RADAR_AI_ENABLED=true to enable.",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(description="Score unscored opportunities in the database")
    parser.add_argument("--platform", choices=["upwork", "reddit"], help="Filter by platform")
    parser.add_argument("--limit", type=int, default=50, help="Max opportunities to score")
    args = parser.parse_args(argv)

    repo = OpportunityRepository()
    try:
        scored, errors = score_opportunities_in_db(
            repo,
            platform=args.platform,
            limit=args.limit,
        )
    finally:
        repo.close()

    print(f"Scoring complete: {scored} scored, {errors} errors")
    return 0 if errors == 0 else 1


def main(argv: list[str] | None = None) -> int:
    return cmd_score(argv)

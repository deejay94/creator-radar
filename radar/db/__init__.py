"""Database layer for persisted opportunities."""

from radar.db.config import resolve_db_path
from radar.db.dedup import DedupResult, DedupSession, check_duplicate, check_duplicate_in_repo
from radar.db.repository import OpportunityRepository

__all__ = [
    "DedupResult",
    "DedupSession",
    "OpportunityRepository",
    "check_duplicate",
    "check_duplicate_in_repo",
    "resolve_db_path",
]

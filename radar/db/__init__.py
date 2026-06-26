"""Database layer for persisted opportunities."""

from radar.db.config import resolve_db_path
from radar.db.dedup import DedupResult, check_duplicate
from radar.db.repository import OpportunityRepository

__all__ = [
    "DedupResult",
    "OpportunityRepository",
    "check_duplicate",
    "resolve_db_path",
]

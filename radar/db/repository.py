"""SQLite persistence for opportunities."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from radar.connectors.types import Opportunity
from radar.db.config import resolve_db_path
from radar.db.schema import SCHEMA_SQL


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bool_to_db(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


def _bool_from_db(value: Optional[int]) -> Optional[bool]:
    if value is None:
        return None
    return bool(value)


class OpportunityRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or resolve_db_path()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _init_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def exists_by_platform_id(self, platform: str, external_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM opportunities WHERE platform = ? AND external_id = ? LIMIT 1",
            (platform, external_id),
        ).fetchone()
        return row is not None

    def exists_by_url(self, url: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM opportunities WHERE url = ? LIMIT 1",
            (url,),
        ).fetchone()
        return row is not None

    def insert(self, opportunity: Opportunity) -> int:
        now = _utc_now_iso()
        posted_at = opportunity.posted_at.isoformat() if opportunity.posted_at else None
        cursor = self._conn.execute(
            """
            INSERT INTO opportunities (
                platform, external_id, title, description, url, budget, hourly,
                skills_json, posted_at, client_rating, client_spend, payment_verified,
                proposal_count, ai_score, priority, reasoning, status, metadata_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity.platform,
                opportunity.external_id,
                opportunity.title,
                opportunity.description,
                opportunity.url,
                opportunity.budget,
                _bool_to_db(opportunity.hourly),
                json.dumps(opportunity.skills),
                posted_at,
                opportunity.client_rating,
                opportunity.client_spend,
                _bool_to_db(opportunity.payment_verified),
                opportunity.proposal_count,
                opportunity.ai_score,
                opportunity.priority,
                opportunity.reasoning,
                opportunity.status,
                json.dumps(opportunity.metadata),
                now,
                now,
            ),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def count(self, platform: str | None = None) -> int:
        if platform:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM opportunities WHERE platform = ?",
                (platform,),
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) AS c FROM opportunities").fetchone()
        return int(row["c"]) if row else 0

    def get_by_platform_id(self, platform: str, external_id: str) -> Opportunity | None:
        row = self._conn.execute(
            "SELECT * FROM opportunities WHERE platform = ? AND external_id = ?",
            (platform, external_id),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_opportunity(row)

    def _row_to_opportunity(self, row: sqlite3.Row) -> Opportunity:
        posted_at = None
        if row["posted_at"]:
            posted_at = datetime.fromisoformat(row["posted_at"])
        return Opportunity(
            platform=row["platform"],
            external_id=row["external_id"],
            title=row["title"],
            description=row["description"],
            url=row["url"],
            budget=row["budget"],
            hourly=_bool_from_db(row["hourly"]),
            skills=json.loads(row["skills_json"] or "[]"),
            posted_at=posted_at,
            client_rating=row["client_rating"],
            client_spend=row["client_spend"],
            payment_verified=_bool_from_db(row["payment_verified"]),
            proposal_count=row["proposal_count"],
            ai_score=row["ai_score"],
            priority=row["priority"],
            reasoning=row["reasoning"],
            status=row["status"],
            metadata=json.loads(row["metadata_json"] or "{}"),
        )

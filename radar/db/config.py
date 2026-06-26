"""Database path configuration."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_DIR = Path.home() / ".creator-radar"
DEFAULT_DB_FILENAME = "opportunities.db"


def resolve_db_path() -> Path:
    configured = os.environ.get("RADAR_DB_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_DB_DIR / DEFAULT_DB_FILENAME

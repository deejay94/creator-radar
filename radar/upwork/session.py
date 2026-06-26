"""Upwork session persistence for Playwright storage_state."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_SESSION_DIR = Path.home() / ".creator-radar"
DEFAULT_SESSION_FILENAME = "upwork-session.json"


class UpworkSessionError(ValueError):
    """Raised when Upwork session file operations fail."""


def resolve_session_path() -> Path:
    configured = os.environ.get("UPWORK_SESSION_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()
    return DEFAULT_SESSION_DIR / DEFAULT_SESSION_FILENAME


def session_exists(path: Path | None = None) -> bool:
    target = path or resolve_session_path()
    return target.is_file()


def validate_storage_state(state: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise UpworkSessionError("Session file must contain a JSON object.")
    if "cookies" not in state or not isinstance(state["cookies"], list):
        raise UpworkSessionError(
            "Session file must be Playwright storage_state JSON with a 'cookies' array. "
            "Export from a logged-in browser session or run: python -m radar upwork login"
        )


def load_session_state(path: Path | None = None) -> dict[str, Any]:
    target = path or resolve_session_path()
    if not target.is_file():
        raise UpworkSessionError(f"No Upwork session saved at {target}.")
    try:
        state = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UpworkSessionError(f"Upwork session file is invalid: {target}") from exc
    if path is None:
        validate_storage_state(state)
    return state


def save_session_state(state: dict[str, Any], path: Path | None = None) -> Path:
    target = path or resolve_session_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return target

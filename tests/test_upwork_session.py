import json
from pathlib import Path

import pytest

from radar.upwork.session import (
    UpworkSessionError,
    load_session_state,
    resolve_session_path,
    save_session_state,
    session_exists,
    validate_storage_state,
)


def test_resolve_session_path_default(monkeypatch):
    monkeypatch.delenv("UPWORK_SESSION_PATH", raising=False)
    path = resolve_session_path()
    assert path.name == "upwork-session.json"
    assert path.parent.name == ".creator-radar"


def test_resolve_session_path_from_env(monkeypatch, tmp_path):
    custom = tmp_path / "custom-session.json"
    monkeypatch.setenv("UPWORK_SESSION_PATH", str(custom))
    assert resolve_session_path() == custom


def test_save_and_load_session_state(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    monkeypatch.setenv("UPWORK_SESSION_PATH", str(session_file))
    state = {"cookies": [{"name": "session", "value": "abc", "domain": ".upwork.com"}]}

    saved = save_session_state(state)
    assert saved == session_file
    assert session_exists()
    assert load_session_state() == state


def test_load_session_state_missing_file(tmp_path, monkeypatch):
    session_file = tmp_path / "missing.json"
    monkeypatch.setenv("UPWORK_SESSION_PATH", str(session_file))

    with pytest.raises(UpworkSessionError, match="No Upwork session saved"):
        load_session_state()


def test_validate_storage_state_requires_cookies():
    with pytest.raises(UpworkSessionError, match="cookies"):
        validate_storage_state({})

    validate_storage_state({"cookies": []})


def test_load_session_state_invalid_shape(tmp_path, monkeypatch):
    session_file = tmp_path / "bad-shape.json"
    session_file.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("UPWORK_SESSION_PATH", str(session_file))

    with pytest.raises(UpworkSessionError, match="cookies"):
        load_session_state()

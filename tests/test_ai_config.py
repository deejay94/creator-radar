"""Tests for central AI feature flags."""

from __future__ import annotations

import pytest

from radar.ai_config import (
    is_ai_classification_enabled,
    is_ai_enabled,
    is_ai_scoring_enabled,
)


@pytest.fixture(autouse=True)
def clear_ai_env(monkeypatch):
    monkeypatch.delenv("RADAR_AI_ENABLED", raising=False)
    monkeypatch.delenv("RADAR_AI_SCORING", raising=False)
    monkeypatch.delenv("RADAR_AI_CLASSIFICATION", raising=False)


def test_is_ai_enabled_defaults_false():
    assert is_ai_enabled() is False


def test_is_ai_enabled_true_via_env(monkeypatch):
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")
    assert is_ai_enabled() is True


def test_is_ai_scoring_enabled_defaults_false():
    assert is_ai_scoring_enabled() is False


def test_is_ai_scoring_follows_master_switch(monkeypatch):
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")
    assert is_ai_scoring_enabled() is True


def test_is_ai_scoring_override_beats_master(monkeypatch):
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")
    monkeypatch.setenv("RADAR_AI_SCORING", "false")
    assert is_ai_scoring_enabled() is False


def test_is_ai_classification_enabled_defaults_false():
    assert is_ai_classification_enabled() is False


def test_is_ai_classification_follows_master_switch(monkeypatch):
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")
    assert is_ai_classification_enabled() is True


def test_is_ai_classification_override_beats_master(monkeypatch):
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")
    monkeypatch.setenv("RADAR_AI_CLASSIFICATION", "false")
    assert is_ai_classification_enabled() is False

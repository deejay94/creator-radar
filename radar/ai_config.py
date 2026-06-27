"""Central AI feature flags for scoring and Reddit classification."""

from __future__ import annotations

import os

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})


def _parse_bool(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    return None


def is_ai_enabled() -> bool:
    """Master AI switch. Default: off."""
    value = os.environ.get("RADAR_AI_ENABLED", "false")
    parsed = _parse_bool(value)
    return parsed if parsed is not None else False


def is_ai_scoring_enabled() -> bool:
    """Import scoring (0–100). RADAR_AI_SCORING overrides; else follows RADAR_AI_ENABLED."""
    override = os.environ.get("RADAR_AI_SCORING")
    if override is not None and override.strip():
        parsed = _parse_bool(override)
        return parsed if parsed is not None else False
    return is_ai_enabled()


def is_ai_classification_enabled() -> bool:
    """Reddit A/B/C classification. RADAR_AI_CLASSIFICATION overrides; else follows RADAR_AI_ENABLED."""
    override = os.environ.get("RADAR_AI_CLASSIFICATION")
    if override is not None and override.strip():
        parsed = _parse_bool(override)
        return parsed if parsed is not None else False
    return is_ai_enabled()

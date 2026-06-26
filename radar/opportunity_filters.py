"""Content filters for normalized opportunities."""

from __future__ import annotations

import re
from typing import Optional

from radar.connectors.types import Opportunity

_FEMALE_PATTERNS = (
    re.compile(r"\bfemales?\b", re.I),
    re.compile(r"\bwomen\b", re.I),
    re.compile(r"\bwoman\b", re.I),
    re.compile(r"\bgirls?\b", re.I),
    re.compile(r"\bladies\b", re.I),
    re.compile(r"\blady\b", re.I),
)

# Matched only when no female-inclusive language is present.
_MALE_CREATOR_PATTERNS = (
    re.compile(r"\bmale\s+ugc\b", re.I),
    re.compile(r"\bmale\s+content\s+creators?\b", re.I),
    re.compile(r"\bmale\s+creators?\b", re.I),
    re.compile(r"\bmale\s+influencers?\b", re.I),
    re.compile(r"\bmale[- ]only\b", re.I),
    re.compile(r"\bmen\s+only\b", re.I),
    re.compile(r"\bman\s+only\b", re.I),
    re.compile(r"\bguys?\s+only\b", re.I),
    re.compile(r"\bmen\b.{0,40}\b(ugc|creators?|content\s+creators?|influencers?)\b", re.I),
    re.compile(r"\b(ugc|creators?|content\s+creators?|influencers?)\b.{0,40}\bmen\b", re.I),
    re.compile(r"\bmale\b.{0,40}\b(ugc|creators?|content\s+creators?|influencers?)\b", re.I),
    re.compile(r"\b(ugc|creators?|content\s+creators?|influencers?)\b.{0,40}\bmale\b", re.I),
)


def opportunity_text(opportunity: Opportunity) -> str:
    return f"{opportunity.title}\n{opportunity.description}"


def mentions_female(text: str) -> bool:
    return any(pattern.search(text) for pattern in _FEMALE_PATTERNS)


def mentions_male_creator_requirement(text: str) -> bool:
    return any(pattern.search(text) for pattern in _MALE_CREATOR_PATTERNS)


def get_male_only_creator_filter_reason(opportunity: Opportunity) -> Optional[str]:
    """Return a skip reason if the post targets male creators only."""
    text = opportunity_text(opportunity)
    if mentions_female(text):
        return None
    if mentions_male_creator_requirement(text):
        return "male-only UGC creator requirement"
    return None

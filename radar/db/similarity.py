"""Text normalization and similarity for deduplication."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

TITLE_SIMILARITY_THRESHOLD = 0.92
DESCRIPTION_SIMILARITY_THRESHOLD = 0.88
MIN_DESCRIPTION_COMPARE_LENGTH = 80


def normalize_dedup_text(text: str) -> str:
    lowered = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def text_similarity(left: str, right: str) -> float:
    normalized_left = normalize_dedup_text(left)
    normalized_right = normalize_dedup_text(right)
    if not normalized_left or not normalized_right:
        return 0.0
    return SequenceMatcher(None, normalized_left, normalized_right).ratio()


def titles_are_similar(left: str, right: str, threshold: float = TITLE_SIMILARITY_THRESHOLD) -> bool:
    return text_similarity(left, right) >= threshold


def descriptions_are_similar(
    left: str,
    right: str,
    threshold: float = DESCRIPTION_SIMILARITY_THRESHOLD,
) -> bool:
    normalized_left = normalize_dedup_text(left)
    normalized_right = normalize_dedup_text(right)
    if len(normalized_left) < MIN_DESCRIPTION_COMPARE_LENGTH:
        return False
    if len(normalized_right) < MIN_DESCRIPTION_COMPARE_LENGTH:
        return False
    return text_similarity(normalized_left, normalized_right) >= threshold

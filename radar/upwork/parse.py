"""Parse Upwork job page text into structured fields."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


def parse_job_id_from_url(url: str) -> str:
    match = re.search(r"~([0-9a-zA-Z]+)", url)
    if not match:
        raise ValueError(f"Could not parse Upwork job id from URL: {url}")
    return match.group(1)


def canonical_job_url(job_id: str) -> str:
    return f"https://www.upwork.com/jobs/~{job_id}"


def _first_match(pattern: str, text: str, flags: int = 0) -> str:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else ""


def _parse_bool(text: str, pattern: str) -> Optional[bool]:
    if re.search(pattern, text, re.IGNORECASE):
        return True
    return None


def parse_listing_fields(
    *,
    title: str,
    description: str,
    skills: list[str],
    features: list[str],
    page_text: str,
) -> dict[str, Any]:
    combined = " | ".join(features + [page_text])

    hourly: Optional[bool] = None
    if re.search(r"\bHourly\b", combined, re.IGNORECASE):
        hourly = True
    elif re.search(r"\bFixed[- ]?price\b", combined, re.IGNORECASE):
        hourly = False

    budget = _first_match(
        r"(\$[\d,]+(?:\.\d{2})?(?:\s*-\s*\$[\d,]+(?:\.\d{2})?)?(?:\s*/\s*hr)?)",
        combined,
    )
    if not budget:
        budget = _first_match(r"(Budget:\s*[^|]+)", combined)

    experience_level = _first_match(
        r"(Entry Level|Intermediate|Expert)\b",
        combined,
        re.IGNORECASE,
    )
    project_length = _first_match(
        r"(Less than \d+ month|\d+ to \d+ months|More than \d+ months|Less than \d+ week|\d+ to \d+ weeks)",
        combined,
        re.IGNORECASE,
    )
    proposal_count = _first_match(r"Proposals?:\s*(\d+(?:\s*to\s*\d+)?)", combined, re.IGNORECASE)
    if not proposal_count:
        proposal_count = _first_match(r"(\d+)\s+proposals?", combined, re.IGNORECASE)

    client_rating = _first_match(r"(\d(?:\.\d)?)\s*(?:of\s*5|stars?)", combined, re.IGNORECASE)
    client_spend = _first_match(r"(\$[\d,.]+[KMB]?\+?\s*(?:spent|total spent))", combined, re.IGNORECASE)
    if not client_spend:
        client_spend = _first_match(r"(\$[\d,.]+[KMB]?\+?\s+spent)", combined, re.IGNORECASE)

    client_country = _first_match(
        r"(?:Location|Country):\s*([A-Za-z][A-Za-z\s,.-]{1,40})",
        combined,
    )

    payment_verified = _parse_bool(combined, r"Payment\s+(?:method\s+)?verified")

    posted_time = _first_match(
        r"(Posted\s+(?:\d+\s+\w+\s+ago|yesterday|today|just now))",
        combined,
        re.IGNORECASE,
    )
    if not posted_time:
        posted_time = _first_match(r"(\d+\s+(?:minute|hour|day|week|month)s?\s+ago)", combined, re.IGNORECASE)

    category = _first_match(r"(?:Category):\s*([^|]+)", combined)
    subcategory = _first_match(r"(?:Subcategory):\s*([^|]+)", combined)

    return {
        "title": title,
        "description": description,
        "budget": budget,
        "hourly": hourly,
        "experience_level": experience_level,
        "client_rating": client_rating,
        "client_spend": client_spend,
        "client_country": client_country,
        "payment_verified": payment_verified,
        "proposal_count": proposal_count,
        "skills": skills,
        "posted_time": posted_time,
        "project_length": project_length,
        "category": category,
        "subcategory": subcategory,
        "features": features,
    }


def parse_posted_at(posted_time: str) -> Optional[datetime]:
    if not posted_time:
        return None

    text = posted_time.lower().strip()
    now = datetime.now(timezone.utc)

    if "just now" in text or "today" in text:
        return now
    if "yesterday" in text:
        return now - timedelta(days=1)

    match = re.search(r"(\d+)\s+(minute|hour|day|week|month)s?\s+ago", text)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)
    deltas = {
        "minute": timedelta(minutes=amount),
        "hour": timedelta(hours=amount),
        "day": timedelta(days=amount),
        "week": timedelta(weeks=amount),
        "month": timedelta(days=amount * 30),
    }
    return now - deltas[unit]

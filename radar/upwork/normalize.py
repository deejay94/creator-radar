"""Map Upwork raw listings to shared Opportunity objects."""

from __future__ import annotations

from radar.connectors.types import Opportunity, RawListing
from radar.upwork.parse import parse_posted_at


def normalize_upwork_listing(raw: RawListing) -> Opportunity:
    payload = raw.payload

    skills = payload.get("skills") or []
    if not isinstance(skills, list):
        skills = []

    posted_time = str(payload.get("posted_time") or "")
    metadata = {
        "experience_level": payload.get("experience_level") or "",
        "client_country": payload.get("client_country") or "",
        "posted_time": posted_time,
        "project_length": payload.get("project_length") or "",
        "category": payload.get("category") or "",
        "subcategory": payload.get("subcategory") or "",
        "search_query": payload.get("search_query") or "",
        "job_id": payload.get("job_id") or raw.external_id,
    }

    return Opportunity(
        platform="upwork",
        external_id=raw.external_id,
        title=raw.title or str(payload.get("title") or ""),
        description=raw.description,
        url=raw.url,
        budget=str(payload.get("budget") or ""),
        hourly=payload.get("hourly"),
        posted_at=parse_posted_at(posted_time),
        skills=[str(skill) for skill in skills if skill],
        client_rating=str(payload.get("client_rating") or ""),
        client_spend=str(payload.get("client_spend") or ""),
        payment_verified=payload.get("payment_verified"),
        proposal_count=str(payload.get("proposal_count") or ""),
        metadata=metadata,
    )

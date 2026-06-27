"""Map Upwork raw listings to shared Opportunity objects."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from radar.connectors.types import Opportunity, RawListing
from radar.upwork.errors import NormalizationError
from radar.upwork.extract_types import UpworkExtractedJob
from radar.upwork.parse import parse_posted_at


def _validate_extracted_payload(raw: RawListing) -> UpworkExtractedJob:
    try:
        return UpworkExtractedJob.model_validate(raw.payload)
    except ValidationError as exc:
        raise NormalizationError(f"Invalid Upwork extraction payload: {exc}") from exc


def normalize_upwork_listing(raw: RawListing) -> Opportunity:
    """Map validated UpworkExtractedJob fields to the shared Opportunity schema."""
    extracted = _validate_extracted_payload(raw)

    external_id = (raw.external_id or extracted.job_id or "").strip()
    title = (raw.title or extracted.title or "").strip()
    description = (raw.description or extracted.description or "").strip()
    url = (raw.url or extracted.url or "").strip()

    if not external_id:
        raise NormalizationError("Missing external_id / job_id for Upwork listing")
    if not title:
        raise NormalizationError(f"Missing title for Upwork listing {external_id}")

    posted_time = extracted.posted_time or str(raw.payload.get("posted_time") or "")
    metadata = {
        "experience_level": extracted.experience_level,
        "client_country": extracted.client_country,
        "posted_time": posted_time,
        "project_length": extracted.project_length,
        "category": extracted.category,
        "subcategory": extracted.subcategory,
        "search_query": extracted.search_query,
        "job_id": extracted.job_id or external_id,
    }

    return Opportunity(
        platform="upwork",
        external_id=external_id,
        title=title,
        description=description,
        url=url,
        budget=extracted.budget,
        hourly=extracted.hourly,
        posted_at=parse_posted_at(posted_time),
        skills=[str(skill) for skill in extracted.skills if skill],
        client_rating=extracted.client_rating,
        client_spend=extracted.client_spend,
        payment_verified=extracted.payment_verified,
        proposal_count=extracted.proposal_count,
        metadata=metadata,
    )


def opportunity_to_prd_dict(opportunity: Opportunity) -> dict[str, Any]:
    """Stable PRD-shaped dict for CLI JSON output."""
    return {
        "platform": opportunity.platform,
        "external_id": opportunity.external_id,
        "title": opportunity.title,
        "description": opportunity.description,
        "url": opportunity.url,
        "budget": opportunity.budget,
        "hourly": opportunity.hourly,
        "skills": opportunity.skills,
        "posted_at": opportunity.posted_at.isoformat() if opportunity.posted_at else None,
        "client_rating": opportunity.client_rating,
        "client_spend": opportunity.client_spend,
        "payment_verified": opportunity.payment_verified,
        "proposal_count": opportunity.proposal_count,
        "metadata": opportunity.metadata,
    }


def opportunity_to_prd_json(opportunity: Opportunity) -> str:
    return json.dumps(opportunity_to_prd_dict(opportunity), ensure_ascii=False)

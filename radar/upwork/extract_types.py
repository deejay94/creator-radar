"""Typed Upwork job extraction models."""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

PRD_EXTRACT_FIELDS = (
    "job_id",
    "title",
    "url",
    "description",
    "budget",
    "hourly",
    "experience_level",
    "client_rating",
    "client_spend",
    "client_country",
    "payment_verified",
    "proposal_count",
    "skills",
    "posted_time",
    "project_length",
    "category",
    "subcategory",
)


class UpworkExtractedJob(BaseModel):
    job_id: str = ""
    title: str = ""
    url: str = ""
    description: str = ""
    budget: str = ""
    hourly: Optional[bool] = None
    experience_level: str = ""
    client_rating: str = ""
    client_spend: str = ""
    client_country: str = ""
    payment_verified: Optional[bool] = None
    proposal_count: str = ""
    skills: list[str] = Field(default_factory=list)
    posted_time: str = ""
    project_length: str = ""
    category: str = ""
    subcategory: str = ""
    search_query: str = ""
    features: list[str] = Field(default_factory=list)

    def missing_prd_fields(self) -> list[str]:
        missing: list[str] = []
        for field_name in PRD_EXTRACT_FIELDS:
            value = getattr(self, field_name)
            if field_name in {"hourly", "payment_verified"}:
                if value is None:
                    missing.append(field_name)
                continue
            if field_name == "skills":
                if not value:
                    missing.append(field_name)
                continue
            if not value:
                missing.append(field_name)
        return missing

    def log_field_completeness(self) -> None:
        missing = self.missing_prd_fields()
        if missing:
            logger.debug(
                "Job %s missing PRD fields: %s",
                self.job_id or self.title[:40] or "unknown",
                ", ".join(missing),
            )


def merge_field_values(*values: Any) -> Any:
    """Return the first non-empty value."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            return value
        if isinstance(value, list):
            if value:
                return value
            continue
        if isinstance(value, str):
            if value.strip():
                return value.strip()
            continue
        return value
    return None


def merge_extracted_job(
    *,
    regex_job: UpworkExtractedJob,
    dom_fields: dict[str, Any] | None = None,
    tile_fields: dict[str, Any] | None = None,
    job_id: str = "",
    url: str = "",
    search_query: str = "",
) -> UpworkExtractedJob:
    dom = dom_fields or {}
    tile = tile_fields or {}

    skills = merge_field_values(dom.get("skills"), regex_job.skills, tile.get("skills")) or []
    if not isinstance(skills, list):
        skills = regex_job.skills

    hourly = merge_field_values(
        dom.get("hourly"),
        tile.get("hourly"),
        regex_job.hourly,
    )

    payment_verified = merge_field_values(
        dom.get("payment_verified"),
        tile.get("payment_verified"),
        regex_job.payment_verified,
    )

    return UpworkExtractedJob(
        job_id=job_id or regex_job.job_id,
        title=merge_field_values(dom.get("title"), regex_job.title, tile.get("title")) or "",
        url=url or regex_job.url,
        description=merge_field_values(dom.get("description"), regex_job.description) or "",
        budget=merge_field_values(dom.get("budget"), tile.get("budget"), regex_job.budget) or "",
        hourly=hourly,
        experience_level=merge_field_values(
            dom.get("experience_level"),
            tile.get("experience_level"),
            regex_job.experience_level,
        )
        or "",
        client_rating=merge_field_values(
            dom.get("client_rating"),
            tile.get("client_rating"),
            regex_job.client_rating,
        )
        or "",
        client_spend=merge_field_values(
            dom.get("client_spend"),
            tile.get("client_spend"),
            regex_job.client_spend,
        )
        or "",
        client_country=merge_field_values(
            dom.get("client_country"),
            tile.get("client_country"),
            regex_job.client_country,
        )
        or "",
        payment_verified=payment_verified,
        proposal_count=merge_field_values(
            dom.get("proposal_count"),
            tile.get("proposal_count"),
            regex_job.proposal_count,
        )
        or "",
        skills=[str(skill) for skill in skills if skill],
        posted_time=merge_field_values(
            dom.get("posted_time"),
            tile.get("posted_time"),
            regex_job.posted_time,
        )
        or "",
        project_length=merge_field_values(
            dom.get("project_length"),
            tile.get("project_length"),
            regex_job.project_length,
        )
        or "",
        category=merge_field_values(dom.get("category"), regex_job.category) or "",
        subcategory=merge_field_values(dom.get("subcategory"), regex_job.subcategory) or "",
        search_query=search_query or regex_job.search_query,
        features=regex_job.features,
    )

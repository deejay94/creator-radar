"""Tests for Upwork opportunity normalization."""

from __future__ import annotations

import json

import pytest

from radar.connectors.types import Opportunity, RawListing
from radar.upwork.errors import NormalizationError
from radar.upwork.normalize import (
    normalize_upwork_listing,
    opportunity_to_prd_dict,
    opportunity_to_prd_json,
)


def _sample_raw(**payload_overrides) -> RawListing:
    payload = {
        "job_id": "abc123",
        "title": "UGC Creator Needed",
        "url": "https://www.upwork.com/jobs/~abc123",
        "description": "Create TikTok videos for our brand.",
        "budget": "$500.00",
        "hourly": False,
        "skills": ["Video Editing", "TikTok"],
        "posted_time": "2 days ago",
        "experience_level": "Intermediate",
        "client_rating": "4.8",
        "client_spend": "$10K+ spent",
        "client_country": "United States",
        "payment_verified": True,
        "proposal_count": "5 to 10",
        "project_length": "1 to 3 months",
        "category": "Sales & Marketing",
        "subcategory": "Marketing Strategy",
        "search_query": "UGC",
    }
    payload.update(payload_overrides)
    return RawListing(
        platform="upwork",
        external_id="abc123",
        url="https://www.upwork.com/jobs/~abc123",
        title="UGC Creator Needed",
        description="Create TikTok videos for our brand.",
        payload=payload,
    )


def test_normalize_upwork_listing_maps_prd_fields():
    opportunity = normalize_upwork_listing(_sample_raw())
    assert opportunity.platform == "upwork"
    assert opportunity.external_id == "abc123"
    assert opportunity.title == "UGC Creator Needed"
    assert opportunity.budget == "$500.00"
    assert opportunity.hourly is False
    assert opportunity.skills == ["Video Editing", "TikTok"]
    assert opportunity.client_rating == "4.8"
    assert opportunity.payment_verified is True
    assert opportunity.posted_at is not None
    assert opportunity.metadata["experience_level"] == "Intermediate"
    assert opportunity.metadata["client_country"] == "United States"
    assert opportunity.metadata["search_query"] == "UGC"
    assert opportunity.metadata["job_id"] == "abc123"


def test_normalize_raises_without_external_id():
    raw = _sample_raw()
    raw.external_id = ""
    raw.payload["job_id"] = ""
    with pytest.raises(NormalizationError, match="external_id"):
        normalize_upwork_listing(raw)


def test_normalize_raises_without_title():
    raw = _sample_raw()
    raw.title = ""
    raw.payload["title"] = ""
    with pytest.raises(NormalizationError, match="title"):
        normalize_upwork_listing(raw)


def test_opportunity_to_prd_json_shape():
    opportunity = normalize_upwork_listing(_sample_raw())
    payload = json.loads(opportunity_to_prd_json(opportunity))
    assert payload["platform"] == "upwork"
    assert payload["hourly"] is False
    assert payload["payment_verified"] is True
    assert isinstance(payload["skills"], list)
    assert payload["posted_at"] is not None
    assert set(payload.keys()) == {
        "platform",
        "external_id",
        "title",
        "description",
        "url",
        "budget",
        "hourly",
        "skills",
        "posted_at",
        "client_rating",
        "client_spend",
        "payment_verified",
        "proposal_count",
        "metadata",
    }


def test_opportunity_to_prd_dict_metadata_mapping():
    opportunity = Opportunity(
        platform="upwork",
        external_id="x1",
        title="Title",
        url="https://example.com",
        metadata={"search_query": "UGC", "job_id": "x1"},
    )
    data = opportunity_to_prd_dict(opportunity)
    assert data["metadata"]["search_query"] == "UGC"

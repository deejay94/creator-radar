"""Tests for Upwork job extraction types and merging."""

from __future__ import annotations

from pathlib import Path

import pytest

from radar.upwork.extract_types import UpworkExtractedJob, merge_extracted_job
from radar.upwork.parse import parse_listing_fields

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "upwork"


def test_merge_extracted_job_prefers_dom_over_regex():
    regex_job = UpworkExtractedJob(
        title="Fallback Title",
        budget="$10.00",
        experience_level="Entry Level",
    )
    merged = merge_extracted_job(
        regex_job=regex_job,
        dom_fields={"budget": "$500.00", "experience_level": "Expert"},
        tile_fields={"posted_time": "Posted 2 hours ago"},
        job_id="abc123",
        url="https://www.upwork.com/jobs/~abc123",
        search_query="UGC",
    )
    assert merged.budget == "$500.00"
    assert merged.experience_level == "Expert"
    assert merged.posted_time == "Posted 2 hours ago"
    assert merged.job_id == "abc123"
    assert merged.search_query == "UGC"


def test_parse_listing_fields_with_dom_and_tile():
    extracted = parse_listing_fields(
        title="UGC Video Creator Needed",
        description="Create short-form TikTok and Instagram videos.",
        skills=["Video Production", "TikTok"],
        features=["Fixed-price", "$500.00", "Expert"],
        page_text="Posted 1 day ago | United States | $50K+ spent | 4.9 of 5",
        dom_fields={
            "budget": "Fixed-price: $500.00",
            "job_type": "Fixed-price: $500.00",
            "experience_level": "Expert",
            "posted_time": "Posted 1 day ago",
            "proposal_count": "Less than 5 proposals",
            "client_rating": "4.9 of 5",
            "client_spend": "$50K+ spent",
            "client_country": "United States",
            "project_length": "1 to 3 months",
            "category": "Sales & Marketing",
            "subcategory": "Marketing Strategy",
            "payment_verified": True,
            "skills": ["Video Production", "TikTok"],
        },
        tile_fields={
            "budget": "Hourly: $25.00 - $45.00",
            "experience_level": "Intermediate",
            "posted_time": "Posted 2 hours ago",
        },
        job_id="detail123",
        url="https://www.upwork.com/jobs/~detail123",
        search_query="UGC",
    )
    assert extracted.job_id == "detail123"
    assert extracted.budget == "Fixed-price: $500.00"
    assert extracted.hourly is False
    assert extracted.experience_level == "Expert"
    assert extracted.client_country == "United States"
    assert extracted.payment_verified is True
    assert extracted.skills == ["Video Production", "TikTok"]
    assert extracted.search_query == "UGC"


def test_fixture_detail_html_fields_present():
    html = (FIXTURES / "job_detail.html").read_text(encoding="utf-8")
    assert 'data-test="job-title"' in html
    assert 'data-test="Description"' in html
    assert 'data-test="payment-verified"' in html


def test_fixture_tile_html_fields_present():
    html = (FIXTURES / "job_tile.html").read_text(encoding="utf-8")
    assert 'data-test="JobTile"' in html
    assert 'data-test="job-type-label"' in html
    assert 'data-test="job-pubilshed-date"' in html


def test_missing_prd_fields_detects_empty_values():
    job = UpworkExtractedJob(title="Only Title", job_id="x1")
    missing = job.missing_prd_fields()
    assert "description" in missing
    assert "budget" in missing
    assert "skills" in missing

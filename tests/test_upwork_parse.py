import pytest

from radar.upwork.parse import (
    canonical_job_url,
    parse_job_id_from_url,
    parse_listing_fields,
    parse_posted_at,
)
from radar.upwork.scraper import build_search_url


def test_parse_job_id_from_url():
    assert parse_job_id_from_url("https://www.upwork.com/jobs/~01abcXYZ") == "01abcXYZ"


def test_canonical_job_url():
    assert canonical_job_url("01abcXYZ") == "https://www.upwork.com/jobs/~01abcXYZ"


def test_build_search_url():
    url = build_search_url("UGC Creator")
    assert "q=UGC+Creator" in url or "q=UGC%20Creator" in url
    assert "sort=recency" in url


def test_parse_listing_fields_from_features():
    payload = parse_listing_fields(
        title="UGC Video Creator",
        description="Need short-form product videos.",
        skills=["Video Production", "TikTok"],
        features=[
            "Hourly",
            "$25.00 - $45.00",
            "Intermediate",
            "Proposals: 5 to 10",
            "Payment method verified",
        ],
        page_text="Posted 3 hours ago | United States | $10K+ spent | 4.9 of 5",
    )
    assert payload["hourly"] is True
    assert "$25.00" in payload["budget"]
    assert payload["experience_level"] == "Intermediate"
    assert payload["proposal_count"] == "5 to 10"
    assert payload["payment_verified"] is True
    assert payload["client_rating"] == "4.9"
    assert "3 hours ago" in payload["posted_time"]


def test_parse_posted_at_relative():
    posted = parse_posted_at("Posted 2 days ago")
    assert posted is not None

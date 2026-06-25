from radar.models import ClassificationResult
from radar.output import format_opportunity


def test_format_opportunity_includes_link():
    result = ClassificationResult(
        title="Paid UGC collab",
        subreddit="UGCCreators",
        url="https://reddit.com/r/UGCCreators/comments/abc/test/",
        niche="Beauty",
        nicheTier=2,
        isOpportunity=True,
        opportunityTier="A",
        contactMethod="DM",
        contactInfo="u/brand",
        reason="Explicit creator hiring with DM contact",
    )
    text = format_opportunity(result)
    assert "🔥 OPPORTUNITY FOUND" in text
    assert "Link: https://reddit.com/r/UGCCreators/comments/abc/test/" in text
    assert "Tier: A" in text
    assert "Contact: DM — u/brand" in text

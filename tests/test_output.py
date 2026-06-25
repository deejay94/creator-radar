from radar.models import ClassificationResult
from radar.output import format_opportunity


def test_format_opportunity_matches_template():
    result = ClassificationResult(
        title="[PAID] $20. 30s video. 30+, Male, English speakers. DM",
        subreddit="UGCCreators",
        url="https://reddit.com/r/UGCCreators/comments/abc/test/",
        niche="UGC Creators",
        nicheTier=1,
        isOpportunity=True,
        opportunityTier="A",
        contactMethod="DM",
        contactInfo="u/goodvibesforeveryone",
        reason="Explicit request for UGC creators with payment mentioned.",
    )
    text = format_opportunity(result)
    assert text == (
        "🔥 TIER A OPPORTUNITY (TIER 1 NICHE)\n"
        "\n"
        "Title: [PAID] $20. 30s video. 30+, Male, English speakers. DM\n"
        "Niche: UGC Creators\n"
        "Niche Tier: 1\n"
        "Opportunity Tier: A\n"
        "\n"
        "Link: https://reddit.com/r/UGCCreators/comments/abc/test/\n"
        "Contact: DM u/goodvibesforeveryone\n"
        "\n"
        "Reason: Explicit request for UGC creators with payment mentioned."
    )

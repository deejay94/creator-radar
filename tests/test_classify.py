import json
from unittest.mock import MagicMock, patch

from radar.classify import classify_post
from radar.models import RedditPost


def test_classify_post_parses_and_enforces_url():
    post = RedditPost(
        post_id="abc",
        title="Looking for UGC creators",
        body="DM me for paid collab",
        author="brand",
        subreddit="UGCCreators",
        url="https://reddit.com/r/UGCCreators/comments/abc123/test/",
    )
    ai_json = {
        "title": "Looking for UGC creators",
        "subreddit": "UGCCreators",
        "url": "https://wrong.com",
        "niche": "Beauty",
        "nicheTier": 2,
        "isOpportunity": True,
        "opportunityTier": "A",
        "contactMethod": "DM",
        "contactInfo": "u/brand",
        "reason": "Explicit hiring signal",
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(ai_json)

    with patch("radar.classify.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            result = classify_post(post)

    assert result.url == post.url
    assert result.opportunityTier == "A"
    assert result.is_actionable()

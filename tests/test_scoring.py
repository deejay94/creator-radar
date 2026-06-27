import json
from unittest.mock import MagicMock, patch

from radar.connectors.types import Opportunity
from radar.scoring.config import is_ai_scoring_enabled
from radar.scoring.scorer import ScoreResult, apply_score, score_opportunity


def test_is_ai_scoring_enabled_defaults_false(monkeypatch):
    monkeypatch.delenv("RADAR_AI_SCORING", raising=False)
    monkeypatch.delenv("RADAR_AI_ENABLED", raising=False)
    assert is_ai_scoring_enabled() is False


def test_is_ai_scoring_enabled_via_master_switch(monkeypatch):
    monkeypatch.delenv("RADAR_AI_SCORING", raising=False)
    monkeypatch.setenv("RADAR_AI_ENABLED", "true")
    assert is_ai_scoring_enabled() is True


def test_is_ai_scoring_disabled_via_env(monkeypatch):
    monkeypatch.setenv("RADAR_AI_SCORING", "false")
    assert is_ai_scoring_enabled() is False


def test_apply_score_updates_opportunity_fields():
    opportunity = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="UGC Creator",
        url="https://www.upwork.com/jobs/~job1234567890",
    )
    result = ScoreResult(
        score=92,
        confidence=0.91,
        reasoning="Clear UGC ask with strong budget.",
        priority="high",
        estimatedMatch="Strong TikTok UGC fit",
        labels=["High Value", "Fast Apply"],
    )
    scored = apply_score(opportunity, result)
    assert scored.ai_score == 92
    assert scored.priority == "high"
    assert scored.reasoning == "Clear UGC ask with strong budget."
    assert scored.metadata["estimated_match"] == "Strong TikTok UGC fit"
    assert scored.metadata["labels"] == ["High Value", "Fast Apply"]


def test_score_opportunity_calls_openai():
    opportunity = Opportunity(
        platform="upwork",
        external_id="job1234567890",
        title="UGC Creator for SaaS",
        description="Need short product demo videos.",
        url="https://www.upwork.com/jobs/~job1234567890",
        budget="$500",
    )
    ai_json = {
        "score": 88,
        "confidence": 0.9,
        "reasoning": "Strong UGC fit.",
        "priority": "high",
        "estimatedMatch": "SaaS product video",
        "labels": ["High Value"],
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(ai_json)

    with patch("radar.scoring.scorer.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            result = score_opportunity(opportunity)

    assert result.score == 88
    assert result.priority == "high"

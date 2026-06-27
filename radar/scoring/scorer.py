"""AI opportunity scoring (0–100) for imported opportunities."""

from __future__ import annotations

import json
import os
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from radar.connectors.types import Opportunity
from radar.niches import format_niche_tiers_for_prompt

Priority = Literal["high", "medium", "low"]

VALID_LABELS = (
    "High Value",
    "New Client",
    "Fast Apply",
    "Beginner Friendly",
    "Premium Budget",
    "Product Shipment Required",
    "Long-Term Potential",
)

SYSTEM_PROMPT = f"""You score freelance UGC/creator opportunities for a UGC creator deciding what to apply to.

Return JSON only with these exact keys:
score, confidence, reasoning, priority, estimatedMatch, labels

Field rules:
- score: integer 0–100 (higher = better opportunity for a UGC creator)
- confidence: number 0.0–1.0 (how confident you are in the score)
- reasoning: 1–3 sentences explaining the score (mention budget, UGC fit, client signals, competition)
- priority: exactly one of: high, medium, low
- estimatedMatch: short phrase describing niche/fit (e.g. "Strong TikTok UGC fit")
- labels: array of zero or more from this list only:
  {list(VALID_LABELS)}

Scoring guidance:
- 80–100: Excellent UGC opportunity — clear UGC ask, good budget, verified client, low competition
- 60–79: Solid opportunity worth reviewing
- 40–59: Weak or unclear fit
- 0–39: Poor fit, wrong role type, or very low signal

Prioritize opportunities that explicitly hire UGC creators, have clear deliverables, and realistic budgets.

{format_niche_tiers_for_prompt()}
"""


class ScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    priority: Priority
    estimated_match: str = Field(alias="estimatedMatch")
    labels: list[str] = Field(default_factory=list)

    @field_validator("labels")
    @classmethod
    def labels_must_be_known(cls, value: list[str]) -> list[str]:
        return [label for label in value if label in VALID_LABELS]

    model_config = {"populate_by_name": True}


def _format_opportunity_for_prompt(opportunity: Opportunity) -> str:
    metadata = opportunity.metadata
    lines = [
        f"Platform: {opportunity.platform}",
        f"Title: {opportunity.title}",
        f"URL: {opportunity.url}",
        f"Budget: {opportunity.budget or 'unknown'}",
        f"Hourly: {opportunity.hourly}",
        f"Skills: {', '.join(opportunity.skills) or 'none'}",
        f"Client rating: {opportunity.client_rating or 'unknown'}",
        f"Client spend: {opportunity.client_spend or 'unknown'}",
        f"Payment verified: {opportunity.payment_verified}",
        f"Proposals: {opportunity.proposal_count or 'unknown'}",
        f"Search query: {metadata.get('search_query', '')}",
        f"Experience level: {metadata.get('experience_level', '')}",
        f"Project length: {metadata.get('project_length', '')}",
        f"Description:\n{opportunity.description[:4000]}",
    ]
    return "\n".join(lines)


def score_opportunity(opportunity: Opportunity) -> ScoreResult:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _format_opportunity_for_prompt(opportunity)},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from OpenAI")

    data = json.loads(content)
    return ScoreResult.model_validate(data)


def apply_score(opportunity: Opportunity, result: ScoreResult) -> Opportunity:
    metadata = dict(opportunity.metadata)
    metadata["ai_confidence"] = result.confidence
    metadata["estimated_match"] = result.estimated_match
    metadata["labels"] = result.labels

    return opportunity.model_copy(
        update={
            "ai_score": result.score,
            "priority": result.priority,
            "reasoning": result.reasoning,
            "metadata": metadata,
        }
    )

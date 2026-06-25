from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

OpportunityTier = Literal["A", "B", "C", "REJECT"]


class RedditPost(BaseModel):
    post_id: str
    title: str
    body: str
    author: str
    subreddit: str
    url: str
    flair: str = ""


class ClassificationResult(BaseModel):
    title: str
    subreddit: str
    url: str
    niche: str
    nicheTier: int = Field(ge=1, le=3)
    isOpportunity: bool
    opportunityTier: OpportunityTier
    contactMethod: str = ""
    contactInfo: str = ""
    reason: str = ""

    @field_validator("url")
    @classmethod
    def url_must_be_reddit(cls, value: str) -> str:
        if not value.startswith("https://reddit.com/"):
            raise ValueError("url must start with https://reddit.com/")
        return value

    def is_actionable(self) -> bool:
        return self.isOpportunity and self.opportunityTier in ("A", "B", "C")

"""Shared types for platform connectors."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ConnectorHealth(BaseModel):
    healthy: bool
    status: str
    display_name: Optional[str] = None
    message: str = ""


class SearchParams(BaseModel):
    queries: list[str] = Field(default_factory=list)
    limit_per_query: int = 20
    extras: dict[str, Any] = Field(default_factory=dict)


class RawListingRef(BaseModel):
    external_id: str
    url: str
    title: str = ""


class RawListing(BaseModel):
    platform: str
    external_id: str
    url: str
    title: str = ""
    description: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


class Opportunity(BaseModel):
    platform: str
    external_id: str
    title: str
    description: str = ""
    url: str
    budget: str = ""
    posted_at: Optional[datetime] = None
    skills: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

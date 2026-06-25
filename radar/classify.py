from __future__ import annotations

import json
import os

from openai import OpenAI

from radar.models import ClassificationResult, RedditPost
from radar.niches import OPPORTUNITY_TIER_RULES, format_niche_tiers_for_prompt

SYSTEM_PROMPT = f"""You classify Reddit posts for UGC creators looking for brand opportunities.

Return JSON only with these exact keys:
title, subreddit, url, niche, nicheTier, isOpportunity, opportunityTier, contactMethod, contactInfo, reason

Rules:
- nicheTier must be 1, 2, or 3 based on the niche lists below
- opportunityTier must be exactly one of: A, B, C, REJECT
- isOpportunity is true only for genuine brand/creator opportunities (A, B, or C)
- url MUST be copied exactly from the user message — do not modify it
- contactMethod: e.g. DM, Email, Form, Comment, Unknown
- contactInfo: email address, username, or link if visible; else empty string
- reason: one concise sentence explaining the classification

{format_niche_tiers_for_prompt()}

{OPPORTUNITY_TIER_RULES}
"""


def classify_post(post: RedditPost) -> ClassificationResult:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    user_prompt = (
        f"Title: {post.title}\n"
        f"Subreddit: r/{post.subreddit}\n"
        f"Author: u/{post.author}\n"
        f"URL (copy exactly): {post.url}\n"
        f"Body:\n{post.body[:3000]}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty response from OpenAI")

    data = json.loads(content)
    data["url"] = post.url
    data["title"] = data.get("title") or post.title
    data["subreddit"] = data.get("subreddit") or post.subreddit

    return ClassificationResult.model_validate(data)

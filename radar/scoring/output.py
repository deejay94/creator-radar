"""Format scored opportunities for console output."""

from __future__ import annotations

from radar.connectors.types import Opportunity


def format_scored_opportunity(row_id: int, opportunity: Opportunity) -> str:
    score = opportunity.ai_score if opportunity.ai_score is not None else "—"
    lines = [
        f"─── [{row_id}] Score {score} · {opportunity.priority or 'unscored'} priority ───",
        f"Title: {opportunity.title}",
        f"Platform: {opportunity.platform} · Budget: {opportunity.budget or 'unknown'}",
        f"Link: {opportunity.url}",
    ]

    estimated_match = opportunity.metadata.get("estimated_match")
    if estimated_match:
        lines.append(f"Match: {estimated_match}")

    if opportunity.reasoning:
        lines.append(f"Reason: {opportunity.reasoning}")

    labels = opportunity.metadata.get("labels") or []
    if labels:
        lines.append(f"Labels: {', '.join(labels)}")

    confidence = opportunity.metadata.get("ai_confidence")
    if confidence is not None:
        lines.append(f"Confidence: {confidence}")

    return "\n".join(lines)

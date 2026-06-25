from __future__ import annotations

from radar.models import ClassificationResult


def format_opportunity(result: ClassificationResult) -> str:
    lines = [
        "🔥 OPPORTUNITY FOUND",
        "",
        f"Title: {result.title}",
        f"Niche: {result.niche}",
        f"Tier: {result.opportunityTier}",
        f"Niche Tier: {result.nicheTier}",
        f"Link: {result.url}",
        f"Reason: {result.reason}",
    ]
    if result.contactMethod or result.contactInfo:
        contact = result.contactMethod
        if result.contactInfo:
            contact = f"{contact} — {result.contactInfo}" if contact else result.contactInfo
        lines.append(f"Contact: {contact}")
    return "\n".join(lines)


def print_opportunity(result: ClassificationResult) -> None:
    print(format_opportunity(result))
    print()


def print_summary(scanned: int, results: list[ClassificationResult], flair_filter: str = "") -> None:
    actionable = [r for r in results if r.is_actionable()]
    counts = {"A": 0, "B": 0, "C": 0}
    for r in actionable:
        counts[r.opportunityTier] += 1
    label = f'"{flair_filter}" posts' if flair_filter else "posts"
    print(
        f"Scanned {scanned} {label} · {len(actionable)} opportunities "
        f"({counts['A']} A, {counts['B']} B, {counts['C']} C)"
    )

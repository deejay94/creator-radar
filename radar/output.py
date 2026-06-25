from __future__ import annotations

from radar.models import ClassificationResult


def _format_contact(result: ClassificationResult) -> str:
    method = result.contactMethod.strip()
    info = result.contactInfo.strip()
    if method and info:
        return f"{method} {info}"
    return method or info


def format_opportunity(result: ClassificationResult) -> str:
    header = (
        f"🔥 TIER {result.opportunityTier} OPPORTUNITY "
        f"(TIER {result.nicheTier} NICHE)"
    )
    lines = [
        header,
        "",
        f"Title: {result.title}",
        f"Niche: {result.niche}",
        f"Niche Tier: {result.nicheTier}",
        f"Opportunity Tier: {result.opportunityTier}",
        "",
        f"Link: {result.url}",
    ]

    contact = _format_contact(result)
    if contact:
        lines.append(f"Contact: {contact}")

    lines.extend(["", f"Reason: {result.reason}"])
    return "\n".join(lines)


def print_opportunity(result: ClassificationResult) -> None:
    print(format_opportunity(result))
    print()


def print_summary(
    scanned: int,
    results: list[ClassificationResult],
    flair_filter: str = "",
    fetched: int = 0,
    filtered_out: int = 0,
) -> None:
    actionable = [r for r in results if r.is_actionable()]
    counts = {"A": 0, "B": 0, "C": 0}
    for r in actionable:
        counts[r.opportunityTier] += 1
    label = f'"{flair_filter}" posts' if flair_filter else "posts"
    prefix = ""
    if fetched and filtered_out:
        prefix = f"Fetched {fetched} · filtered out {filtered_out} · "
    print(
        f"{prefix}Scanned {scanned} {label} · {len(actionable)} opportunities "
        f"({counts['A']} A, {counts['B']} B, {counts['C']} C)"
    )

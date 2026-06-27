from __future__ import annotations

from radar.models import ClassificationResult, RedditPost


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


def format_reddit_post(post: RedditPost) -> str:
    lines = [
        f"Title: {post.title}",
        f"Link: {post.url}",
    ]
    if post.flair:
        lines.append(f"Flair: {post.flair}")
    if post.author:
        lines.append(f"Author: u/{post.author}")
    return "\n".join(lines)


def print_reddit_post(post: RedditPost) -> None:
    print(format_reddit_post(post))
    print()


def print_plain_summary(
    *,
    shown: int,
    flair_filter: str = "",
    fetched: int = 0,
    filtered_out: int = 0,
) -> None:
    label = f'"{flair_filter}" posts' if flair_filter else "posts"
    prefix = ""
    if fetched and filtered_out:
        prefix = f"Fetched {fetched} · filtered out {filtered_out} · "
    print(f"{prefix}Showing {shown} {label} (AI classification disabled)")


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

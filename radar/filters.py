from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from radar.models import RedditPost

MAX_POST_AGE_HOURS = 72

_HIRER_PATTERNS = (
    re.compile(r"looking for (ugc )?creators?", re.I),
    re.compile(r"seeking (ugc )?creators?", re.I),
    re.compile(r"need (ugc )?creators?", re.I),
    re.compile(r"\b(?:we(?:'re| are) )?hiring (ugc )?creators?", re.I),
    re.compile(r"^\[hiring\]", re.I),
    re.compile(r"\bhiring:\s", re.I),
    re.compile(r"\bpaid\b", re.I),
    re.compile(r"paying creators?", re.I),
    re.compile(r"dm (me )?for (a )?collab", re.I),
)

_JOB_SEEKER_ASKING_HIRING = (
    re.compile(r"\banyone hiring\b", re.I),
    re.compile(r"\bwho(?:'s| is) hiring\b", re.I),
)

_JOB_SEEKER_PATTERNS = (
    re.compile(r"\bhire me\b", re.I),
    re.compile(r"looking for (work|gigs?|jobs?|opportunities)\b", re.I),
    re.compile(r"looking for (a )?(ugc |content creator )?(jobs?|gigs?|work)\b", re.I),
    re.compile(r"seeking (a )?(ugc |content creator )?(jobs?|gigs?|work)\b", re.I),
    re.compile(r"searching for (a )?(ugc |content creator )?(jobs?|gigs?|work)\b", re.I),
    re.compile(r"looking for brands? to work with", re.I),
    re.compile(r"where (are|can i find) (the )?gigs?", re.I),
    re.compile(r"trying to (break into|get into|start in) (ugc|content creation)", re.I),
    re.compile(r"\bnew (ugc )?creator\b", re.I),
    re.compile(r"get (my|your) first (gig|client|collab|brand)", re.I),
    re.compile(r"available for (ugc )?collabs?", re.I),
    re.compile(r"rate my (portfolio|profile|page)", re.I),
    re.compile(r"roast my", re.I),
    re.compile(r"feedback on my (portfolio|profile|videos?)", re.I),
    re.compile(r"\bopen to work\b", re.I),
    re.compile(r"\bopen for work\b", re.I),
    re.compile(r"\bneed (a )?(ugc )?(job|gig)\b", re.I),
)

_MEME_DISCUSSION_FLAIR = re.compile(r"\b(meme|discussion|rant|shitpost|off[- ]topic|humou?r)\b", re.I)
_MEME_DISCUSSION_PATTERNS = (
    re.compile(r"\bunpopular opinion\b", re.I),
    re.compile(r"\bam i the only one\b", re.I),
    re.compile(r"\bdoes anyone else\b", re.I),
    re.compile(r"\bhot take\b", re.I),
    re.compile(r"\bjust (a )?rant\b", re.I),
)

_HOW_DO_I_PATTERNS = (
    re.compile(r"^how (do|can|should|would) i\b", re.I),
    re.compile(r"^how to\b", re.I),
    re.compile(r"^what(?:'s| is) the best (way|app|platform|site)\b", re.I),
    re.compile(r"^any (tips|advice|suggestions)\b", re.I),
    re.compile(r"^help (me |with\b)", re.I),
    re.compile(r"^where (do|can) i (find|get|start)\b", re.I),
    re.compile(r"^is it (worth|possible)\b", re.I),
)

_META_PATTERNS = (
    re.compile(r"\bthis sub(reddit)?\b", re.I),
    re.compile(r"\bthe mods?\b", re.I),
    re.compile(r"\bmoderators?\b", re.I),
    re.compile(r"\bsubreddit rules?\b", re.I),
    re.compile(r"\bmeta\b", re.I),
    re.compile(r"\bwhy was my post removed\b", re.I),
    re.compile(r"\babout r/", re.I),
)


def _post_text(post: RedditPost) -> str:
    return f"{post.title}\n{post.body}".strip()


def _matches_any(text: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _is_job_seeker_post(post: RedditPost) -> bool:
    text = _post_text(post)
    if _matches_any(text, _JOB_SEEKER_ASKING_HIRING):
        return True
    if _matches_any(text, _HIRER_PATTERNS):
        return False
    return _matches_any(text, _JOB_SEEKER_PATTERNS)


def _is_meme_or_discussion(post: RedditPost) -> bool:
    if post.flair and _MEME_DISCUSSION_FLAIR.search(post.flair):
        return True
    return _matches_any(post.title, _MEME_DISCUSSION_PATTERNS)


def _is_how_do_i_post(post: RedditPost) -> bool:
    return _matches_any(post.title, _HOW_DO_I_PATTERNS)


def _is_meta_post(post: RedditPost) -> bool:
    return _matches_any(_post_text(post), _META_PATTERNS)


def _is_too_old(post: RedditPost, max_age_hours: int = MAX_POST_AGE_HOURS) -> bool:
    if post.created_at is None:
        return False
    created = post.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - created
    return age > timedelta(hours=max_age_hours)


def get_skip_reason(post: RedditPost, max_age_hours: int = MAX_POST_AGE_HOURS) -> Optional[str]:
    if _is_too_old(post, max_age_hours):
        return "older than 72 hours"
    if _is_job_seeker_post(post):
        return "job seeker post"
    if _is_meme_or_discussion(post):
        return "meme or discussion post"
    if _is_how_do_i_post(post):
        return "how-to or advice-seeking post"
    if _is_meta_post(post):
        return "meta subreddit content"
    return None


def filter_posts_for_classification(
    posts: list[RedditPost],
    max_age_hours: int = MAX_POST_AGE_HOURS,
) -> tuple[list[RedditPost], list[tuple[RedditPost, str]]]:
    eligible: list[RedditPost] = []
    skipped: list[tuple[RedditPost, str]] = []
    for post in posts:
        reason = get_skip_reason(post, max_age_hours)
        if reason:
            skipped.append((post, reason))
        else:
            eligible.append(post)
    return eligible, skipped

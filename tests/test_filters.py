from datetime import datetime, timedelta, timezone
from typing import Optional

from radar.filters import filter_posts_for_classification, get_skip_reason
from radar.models import RedditPost


def _post(
    title: str,
    body: str = "",
    flair: str = "Collab Request 🤝",
    created_at: Optional[datetime] = None,
) -> RedditPost:
    return RedditPost(
        post_id="abc",
        title=title,
        body=body,
        author="user",
        subreddit="UGCCreators",
        url="https://reddit.com/r/UGCCreators/comments/abc/test/",
        flair=flair,
        created_at=created_at,
    )


def test_keeps_brand_collab_request():
    post = _post("[PAID] $20 video. Looking for UGC creators. DM me")
    assert get_skip_reason(post) is None


def test_filters_job_seeker_posts():
    post = _post("Where are the gigs for 40+ women?!")
    assert get_skip_reason(post) == "job seeker post"

    post = _post("New UGC creator looking for work")
    assert get_skip_reason(post) == "job seeker post"

    post = _post("Looking for UGC jobs")
    assert get_skip_reason(post) == "job seeker post"

    post = _post("Looking for a content creator job")
    assert get_skip_reason(post) == "job seeker post"

    post = _post("Anyone hiring UGC creators?")
    assert get_skip_reason(post) == "job seeker post"


def test_does_not_filter_hirer_looking_for_creators():
    post = _post("Looking for creators for paid skincare campaign")
    assert get_skip_reason(post) is None

    post = _post("[HIRING] Looking for UGC creators — $150 per video")
    assert get_skip_reason(post) is None


def test_filters_meme_and_discussion():
    post = _post("Unpopular opinion about UGC rates")
    assert get_skip_reason(post) == "meme or discussion post"

    post = _post("Random thread", flair="Discussion")
    assert get_skip_reason(post) == "meme or discussion post"


def test_filters_how_do_i_posts():
    post = _post("How do I land my first collab?")
    assert get_skip_reason(post) == "how-to or advice-seeking post"

    post = _post("What is the best app for editing?")
    assert get_skip_reason(post) == "how-to or advice-seeking post"


def test_filters_meta_subreddit_content():
    post = _post("Can the mods update the rules for this subreddit?")
    assert get_skip_reason(post) == "meta subreddit content"


def test_filters_posts_older_than_72_hours():
    old = datetime.now(timezone.utc) - timedelta(hours=73)
    post = _post("Paid collab for creators", created_at=old)
    assert get_skip_reason(post) == "older than 72 hours"


def test_keeps_recent_posts():
    recent = datetime.now(timezone.utc) - timedelta(hours=12)
    post = _post("Paid collab for creators", created_at=recent)
    assert get_skip_reason(post) is None


def test_filter_posts_for_classification_splits_lists():
    recent = datetime.now(timezone.utc) - timedelta(hours=1)
    posts = [
        _post("Paid collab for creators", created_at=recent),
        _post("How do I get started?"),
    ]
    eligible, skipped = filter_posts_for_classification(posts)
    assert len(eligible) == 1
    assert len(skipped) == 1
    assert skipped[0][1] == "how-to or advice-seeking post"

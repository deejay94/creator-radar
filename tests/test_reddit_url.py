from radar.reddit import build_reddit_url


def test_build_reddit_url_from_permalink():
    assert build_reddit_url("/r/UGCCreators/comments/abc123/title/") == (
        "https://reddit.com/r/UGCCreators/comments/abc123/title/"
    )


def test_build_reddit_url_normalizes_www():
    assert build_reddit_url("https://www.reddit.com/r/test/comments/1/") == (
        "https://reddit.com/r/test/comments/1/"
    )

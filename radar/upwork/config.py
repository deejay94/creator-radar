"""Upwork connector configuration."""

DEFAULT_SEARCH_QUERIES = [
    "UGC",
    "User Generated Content",
    "TikTok Creator",
    "TikTok Content",
    "Instagram Creator",
    "Content Creator",
    "Product Video",
    "Product Review",
    "Video Testimonial",
    "Social Media Content",
]

DEFAULT_LIMIT_PER_QUERY = 20
PAGE_TIMEOUT_MS = 60_000
SEARCH_BASE_URL = "https://www.upwork.com/nx/search/jobs/"

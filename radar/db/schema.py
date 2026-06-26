"""SQLite schema for opportunities."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    budget TEXT NOT NULL DEFAULT '',
    hourly INTEGER,
    skills_json TEXT NOT NULL DEFAULT '[]',
    posted_at TEXT,
    client_rating TEXT NOT NULL DEFAULT '',
    client_spend TEXT NOT NULL DEFAULT '',
    payment_verified INTEGER,
    proposal_count TEXT NOT NULL DEFAULT '',
    ai_score INTEGER,
    priority TEXT NOT NULL DEFAULT '',
    reasoning TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(platform, external_id)
);

CREATE INDEX IF NOT EXISTS idx_opportunities_url ON opportunities(url);
CREATE INDEX IF NOT EXISTS idx_opportunities_platform ON opportunities(platform);
"""

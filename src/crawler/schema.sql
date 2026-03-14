CREATE TYPE url_status AS ENUM (
    'to_visit',    -- in sites_to_visit
    'in_progress',-- claimed by a worker, not yet finished
    'visited',    -- in sites_visited (fetched successfully)
    'failed',     -- in failed_links (non-200 response)
    'ignored'     -- in ignored_links (filtered out, e.g. non-EECS URL)
);

CREATE TABLE urls (
    id              BIGSERIAL       PRIMARY KEY,
    url             TEXT            NOT NULL UNIQUE,
    status          url_status      NOT NULL DEFAULT 'to_visit',

    -- populated for 'failed' status
    http_status_code INT,

    -- distributed crawling support
    worker_id       TEXT,
    claimed_at      TIMESTAMPTZ,

    -- audit timestamps
    discovered_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    visited_at      TIMESTAMPTZ
);

-- fast lookup of the next pending URL to claim
CREATE INDEX idx_urls_status ON urls (status);

-- fast deduplication check by URL
CREATE UNIQUE INDEX idx_urls_url ON urls (url);

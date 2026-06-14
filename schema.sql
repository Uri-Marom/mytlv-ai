-- mytlv.ai PostgreSQL schema
-- Run once: psql $DATABASE_URL -f schema.sql

CREATE TABLE IF NOT EXISTS venues (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    neighborhood TEXT,
    address     TEXT,
    lat         DOUBLE PRECISION,
    lng         DOUBLE PRECISION,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS organizers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    source      TEXT,
    UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS events (
    id           SERIAL PRIMARY KEY,
    source       TEXT NOT NULL,        -- 'secret_tel_aviv' | 'entrio' | 'bandsintown' | ...
    source_id    TEXT NOT NULL,        -- slug or external ID
    title        TEXT NOT NULL,
    description  TEXT,
    category     TEXT,                 -- 'music' | 'cultural' | 'market'
    subcategory  TEXT,                 -- 'dj-set' | 'live' | 'exhibition' | ...
    sta_category TEXT,                 -- raw source category label
    venue_id     INT REFERENCES venues(id),
    venue_name   TEXT,                 -- denormalized for convenience
    neighborhood TEXT,
    event_date   DATE,
    start_time   TIME,
    end_time     TIME,
    price_min    INT DEFAULT 0,
    price_max    INT,
    image_url    TEXT,
    ticket_url   TEXT,
    source_url   TEXT,
    tags         TEXT[],
    is_published BOOLEAN DEFAULT TRUE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source, source_id)
);

CREATE INDEX IF NOT EXISTS idx_events_date     ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_events_source   ON events(source);

-- Similarity table (populated by nightly job)
CREATE TABLE IF NOT EXISTS event_similarity (
    event_a_id         INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    event_b_id         INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    score_user_overlap FLOAT NOT NULL DEFAULT 0,
    score_venue        FLOAT NOT NULL DEFAULT 0,
    score_temporal     FLOAT NOT NULL DEFAULT 0,
    score_organizer    FLOAT NOT NULL DEFAULT 0,
    score_composite    FLOAT NOT NULL DEFAULT 0,
    overlap_user_count INT NOT NULL DEFAULT 0,
    computed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (event_a_id, event_b_id),
    CHECK (event_a_id < event_b_id)
);

CREATE INDEX IF NOT EXISTS idx_sim_a ON event_similarity(event_a_id, score_composite DESC);
CREATE INDEX IF NOT EXISTS idx_sim_b ON event_similarity(event_b_id, score_composite DESC);

-- Convenience function: top-K similar events (bidirectional)
CREATE OR REPLACE FUNCTION top_similar_events(p_event_id INT, p_k INT DEFAULT 6)
RETURNS TABLE(similar_event_id INT, score_composite FLOAT, score_user_overlap FLOAT,
              score_venue FLOAT, score_temporal FLOAT, score_organizer FLOAT, overlap_user_count INT)
LANGUAGE SQL STABLE AS $$
    SELECT CASE WHEN event_a_id = p_event_id THEN event_b_id ELSE event_a_id END,
           es.score_composite, es.score_user_overlap, es.score_venue,
           es.score_temporal, es.score_organizer, es.overlap_user_count
    FROM event_similarity es
    WHERE event_a_id = p_event_id OR event_b_id = p_event_id
    ORDER BY es.score_composite DESC LIMIT p_k;
$$;

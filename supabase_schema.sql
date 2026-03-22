-- BergenBook Supabase Schema
-- Run this in Supabase → SQL Editor → New Query

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE,
    password_hash TEXT,
    avatar_url    TEXT,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS oauth_accounts (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider         TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    email            TEXT,
    created_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

CREATE TABLE IF NOT EXISTS players (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS courses (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    slope_rating  FLOAT DEFAULT 113.0,
    course_rating FLOAT DEFAULT 72.0,
    par           INTEGER DEFAULT 72
);

CREATE TABLE IF NOT EXISTS rounds (
    id         SERIAL PRIMARY KEY,
    course_id  INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    date       DATE NOT NULL,
    created_by TEXT,
    image_url  TEXT,
    notes      TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS round_players (
    id               SERIAL PRIMARY KEY,
    round_id         INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
    player_id        INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    handicap_at_time FLOAT,
    total_score      INTEGER
);

CREATE TABLE IF NOT EXISTS scores (
    id          SERIAL PRIMARY KEY,
    round_id    INTEGER NOT NULL REFERENCES rounds(id) ON DELETE CASCADE,
    player_id   INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    hole_number INTEGER NOT NULL,
    strokes     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS name_mappings (
    id               SERIAL PRIMARY KEY,
    raw_name         TEXT NOT NULL,
    player_id        INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    confidence_score FLOAT DEFAULT 1.0,
    last_used        TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS handicap_history (
    id              SERIAL PRIMARY KEY,
    player_id       INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    handicap_index  FLOAT NOT NULL,
    calculated_at   TIMESTAMP DEFAULT NOW(),
    rounds_used     INTEGER DEFAULT 0
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Supabase — Demo Logging Tables
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- These tables track all demo chat activity for sales intelligence.
-- ─────────────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────────────
-- 1. demo_chat_logs
--
-- One row per demo chat exchange (all levels: single-model, council, prism).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS demo_chat_logs (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    venue_id        TEXT NOT NULL,
    venue_name      TEXT NOT NULL,
    prospect_name   TEXT NOT NULL,
    question        TEXT NOT NULL,
    response        TEXT NOT NULL,

    -- Which pipeline produced this response
    demo_mode       TEXT NOT NULL DEFAULT 'single_model'
        CHECK (demo_mode IN ('single_model', 'council', 'prism', 'council_prism'))
);

CREATE INDEX IF NOT EXISTS idx_demo_chat_venue
    ON demo_chat_logs (venue_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_demo_chat_prospect
    ON demo_chat_logs (prospect_name, created_at DESC);

COMMENT ON TABLE demo_chat_logs IS
    'Every demo chat Q&A pair, regardless of pipeline. '
    'demo_mode distinguishes single-model, council, prism, and council+prism responses.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. prism_sessions
--
-- One row per Prism pipeline run — tracks the full 6-agent analysis,
-- question asked, duration, and how many agents completed.
-- Mirrors venue_council_sessions but for the Prism multi-agent pipeline.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS prism_sessions (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    venue_id        TEXT NOT NULL,
    venue_name      TEXT NOT NULL,
    prospect_name   TEXT NOT NULL,
    demo_level      INT NOT NULL CHECK (demo_level IN (3, 4)),

    question        TEXT NOT NULL,
    full_response   TEXT NOT NULL,

    -- How long the full Prism pipeline took end-to-end
    duration_ms     INT,

    -- Number of agents that returned a response (out of 6)
    agents_completed INT NOT NULL DEFAULT 6,

    -- Any agents that errored (array of agent labels e.g. ['Agent 3'])
    agents_errored  TEXT[] NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_prism_sessions_venue
    ON prism_sessions (venue_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_prism_sessions_prospect
    ON prism_sessions (prospect_name, created_at DESC);

COMMENT ON TABLE prism_sessions IS
    'One row per Prism pipeline run. Tracks the full 6-agent response, duration, '
    'and completion status. Use this to audit Prism quality and identify slow or '
    'erroring agents across demo sessions.';

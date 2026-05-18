-- 016_council_sessions.sql
-- Stores the full debate tree from the Council of Models.
-- Every session captures Round 1 (independent), Round 2 (debate), and the synthesis.
-- This is Polynovea's proprietary training dataset.

create table if not exists venue_council_sessions (
    id               uuid        default gen_random_uuid() primary key,
    created_at       timestamptz default now(),

    -- Request context
    venue_id         text        not null,
    tab              text        not null,
    question         text        not null,

    -- Round 1: independent answers
    nemotron_r1      text,
    deepseek_r1      text,
    qwen_r1          text,

    -- Round 2: positions after cross-review
    nemotron_r2      text,
    deepseek_r2      text,
    qwen_r2          text,

    -- Round 3: synthesis output
    synthesis        text,
    consensus_reached boolean,

    -- Performance
    duration_ms      integer
);

-- Index for analytics queries
create index if not exists idx_council_venue    on venue_council_sessions (venue_id);
create index if not exists idx_council_tab      on venue_council_sessions (tab);
create index if not exists idx_council_consensus on venue_council_sessions (consensus_reached);
create index if not exists idx_council_created  on venue_council_sessions (created_at desc);

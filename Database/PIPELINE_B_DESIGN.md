# Pipeline B — General Human Behavior Pipeline

**Session designed:** 2026-05-20
**Status:** Designed, not built. No code written, no DB changes made.

---

## The Problem with Pipeline A

Pipeline A is a **venue intelligence tool**. Every step moves further from the person
and deeper into the venue. The human is extracted for signals in step 3 and then discarded.

It answers: *"What kind of place is this?"* — not *"Who are the people visiting this city?"*

**Specific losses identified:**

- Conditional logic flattened — *"food is good BUT service is pathetic"* loses the tradeoff judgment; only individual signals survive
- Person-level decision fingerprint discarded — why they came, what they tolerated, what caused exit — all lost after step 3 aggregation
- Implicit behavioral identity signals not extracted — e.g. *"who goes dining and doesn't click pictures?"* is a social identity signal, not a keyword match
- Aggregation direction wrong for population intelligence — aggregates reviews → venue, not people → segments → population

---

## What Pipeline B Is

A **parallel pipeline** that treats each Google review as one human behavioral record.

> 30L reviews = behavioral data of 30L people.

Pipeline B **never aggregates upward to venue level**. It aggregates:
**people → behavioral segments → population patterns** (cross-venue by design).

### Person Fingerprint

Each review produces one person fingerprint with these fields:

| Field | What it captures |
|---|---|
| `decision_trigger` | Why they came |
| `valued_dimensions` | What they care about |
| `tolerance_floor` | What they won't accept |
| `tradeoff_expressed` | What compensated for what — or didn't |
| `exit_or_retention` | Verdict: stayed, left early, would return |
| `social_behavior` | Brought friends / warned others / shared online |
| `behavioral_identity` | value_seeker, dignity_conscious, social_content_creator, etc. |

### Key New Extraction Needed

Decision logic parsing — reading conjunctions and contrast markers
(`BUT`, `DESPITE`, `EVEN THOUGH`) to understand tradeoff hierarchies.
Everything else (negation, temporal, quality scoring) is reusable from step 3 of Pipeline A.

---

## Architecture Decision

| | Pipeline A | Pipeline B |
|---|---|---|
| Input | Raw review JSON files | Same raw review JSON files |
| Unit of analysis | Venue primitive | Person fingerprint |
| Aggregation key | `place_id` | Behavioral segment ID (cross-venue) |
| Output answers | What kind of place is this? | Who are the people in this city? |
| Update cadence | Per venue when new reviews arrive | When enough new people shift a segment |

- Pipeline A stays **completely untouched**
- Pipeline B runs on the **same raw review JSON** but produces entirely separate outputs
- They reference each other via cross-reference fields — no ownership between them

---

## New DB Tables Required

```
behavioral_segments          — empirical, revealed, city-specific segments
segment_exit_triggers        — what caused people in each segment to leave
segment_retention_drivers    — what made them stay or return
segment_decision_triggers    — what brought them in the first place
venue_segment_density        — which behavioral segments actually visit which venues
archetype_validation         — how Pipeline B segments map to the 35 survey archetypes
```

---

## How It Augments Module 2

### Current weakness

Module 2's demand side is built from **45 survey responses** (stated preferences).
Supply side (venue primitives) is solid. The gap is a weak demand side.

### What Pipeline B changes

Survey schema fields map 1:1 to Pipeline B fields:

| Survey field | Pipeline B equivalent |
|---|---|
| `what_makes_leave_early` | `exit_triggers` |
| `what_makes_stay_longer` | `retention_drivers` |
| `what_drives_return` | `repeat_visit_signals` |
| `decision_factors` | `decision_trigger` |
| `archetype_derived` | `behavioral_segment` (empirically derived) |
| `group_role` | `social_behavior` pattern |

Pipeline B **validates and enriches** the demand side — it does not replace the survey.

### Concrete example

> Current: Party Seeker wants `live_music` → venue lacks `live_music` → prescribe music.
>
> With Pipeline B: Party Seeker behavioral segment shows `live_music` absence in exit signals
> only 31% of the time. Service dignity violations appear in 67% of exit signals.
> **Intervention priority flips from music to service.**

---

## Module 3 Connection (Deferred)

Pipeline B's person-level behavioral segments would sharpen Module 3 music psychology targeting.

Current M3 limitation: music prescriptions are archetype-level — *"Party Seekers → 120-130 BPM"*.

With Pipeline B: prescriptions could target specific behavioral sub-segments (which Party Seeker
types respond to energy vs. intimacy vs. authenticity) and account for the actual friction
causing exit before music even has a chance to work.

---

## Next Steps (Agreed, Still Pending)

1. **Design Stage 1** — the person fingerprint extractor (decision logic parsing layer, conjunction/contrast markers)
2. **Decide data routing** — does Google Raw Scrapper data feed Pipeline A, Pipeline B, or both?
3. **Module 3 augmentation** — music psychology sub-segment targeting via Pipeline B segments
4. **Zomato pipeline** — when Zomato extraction is ready, feed it into both pipelines

-- F5: persist vector_confidence flag from step_5b_similarity pipeline output
-- Run once before next step5b loader run
ALTER TABLE venue_vectors
    ADD COLUMN IF NOT EXISTS vector_confidence TEXT DEFAULT 'behavioral_evidence';

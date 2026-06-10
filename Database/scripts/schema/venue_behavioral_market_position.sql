CREATE TABLE IF NOT EXISTS behavioral_districts (
    district_id               VARCHAR(160) PRIMARY KEY,
    source                    VARCHAR(50) NOT NULL DEFAULT 'blended',
    city                      VARCHAR(100) NOT NULL,
    geo_cell                  VARCHAR(80),
    district_label            VARCHAR(200) NOT NULL,
    behavioral_signature      JSONB NOT NULL,
    venue_count               INTEGER NOT NULL,
    avg_state_energy          DECIMAL(6,4),
    avg_behavioral_entropy    DECIMAL(6,4),
    avg_niche_saturation      DECIMAL(6,4),
    centroid_lat              DECIMAL(9,6),
    centroid_lng              DECIMAL(9,6),
    top_dimensions            JSONB,
    details                   JSONB,
    pipeline_version          VARCHAR(80),
    computed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_behavioral_districts_city_source
    ON behavioral_districts(city, source);

CREATE TABLE IF NOT EXISTS venue_behavioral_market_position (
    venue_id                  INTEGER PRIMARY KEY REFERENCES venues(id) ON DELETE CASCADE,
    source                    VARCHAR(50) NOT NULL DEFAULT 'blended',
    district_id               VARCHAR(160) REFERENCES behavioral_districts(district_id) ON DELETE SET NULL,
    behavioral_district       VARCHAR(200) NOT NULL,
    state_energy              DECIMAL(6,4),
    energy_band               VARCHAR(20),
    anomaly_score             DECIMAL(8,4),
    is_anomaly                BOOLEAN DEFAULT FALSE,
    behavioral_entropy        DECIMAL(6,4),
    niche_saturation          DECIMAL(6,4),
    district_size             INTEGER,
    signature_family          VARCHAR(120),
    local_density             DECIMAL(6,4),
    top_dimensions            JSONB,
    details                   JSONB,
    pipeline_version          VARCHAR(80),
    computed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vbmp_source_district
    ON venue_behavioral_market_position(source, district_id);

CREATE INDEX IF NOT EXISTS idx_vbmp_city_energy
    ON venue_behavioral_market_position(source, state_energy DESC);

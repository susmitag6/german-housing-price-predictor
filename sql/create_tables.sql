CREATE TABLE IF NOT EXISTS listings (

    id SERIAL PRIMARY KEY,

    source_listing_id VARCHAR(100) UNIQUE,

    state VARCHAR(100),
    region VARCHAR(150),

    living_space NUMERIC,
    rooms NUMERIC,
    year_built INTEGER,
    lot_area NUMERIC,

    condition VARCHAR(100),
    building_type VARCHAR(100),

    asking_price NUMERIC,

    predicted_price NUMERIC,
    valuation_delta NUMERIC,
    valuation_delta_pct NUMERIC,

    source VARCHAR(100),

    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    predicted_at TIMESTAMP
);

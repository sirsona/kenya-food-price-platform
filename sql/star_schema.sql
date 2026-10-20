-- Kenya Food Price & Inflation Platform
-- Milestone 1 target star schema (PostgreSQL 16).
--
-- The loader, marts and governance tables are added in later milestones.

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_source (
    source_key       SERIAL PRIMARY KEY,
    source_code      TEXT NOT NULL UNIQUE,
    source_name      TEXT NOT NULL,
    publisher        TEXT,
    source_type      TEXT NOT NULL,
    landing_url      TEXT,
    license          TEXT,
    update_frequency TEXT,
    citation         TEXT,
    coverage_start   DATE,
    coverage_end     DATE,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key       INTEGER PRIMARY KEY,
    full_date      DATE NOT NULL UNIQUE,
    year           INTEGER NOT NULL,
    quarter        INTEGER NOT NULL,
    month          INTEGER NOT NULL,
    month_name     TEXT NOT NULL,
    month_short    TEXT NOT NULL,
    month_start    DATE NOT NULL,
    month_end      DATE NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end   BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.dim_county (
    county_key   SERIAL PRIMARY KEY,
    county_code  TEXT NOT NULL UNIQUE,
    county_number INTEGER NOT NULL UNIQUE,
    county_name  TEXT NOT NULL UNIQUE,
    region       TEXT NOT NULL,
    area_sqkm    NUMERIC(12, 2),
    center_lat   NUMERIC(10, 6),
    center_lon   NUMERIC(10, 6)
);

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key  SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    category     TEXT NOT NULL,
    default_unit TEXT NOT NULL CHECK (default_unit IN ('kg', 'L', 'unit')),
    is_food      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_product_alias (
    alias_key        SERIAL PRIMARY KEY,
    product_key      INTEGER NOT NULL REFERENCES warehouse.dim_product(product_key),
    alias_name       TEXT NOT NULL,
    alias_normalized TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_unit (
    unit_key          SERIAL PRIMARY KEY,
    unit_native       TEXT NOT NULL UNIQUE,
    unit_standard     TEXT NOT NULL CHECK (unit_standard IN ('kg', 'L', 'unit')),
    conversion_factor NUMERIC(18, 8) NOT NULL CHECK (conversion_factor > 0),
    description       TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.dim_market (
    market_key             SERIAL PRIMARY KEY,
    source_key             INTEGER NOT NULL REFERENCES warehouse.dim_source(source_key),
    source_market_id       TEXT NOT NULL,
    market_name            TEXT NOT NULL,
    market_name_normalized TEXT NOT NULL,
    county_key             INTEGER REFERENCES warehouse.dim_county(county_key),
    latitude               NUMERIC(10, 6),
    longitude              NUMERIC(10, 6),
    admin1_name            TEXT,
    admin2_name            TEXT,
    first_seen             DATE,
    last_seen              DATE,
    UNIQUE (source_key, source_market_id)
);

CREATE INDEX IF NOT EXISTS ix_dim_market_name_county
    ON warehouse.dim_market (market_name_normalized, county_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_price_observation (
    price_observation_key BIGSERIAL PRIMARY KEY,
    date_key              INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    observed_date         DATE NOT NULL,
    month                 DATE NOT NULL,
    market_key            INTEGER NOT NULL REFERENCES warehouse.dim_market(market_key),
    product_key           INTEGER NOT NULL REFERENCES warehouse.dim_product(product_key),
    source_key            INTEGER NOT NULL REFERENCES warehouse.dim_source(source_key),
    price_type            TEXT NOT NULL,
    price_flag            TEXT,
    price_native          NUMERIC(18, 4),
    unit_native           TEXT NOT NULL,
    price_kes             NUMERIC(18, 4) NOT NULL CHECK (price_kes > 0),
    price_usd             NUMERIC(18, 4),
    price_low             NUMERIC(18, 4),
    price_high            NUMERIC(18, 4),
    unit_standard         TEXT NOT NULL CHECK (unit_standard IN ('kg', 'L', 'unit')),
    conversion_factor     NUMERIC(18, 8),
    is_imputed            BOOLEAN NOT NULL DEFAULT FALSE,
    confidence_score      NUMERIC(5, 4) CHECK (confidence_score BETWEEN 0 AND 1),
    is_outlier            BOOLEAN NOT NULL DEFAULT FALSE,
    run_id                UUID,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (
        source_key, market_key, product_key, observed_date,
        price_type, unit_native, unit_standard
    )
);

CREATE INDEX IF NOT EXISTS ix_fact_price_month
    ON warehouse.fact_price_observation (month);
CREATE INDEX IF NOT EXISTS ix_fact_price_market_product
    ON warehouse.fact_price_observation (market_key, product_key, month);
CREATE INDEX IF NOT EXISTS ix_fact_price_source
    ON warehouse.fact_price_observation (source_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_food_price_index (
    food_index_key        BIGSERIAL PRIMARY KEY,
    date_key              INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    month                 DATE NOT NULL,
    market_key            INTEGER NOT NULL REFERENCES warehouse.dim_market(market_key),
    source_key            INTEGER NOT NULL REFERENCES warehouse.dim_source(source_key),
    index_value           NUMERIC(18, 6) NOT NULL CHECK (index_value > 0),
    inflation_yoy_pct     NUMERIC(10, 4),
    confidence_score      NUMERIC(5, 4) CHECK (confidence_score BETWEEN 0 AND 1),
    spatially_interpolated BOOLEAN NOT NULL DEFAULT FALSE,
    is_outlier            BOOLEAN NOT NULL DEFAULT FALSE,
    run_id                UUID,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_key, market_key, month)
);

CREATE INDEX IF NOT EXISTS ix_fact_index_month
    ON warehouse.fact_food_price_index (month);

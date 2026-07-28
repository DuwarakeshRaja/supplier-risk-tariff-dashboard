-- Supplier Risk & Tariff Exposure Dashboard
-- SQLite schema

DROP TABLE IF EXISTS risk_scores;
DROP TABLE IF EXISTS suppliers;

CREATE TABLE suppliers (
    supplier_id       TEXT PRIMARY KEY,
    supplier_name     TEXT NOT NULL,
    country           TEXT NOT NULL,
    category          TEXT NOT NULL,
    annual_spend_usd  REAL NOT NULL CHECK (annual_spend_usd >= 0),
    tariff_rate       REAL NOT NULL CHECK (tariff_rate >= 0 AND tariff_rate <= 1),
    lead_time_days    INTEGER NOT NULL CHECK (lead_time_days >= 0),
    single_source     INTEGER NOT NULL CHECK (single_source IN (0, 1))
);

CREATE TABLE risk_scores (
    supplier_id          TEXT PRIMARY KEY REFERENCES suppliers(supplier_id),
    spend_share          REAL,
    spend_score          REAL,
    tariff_score         REAL,
    single_source_score  REAL,
    lead_time_score      REAL,
    risk_score           REAL,
    risk_tier            TEXT
);

CREATE INDEX idx_suppliers_country ON suppliers(country);
CREATE INDEX idx_suppliers_category ON suppliers(category);

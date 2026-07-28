-- Supplier Risk & Tariff Exposure Dashboard
-- Analytical queries used to drive dashboard panels and resume-level insights.
-- Run against supplier_risk.db (SQLite), e.g.: sqlite3 supplier_risk.db < sql/queries.sql

-- 1. Total spend and blended tariff exposure by country
SELECT
    country,
    COUNT(*)                                   AS supplier_count,
    ROUND(SUM(annual_spend_usd), 0)            AS total_spend_usd,
    ROUND(AVG(tariff_rate) * 100, 1)           AS avg_tariff_pct,
    ROUND(SUM(annual_spend_usd * tariff_rate), 0) AS estimated_tariff_cost_usd
FROM suppliers
GROUP BY country
ORDER BY total_spend_usd DESC;

-- 2. Spend concentration: top 5 suppliers' share of total spend
SELECT
    supplier_id,
    supplier_name,
    country,
    annual_spend_usd,
    ROUND(100.0 * annual_spend_usd / (SELECT SUM(annual_spend_usd) FROM suppliers), 2) AS pct_of_total_spend
FROM suppliers
ORDER BY annual_spend_usd DESC
LIMIT 5;

-- 3. Single-source suppliers with high spend (concentration + dependency risk)
SELECT
    supplier_id,
    supplier_name,
    country,
    category,
    annual_spend_usd,
    tariff_rate
FROM suppliers
WHERE single_source = 1
ORDER BY annual_spend_usd DESC;

-- 4. High risk tier: % of total spend flagged, and supplier list
SELECT
    r.risk_tier,
    COUNT(*)                                AS supplier_count,
    ROUND(SUM(s.annual_spend_usd), 0)       AS spend_usd,
    ROUND(100.0 * SUM(s.annual_spend_usd) /
        (SELECT SUM(annual_spend_usd) FROM suppliers), 2) AS pct_of_total_spend
FROM risk_scores r
JOIN suppliers s ON s.supplier_id = r.supplier_id
GROUP BY r.risk_tier
ORDER BY spend_usd DESC;

-- 5. Top 5 highest-risk suppliers overall
SELECT
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.category,
    s.annual_spend_usd,
    s.tariff_rate,
    s.single_source,
    r.risk_score,
    r.risk_tier
FROM risk_scores r
JOIN suppliers s ON s.supplier_id = r.supplier_id
ORDER BY r.risk_score DESC
LIMIT 5;

-- 6. Category-level risk rollup
SELECT
    s.category,
    COUNT(*)                          AS supplier_count,
    ROUND(SUM(s.annual_spend_usd), 0) AS spend_usd,
    ROUND(AVG(r.risk_score), 3)       AS avg_risk_score
FROM suppliers s
JOIN risk_scores r ON r.supplier_id = s.supplier_id
GROUP BY s.category
ORDER BY avg_risk_score DESC;

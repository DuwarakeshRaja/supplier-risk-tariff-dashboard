# Supplier Risk & Tariff Exposure Dashboard

A simulated procurement analytics project that identifies which suppliers pose
the greatest combined risk from **spend concentration, tariff exposure, and
single-source dependency** — the kind of analysis a sourcing/planning team
would run before a tariff change hits margins or a disruption hits a
single-source supplier.

Built to extend hands-on SAP/supply-chain experience with a SQL + Python
analytics workflow.

## Problem

Under the current U.S. tariff environment, sourcing teams need to know, at a
glance: *which suppliers would hurt the most if their country's tariff rate
rose, or if they went down entirely?* A supplier can be risky for more than
one reason — high spend, high tariff exposure, or no backup supplier — and
those risks compound. This project scores and ranks suppliers on all three.

## Approach

1. **Simulate data** (`data/generate_data.py`) — 65 suppliers across 16
   countries and 10 categories, with a Pareto-distributed spend curve (a
   realistic "vital few" concentration), country-level tariff rates modeled
   on the 2026 U.S. tariff landscape, lead times, and single-source flags.
2. **Store & query in SQL** (`sql/`) — SQLite schema for `suppliers` and
   `risk_scores`, loaded via `sql/load_data.py`. `sql/queries.sql` holds the
   analytical queries (spend/tariff by country, top risk suppliers, spend
   concentration, category rollups) used to drive the results below.
3. **Score risk in Python** (`analysis/risk_scoring.py`) — pandas model that
   normalizes and weights four risk drivers into one composite score:

   | Driver | Weight | Rationale |
   |---|---|---|
   | Spend concentration | 35% | How much is riding on this one supplier |
   | Tariff exposure | 30% | Country-level tariff rate |
   | Single-source flag | 20% | No qualified backup supplier |
   | Lead time | 15% | Slower to react if disrupted |

   Suppliers are ranked and split into **High / Medium / Low** risk tiers
   (top 20% / next 30% / bottom 50% by score).
4. **Visualize** (`dashboard/build_dashboard.py`) — self-contained Plotly
   HTML dashboard: spend-by-country colored by tariff rate, spend-by-risk-tier
   breakdown, and the top 10 highest-risk suppliers.

## Results (from this simulated run)

- **42.2% of total spend ($4.57M of $10.84M) is concentrated in "High" risk
  suppliers** — only 13 of 65 suppliers (20%), confirming spend risk is
  concentrated, not spread evenly.
- **Top 5 highest-risk suppliers:**

  | Supplier | Country | Annual Spend | Tariff Rate | Single-Sourced | Risk Score |
  |---|---|---|---|---|---|
  | Horizon Technologies | Mexico | $2,936,000 | 25.0% | Yes | 0.827 |
  | Titan Technologies | China | $217,200 | 30.8% | Yes | 0.657 |
  | Argon Industries | China | $102,300 | 29.8% | Yes | 0.624 |
  | Anchor Systems | China | $46,000 | 28.7% | Yes | 0.589 |
  | Yield Systems | China | $76,200 | 30.2% | Yes | 0.585 |

- Every top-5 supplier is single-sourced — the model surfaces exactly the
  suppliers a diversification effort should target first.

Re-running `analysis/risk_scoring.py` prints this summary (and regenerating
the data with a different seed will change the exact numbers — the pipeline,
not the specific figures, is the point).

## How to run

```bash
pip install -r requirements.txt

python data/generate_data.py        # -> data/suppliers.csv
python sql/load_data.py             # -> supplier_risk.db
python analysis/risk_scoring.py     # -> analysis/risk_scores.csv + console summary
python dashboard/build_dashboard.py # -> dashboard/supplier_risk_dashboard.html
```

Open `dashboard/supplier_risk_dashboard.html` in a browser to explore the
interactive dashboard.

## Project structure

```
data/          simulated dataset + generator
sql/           schema, load script, analytical queries
analysis/      pandas risk-scoring model + scored output
dashboard/     Plotly dashboard builder + generated HTML
```

## Tech stack

Python (pandas, numpy, plotly), SQL (SQLite), Excel-comparable analytics
reasoning carried over from Excel-based demand forecasting experience.

## Notes

All data is synthetic, generated for demonstration purposes. Tariff rates are
approximate and illustrative, not sourced from an official tariff schedule.

"""
Supplier risk-scoring model.

Combines four risk drivers into a single composite score per supplier:
  - spend concentration  (how much of total spend rides on this supplier)
  - tariff exposure       (country-level tariff rate applied to this supplier)
  - single-source flag    (no qualified alternate supplier)
  - lead time             (longer lead time = slower to react to a disruption)

Each driver is min-max normalized to [0, 1], then combined with weights
that reflect relative business impact (spend and tariff exposure weighted
highest, since those drive direct cost/margin risk).

Run:
    python analysis/risk_scoring.py
Reads:
    supplier_risk.db (suppliers table)
Writes:
    analysis/risk_scores.csv
    supplier_risk.db (risk_scores table)
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "supplier_risk.db"
OUTPUT_CSV = ROOT / "analysis" / "risk_scores.csv"

WEIGHTS = {
    "spend_score": 0.35,
    "tariff_score": 0.30,
    "single_source_score": 0.20,
    "lead_time_score": 0.15,
}

# Suppliers ranked in the top HIGH_PCT of risk_score are "High" risk,
# next MED_PCT are "Medium", the rest are "Low".
HIGH_PCT = 0.20
MED_PCT = 0.30


def min_max(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.0, index=series.index)
    return (series - lo) / (hi - lo)


def score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["spend_share"] = out["annual_spend_usd"] / out["annual_spend_usd"].sum()
    out["spend_score"] = min_max(out["spend_share"])
    out["tariff_score"] = min_max(out["tariff_rate"])
    out["single_source_score"] = out["single_source"].astype(float)
    out["lead_time_score"] = min_max(out["lead_time_days"])

    out["risk_score"] = sum(out[col] * w for col, w in WEIGHTS.items())

    high_cut = out["risk_score"].quantile(1 - HIGH_PCT)
    med_cut = out["risk_score"].quantile(1 - HIGH_PCT - MED_PCT)

    def tier(v: float) -> str:
        if v >= high_cut:
            return "High"
        if v >= med_cut:
            return "Medium"
        return "Low"

    out["risk_tier"] = out["risk_score"].apply(tier)
    return out


def summarize(scored: pd.DataFrame) -> None:
    total_spend = scored["annual_spend_usd"].sum()
    tier_spend = scored.groupby("risk_tier")["annual_spend_usd"].sum().sort_values(ascending=False)

    print("=== Supplier Risk Summary ===")
    print(f"Total simulated annual spend: ${total_spend:,.0f}")
    print(f"Suppliers scored: {len(scored)}\n")

    for tier_name, spend in tier_spend.items():
        pct = 100 * spend / total_spend
        n = (scored["risk_tier"] == tier_name).sum()
        print(f"  {tier_name:<7} risk: {n:>2} suppliers | ${spend:>12,.0f} | {pct:5.1f}% of total spend")

    print("\nTop 5 suppliers by risk score:")
    top5 = scored.sort_values("risk_score", ascending=False).head(5)
    for _, row in top5.iterrows():
        print(
            f"  {row['supplier_id']} {row['supplier_name']:<22} "
            f"{row['country']:<14} spend=${row['annual_spend_usd']:>10,.0f} "
            f"tariff={row['tariff_rate']*100:4.1f}% "
            f"single_source={'Y' if row['single_source'] else 'N'} "
            f"risk_score={row['risk_score']:.3f}"
        )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        suppliers = pd.read_sql("SELECT * FROM suppliers", conn)
        scored = score(suppliers)

        cols = [
            "supplier_id", "spend_share", "spend_score", "tariff_score",
            "single_source_score", "lead_time_score", "risk_score", "risk_tier",
        ]
        scored[cols].to_sql("risk_scores", conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()

    scored.sort_values("risk_score", ascending=False).to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {OUTPUT_CSV}\n")
    summarize(scored)


if __name__ == "__main__":
    main()

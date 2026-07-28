"""
Builds a self-contained interactive HTML dashboard (Plotly) from the
scored supplier data in supplier_risk.db.

Run:
    python dashboard/build_dashboard.py
Output:
    dashboard/supplier_risk_dashboard.html
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "supplier_risk.db"
OUTPUT_HTML = ROOT / "dashboard" / "supplier_risk_dashboard.html"

# --- palette (validated categorical / sequential / status roles) ---
STATUS = {"Low": "#0ca30c", "Medium": "#fab219", "High": "#d03b3b"}
SEQUENTIAL_BLUE = [
    [0.00, "#cde2fb"], [0.15, "#9ec5f4"], [0.30, "#6da7ec"],
    [0.45, "#3987e5"], [0.60, "#256abf"], [0.75, "#184f95"],
    [1.00, "#0d366b"],
]
INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"


def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(
            """
            SELECT s.*, r.risk_score, r.risk_tier
            FROM suppliers s
            JOIN risk_scores r ON r.supplier_id = s.supplier_id
            """,
            conn,
        )
    finally:
        conn.close()
    return df


def build(df: pd.DataFrame) -> go.Figure:
    total_spend = df["annual_spend_usd"].sum()

    by_country = (
        df.groupby("country")
        .agg(spend=("annual_spend_usd", "sum"), tariff=("tariff_rate", "mean"))
        .sort_values("spend", ascending=True)
        .reset_index()
    )

    by_tier = (
        df.groupby("risk_tier")["annual_spend_usd"].sum()
        .reindex(["High", "Medium", "Low"])
        .reset_index()
    )

    top_risk = df.sort_values("risk_score", ascending=False).head(10).iloc[::-1]

    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"type": "xy"}, {"type": "domain"}],
               [{"type": "xy", "colspan": 2}, None]],
        subplot_titles=(
            "Spend by Country (color = avg. tariff rate)",
            "Spend by Risk Tier",
            "Top 10 Suppliers by Risk Score",
        ),
        row_heights=[0.5, 0.5],
        vertical_spacing=0.14,
        horizontal_spacing=0.12,
    )

    # Panel A: spend by country, bar length = spend, color = tariff rate (sequential)
    fig.add_trace(
        go.Bar(
            y=by_country["country"], x=by_country["spend"],
            orientation="h",
            marker=dict(
                color=by_country["tariff"], colorscale=SEQUENTIAL_BLUE,
                colorbar=dict(title="Tariff", tickformat=".0%", x=0.44, len=0.42, y=0.79),
                line=dict(width=0),
            ),
            customdata=by_country["tariff"],
            hovertemplate="<b>%{y}</b><br>Spend: $%{x:,.0f}<br>Avg tariff: %{customdata:.1%}<extra></extra>",
            showlegend=False,
        ),
        row=1, col=1,
    )

    # Panel B: spend by risk tier, donut, status colors
    fig.add_trace(
        go.Pie(
            labels=by_tier["risk_tier"], values=by_tier["annual_spend_usd"],
            hole=0.55,
            marker=dict(colors=[STATUS[t] for t in by_tier["risk_tier"]]),
            textinfo="label+percent",
            textfont=dict(color=INK),
            hovertemplate="<b>%{label} risk</b><br>Spend: $%{value:,.0f}<br>%{percent}<extra></extra>",
        ),
        row=1, col=2,
    )

    # Panel C: top 10 riskiest suppliers, status-colored bars
    fig.add_trace(
        go.Bar(
            y=top_risk["supplier_name"] + " (" + top_risk["country"] + ")",
            x=top_risk["risk_score"],
            orientation="h",
            marker=dict(color=[STATUS[t] for t in top_risk["risk_tier"]], line=dict(width=0)),
            customdata=top_risk[["annual_spend_usd", "tariff_rate", "single_source"]],
            hovertemplate=(
                "<b>%{y}</b><br>Risk score: %{x:.3f}"
                "<br>Spend: $%{customdata[0]:,.0f}"
                "<br>Tariff: %{customdata[1]:.1%}"
                "<br>Single-sourced: %{customdata[2]}<extra></extra>"
            ),
            showlegend=False,
        ),
        row=2, col=1,
    )

    fig.update_layout(
        title=dict(
            text=(
                f"Supplier Risk & Tariff Exposure Dashboard"
                f"<br><sup>{len(df)} suppliers &nbsp;|&nbsp; "
                f"${total_spend:,.0f} total simulated annual spend &nbsp;|&nbsp; "
                f"{100*df.loc[df.risk_tier=='High','annual_spend_usd'].sum()/total_spend:.1f}% "
                f"of spend flagged High risk</sup>"
            ),
            font=dict(color=INK, size=20),
        ),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=SECONDARY_INK, family="system-ui, -apple-system, Segoe UI, sans-serif"),
        height=900,
        margin=dict(t=110, l=10, r=10, b=40),
        legend=dict(bgcolor=SURFACE),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=INK))
    fig.update_xaxes(title_text="Annual spend (USD)", row=1, col=1, tickformat="$,.0f")
    fig.update_xaxes(title_text="Composite risk score", row=2, col=1)

    return fig


def main() -> None:
    df = load_data()
    fig = build(df)
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn")
    print(f"Wrote {OUTPUT_HTML}")


if __name__ == "__main__":
    main()

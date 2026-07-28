"""
Loads data/suppliers.csv into a SQLite database (supplier_risk.db) using
the schema defined in sql/schema.sql.

Run:
    python sql/load_data.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "supplier_risk.db"
CSV_PATH = ROOT / "data" / "suppliers.csv"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"


def main() -> None:
    df = pd.read_csv(CSV_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        df.to_sql("suppliers", conn, if_exists="append", index=False)
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        print(f"Loaded {count} suppliers into {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

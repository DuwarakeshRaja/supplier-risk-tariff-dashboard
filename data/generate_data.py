"""
Generates a simulated supplier procurement dataset for the
Supplier Risk & Tariff Exposure Dashboard project.

Data is synthetic but modeled on realistic 2026 sourcing patterns:
country mix, category mix, spend distribution (Pareto-like, since
real procurement portfolios are dominated by a handful of large
suppliers), and country-level tariff rates approximating the
US tariff environment.

Run:
    python data/generate_data.py
Output:
    data/suppliers.csv
"""

import numpy as np
import pandas as pd

SEED = 42
N_SUPPLIERS = 65
OUTPUT_PATH = "data/suppliers.csv"

# Country -> (weight in supplier base, approximate effective US tariff rate)
COUNTRIES = {
    "China": (0.20, 0.30),
    "Mexico": (0.14, 0.25),
    "Vietnam": (0.10, 0.20),
    "India": (0.10, 0.15),
    "Taiwan": (0.07, 0.20),
    "South Korea": (0.06, 0.15),
    "Japan": (0.06, 0.15),
    "Germany": (0.06, 0.15),
    "Malaysia": (0.05, 0.19),
    "Thailand": (0.04, 0.19),
    "Indonesia": (0.03, 0.19),
    "Bangladesh": (0.03, 0.20),
    "Brazil": (0.02, 0.10),
    "Canada": (0.02, 0.10),
    "United Kingdom": (0.01, 0.10),
    "United States": (0.01, 0.00),
}

CATEGORIES = [
    "Electronics Components",
    "Semiconductors",
    "Packaging Materials",
    "Raw Metals",
    "Industrial Equipment",
    "Automotive Parts",
    "Textiles",
    "Chemicals",
    "Logistics Services",
    "Office Supplies",
]

# Categories more likely to be single-sourced (specialty / high switching cost)
HIGH_SWITCHING_COST_CATEGORIES = {"Semiconductors", "Industrial Equipment", "Chemicals"}

NAME_PREFIXES = [
    "Summit", "Pacific", "Meridian", "Vertex", "Atlas", "Nova", "Ironclad",
    "Crestline", "Horizon", "Union", "Cobalt", "Granite", "Silverline",
    "Northgate", "Anchor", "Delta", "Redwood", "Sterling", "Bluewave",
    "Falcon", "Trident", "Zenith", "Harbor", "Titan", "Vantage", "Argon",
    "Beacon", "Cascade", "Element", "Frontier", "Keystone", "Lumen",
    "Orbit", "Pioneer", "Quantum", "Ridgeline", "Solstice", "Vanguard",
    "Wavelength", "Yield",
]
NAME_SUFFIXES = [
    "Industries", "Manufacturing", "Components", "Supply Co.", "Group",
    "Materials", "Technologies", "Systems", "Holdings", "Partners",
]


def generate() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    countries = list(COUNTRIES.keys())
    country_weights = np.array([v[0] for v in COUNTRIES.values()])
    country_weights = country_weights / country_weights.sum()

    chosen_countries = rng.choice(countries, size=N_SUPPLIERS, p=country_weights)
    chosen_categories = rng.choice(CATEGORIES, size=N_SUPPLIERS)

    # Pareto-distributed annual spend: a handful of suppliers carry most of the spend.
    # Shape ~1.3 gives a realistic "vital few" concentration without being extreme.
    raw_spend = (rng.pareto(a=1.3, size=N_SUPPLIERS) + 1) * 45_000
    annual_spend = np.round(raw_spend, -2)  # round to nearest $100

    tariff_rate = np.array([COUNTRIES[c][1] for c in chosen_countries])
    tariff_jitter = rng.normal(0, 0.01, size=N_SUPPLIERS)
    tariff_rate = np.clip(tariff_rate + tariff_jitter, 0, 0.45)

    lead_time_days = rng.integers(15, 121, size=N_SUPPLIERS)

    single_source_prob = np.array([
        0.45 if cat in HIGH_SWITCHING_COST_CATEGORIES else 0.18
        for cat in chosen_categories
    ])
    single_source = rng.random(N_SUPPLIERS) < single_source_prob

    used_names = set()
    names = []
    while len(names) < N_SUPPLIERS:
        candidate = f"{rng.choice(NAME_PREFIXES)} {rng.choice(NAME_SUFFIXES)}"
        if candidate not in used_names:
            used_names.add(candidate)
            names.append(candidate)

    supplier_ids = [f"S{str(i + 1).zfill(3)}" for i in range(N_SUPPLIERS)]

    df = pd.DataFrame({
        "supplier_id": supplier_ids,
        "supplier_name": names,
        "country": chosen_countries,
        "category": chosen_categories,
        "annual_spend_usd": annual_spend,
        "tariff_rate": np.round(tariff_rate, 4),
        "lead_time_days": lead_time_days,
        "single_source": single_source.astype(int),
    })

    df = df.sort_values("annual_spend_usd", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = generate()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(df)} suppliers -> {OUTPUT_PATH}")
    print(f"Total simulated annual spend: ${df['annual_spend_usd'].sum():,.0f}")

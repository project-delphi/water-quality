"""Analysis of Colombian municipal water quality: one importable script, run with
`uv run python scripts/analysis.py`. Reads data/ (never changes it) and writes outputs/.

IRCA is the utility-supplied (prestadores) IRCA from INS open data (datos.gov.co nxt2-39c3).
Outcomes (infant mortality, Saber 11, dropout) are never used as clustering features.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "water_municipal.csv"
OUTPUTS = ROOT / "outputs"

FIRST_YEAR, LAST_YEAR = 2016, 2023          # MDM starts in 2016
FEATURES = ["irca", "water_coverage", "sewer_coverage", "ipm", "rural_share",
            "altitude_m", "rainfall_mm", "mdm", "log_sgp_water_pc"]
OUTCOMES = ["infant_mortality", "saber11_mean", "dropout_rate"]
KEYS = ["divipola", "municipio", "departamento", "region", "zone", "year"]
TOTAL_FILL = {"water_coverage": "water_coverage_total", "sewer_coverage": "sewer_coverage_total"}


def load(path=DATA):
    """The analysis table, with DIVIPOLA codes as text."""
    return pd.read_csv(path, dtype={"divipola": str, "dpto_code": str})


def prepare(df, verbose=False):
    """Select, transform, impute and standardise: one row per kept zone-year.

    1. select municipality zone-years 2016–2023 with IRCA;
    2. transform: log SGP per person; department capitals (codes ending 001) have no
       urban/rural coverage split, so their urban rows take the municipal total, flagged
       in <col>_from_total;
    3. drop rows missing more than 2 features, fill the rest with the year × zone median,
       flagged in <col>_imputed;
    4. add z_<col>, the z-score of each feature within its year.
    """
    counts = {}
    d = df[df["entity_type"] == "municipality"]
    d = d[d["year"].between(FIRST_YEAR, LAST_YEAR)].copy()
    counts["municipality_rows"] = len(d)
    has_irca = d["irca"].notna()
    counts["dropped_no_irca"] = int((~has_irca).sum())
    d = d[has_irca].copy()

    # Transform: skewed nominal pesos per person -> log.
    d["log_sgp_water_pc"] = np.log(d["sgp_water_pc"].where(d["sgp_water_pc"] > 0))

    # Capitals' urban rows take the municipal coverage total, flagged.
    capital_urban = d["divipola"].str.endswith("001") & (d["zone"] == "urban")
    for col, total in TOTAL_FILL.items():
        fill = capital_urban & d[total].notna()
        d[col] = d[col].mask(fill, d[total])
        d[f"{col}_from_total"] = fill.astype(int)

    # Impute: drop rows missing more than two features, fill the rest.
    n_missing = d[FEATURES].isna().sum(axis=1)
    counts["dropped_too_many_missing"] = int((n_missing > 2).sum())
    d = d[n_missing <= 2].copy()
    for col in FEATURES:
        missing = d[col].isna()
        d[f"{col}_imputed"] = missing.astype(int)
        median = d.groupby(["year", "zone"])[col].transform("median")
        d[col] = d[col].fillna(median)

    # Standardise within each year.
    for col in FEATURES:
        by_year = d.groupby("year")[col]
        d[f"z_{col}"] = (d[col] - by_year.transform("mean")) / by_year.transform("std", ddof=0)

    counts["kept"] = len(d)
    counts["kept_urban"] = int((d["zone"] == "urban").sum())
    counts["kept_rural"] = int((d["zone"] == "rural").sum())
    counts["municipalities"] = int(d["divipola"].nunique())
    counts["rows_with_any_imputed"] = int(d[[f"{c}_imputed" for c in FEATURES]].any(axis=1).sum())
    counts["capital_urban_rows_filled_from_total"] = int(d["water_coverage_from_total"].sum())
    if verbose:
        for k, v in counts.items():
            print(f"{k}: {v:,}")
    flags = ([f"{c}_from_total" for c in TOTAL_FILL] + [f"{c}_imputed" for c in FEATURES])
    cols = KEYS + FEATURES + [f"z_{c}" for c in FEATURES] + OUTCOMES + flags
    return d[cols].reset_index(drop=True)


if __name__ == "__main__":
    OUTPUTS.mkdir(exist_ok=True)
    prepared = prepare(load(), verbose=True)
    prepared.to_parquet(OUTPUTS / "prepared.parquet", index=False)
    print(f"wrote outputs/prepared.parquet: {len(prepared):,} rows x {prepared.shape[1]} columns")

"""Colombian municipal water safety: preparation of the clustering table."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["irca", "water_coverage", "sewer_coverage", "ipm", "rural_share",
            "altitude_m", "rainfall_mm", "mdm", "log_sgp_water_pc"]


def prepare(df):
    """Municipality rows, 2016-2023, with a utility-supplied IRCA; features + flags."""
    out = df[(df["entity_type"] == "municipality")
             & df["year"].between(2016, 2023)
             & df["irca"].notna()].copy()
    # Department capitals have no urban/rural coverage split: use the municipal total
    # for their urban rows and flag every fill.
    for col in ["water_coverage", "sewer_coverage"]:
        flag = f"{col}_from_total"
        fill = ((out["zone"] == "urban") & (out["department_capital"] == 1)
                & out[col].isna() & out[f"{col}_total"].notna())
        out[flag] = fill.astype(int)
        out.loc[fill, col] = out.loc[fill, f"{col}_total"]
    out["log_sgp_water_pc"] = np.log(out["sgp_water_pc"].where(out["sgp_water_pc"] > 0))
    return out


OUTCOMES = ["infant_mortality", "saber11_mean", "saber11_n", "dropout_rate"]


def clean(prepared, log=print):
    """Drop rows missing >2 features, impute the rest, add z_<col> within year."""
    out = prepared.copy()
    n0 = len(out)
    n_missing = out[FEATURES].isna().sum(axis=1)
    out = out[n_missing <= 2].copy()
    log(f"step 1 drop rows missing more than 2 features: kept {len(out):,}, "
        f"dropped {n0 - len(out):,}")
    # median of year x zone; fall back to the year median where a whole group is empty
    for col in FEATURES:
        flag = f"{col}_imputed"
        out[flag] = out[col].isna().astype(int)
        med = out.groupby(["year", "zone"])[col].transform("median")
        med = med.fillna(out.groupby("year")[col].transform("median"))
        out[col] = out[col].fillna(med)
    log("step 2 impute with year x zone median: "
        + ", ".join(f"{c} {int(out[c + '_imputed'].sum())}" for c in FEATURES))
    for col in FEATURES:
        g = out.groupby("year")[col]
        sd = g.transform("std").replace(0, np.nan)
        out[f"z_{col}"] = ((out[col] - g.transform("mean")) / sd).fillna(0.0)
    log(f"step 3 z-scores within year added: {len(FEATURES)} z_ columns; "
        f"rows kept in total {len(out):,}, dropped in total {n0 - len(out):,} after prepare()")
    return out


def main():
    df = pd.read_csv(ROOT / "data" / "water_municipal.csv", dtype={"divipola": str})
    prepared = prepare(df)
    print(f"rows in: {len(df):,}; rows kept by prepare(): {len(prepared):,}; "
          f"dropped: {len(df) - len(prepared):,}")
    for col in ["water_coverage", "sewer_coverage"]:
        print(f"{col}_from_total filled: {int(prepared[col + '_from_total'].sum())}")
    print(prepared[FEATURES].isna().sum().rename("missing").to_string())
    ready = clean(prepared)
    (ROOT / "outputs").mkdir(exist_ok=True)
    ready.to_parquet(ROOT / "outputs" / "prepared.parquet", index=False)
    print(f"saved outputs/prepared.parquet: {ready.shape[0]:,} rows x {ready.shape[1]} columns")


if __name__ == "__main__":
    main()

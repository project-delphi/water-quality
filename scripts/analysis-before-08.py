"""Cluster Colombian municipal zones with k-means (workshop checkpoint 07).

Run from the project folder (the one that holds data/ and scripts/):

    python scripts/analysis.py

Prepares the rows (see prepare()), compares k = 2-8 by inertia and silhouette,
chooses k with an elbow rule, checks stability across seeds and writes
outputs/clusters.parquet, outputs/k_selection.csv, outputs/stability.csv and
outputs/summary.json. IRCA is the utility-supplied ("prestadores") IRCA in INS
open data, datos.gov.co nxt2-39c3.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "water_municipal.csv"
OUTPUTS = ROOT / "outputs"

FIRST_YEAR, LAST_YEAR = 2016, 2023      # MDM starts in 2016
KEYS = ["divipola", "municipio", "departamento", "region", "zone", "year"]
RAW_FEATURES = ["irca", "water_coverage", "sewer_coverage", "ipm", "rural_share",
                "altitude_m", "rainfall_mm", "mdm", "sgp_water_pc"]
FEATURES = ["irca", "water_coverage", "sewer_coverage", "ipm", "rural_share",
            "altitude_m", "rainfall_mm", "mdm", "log_sgp_water_pc"]
FEATURE_LABELS = {
    "irca": "IRCA, utility-supplied (0–100)",
    "water_coverage": "Piped water coverage (%)",
    "sewer_coverage": "Sewer coverage (%)",
    "ipm": "Multidimensional poverty, 2018 (%)",
    "rural_share": "Rural share of population",
    "altitude_m": "Altitude of head town, derived SRTM point (m)",
    "rainfall_mm": "Rainfall (mm/year)",
    "mdm": "Municipal performance, MDM",
    "log_sgp_water_pc": "Water transfers per person (log SGP)",
}
MAX_MISSING = 2                          # drop rows missing more features than this
K_RANGE = range(2, 9)
SEED = 42
N_INIT = 20
SILHOUETTE_N = 5000                      # fixed-seed sample for the silhouette
STABILITY_SEEDS = (1, 2, 3, 4, 5)
ELBOW_DROP = 0.10                        # an extra cluster must cut inertia by >= 10 %
SILHOUETTE_TOL = 0.01                    # ... and keep silhouette near the best k >= 3
# Resolución 2115 de 2007, art. 15. IRCA has one decimal, so (5, 14] means 5.1-14.
IRCA_BINS = [-0.001, 5, 14, 35, 80, 100]
IRCA_BANDS = ["No risk", "Low", "Medium", "High", "Unfit"]
# Cluster colours follow the cluster id on every page and output. The first
# four pass the dataviz validator for all pairs (scatter, maps) on white and on
# the #191919 slide background, including protan/deutan simulation.
CLUSTER_COLORS = ["#0072b2", "#009e73", "#9085e9", "#d55e00",
                  "#e69f00", "#56b4e9", "#cc79a7", "#f0e442"]
CLUSTER_MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]


# --- 1. load and select --------------------------------------------------------
def load(path: Path | str = DATA) -> pd.DataFrame:
    """Read the analysis table, keeping DIVIPOLA codes as text."""
    return pd.read_csv(path, dtype={"divipola": str, "dpto_code": str})


def irca_band(irca: pd.Series) -> pd.Series:
    """Resolución 2115 risk band for each IRCA value."""
    return pd.cut(irca, bins=IRCA_BINS, labels=IRCA_BANDS)


def floor_to(x: float, decimals: int = 3) -> str:
    """Round down for "at least" statements: 0.99859 -> "0.998", never "0.999"."""
    factor = 10 ** decimals
    return f"{np.floor(x * factor) / factor:.{decimals}f}"


def prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Select rows, transform, impute with flags and standardise within year.

    Returns the prepared rows (raw features, ``z_<feature>``, flags, outcomes)
    and a dict of row counts for each step.
    """
    counts = {}
    win = df[df["year"].between(FIRST_YEAR, LAST_YEAR)]
    counts["rows_2016_2023"] = len(win)
    # Municipalities only. San Andrés (entity_type "island") has no TerriData
    # values (data/README.md, caveat 11), so it would miss 5 of 9 features.
    d = win[win["entity_type"] == "municipality"].copy()
    counts["dropped_not_municipality"] = len(win) - len(d)
    counts["municipality_rows"] = len(d)

    has_irca = d["irca"].notna()
    counts["dropped_no_irca"] = int((~has_irca).sum())
    d = d[has_irca].copy()

    # Department capitals (code ends in 001) have no urban/rural REC split.
    # Urban capital rows take the municipal total, flagged; rural rows are not
    # filled from the total and go through the usual imputation below.
    capital_urban = d["divipola"].str.endswith("001") & (d["zone"] == "urban")
    for col in ["water_coverage", "sewer_coverage"]:
        fill = capital_urban & d[col].isna() & d[f"{col}_total"].notna()
        d[f"{col}_from_total"] = fill.astype(int)
        d.loc[fill, col] = d.loc[fill, f"{col}_total"]
    counts["capital_urban_rows_filled_from_total"] = int(d["water_coverage_from_total"].sum())

    d["log_sgp_water_pc"] = np.log(d["sgp_water_pc"])  # all values > 0

    n_missing = d[FEATURES].isna().sum(axis=1)
    keep = n_missing <= MAX_MISSING
    counts["dropped_too_many_missing"] = int((~keep).sum())
    d = d[keep].copy()

    medians = d.groupby(["year", "zone"])[FEATURES].transform("median")
    for col in FEATURES:
        d[f"{col}_imputed"] = d[col].isna().astype(int)
        d[col] = d[col].fillna(medians[col])
        counts[f"imputed_{col}"] = int(d[f"{col}_imputed"].sum())
    counts["rows_with_any_imputed"] = int(d[[f"{c}_imputed" for c in FEATURES]].any(axis=1).sum())

    # Standardise within year: removes nominal-peso drift and year-level shifts.
    grp = d.groupby("year")[FEATURES]
    z = (d[FEATURES] - grp.transform("mean")) / grp.transform(lambda s: s.std(ddof=0))
    for col in FEATURES:
        d[f"z_{col}"] = z[col]

    d["irca_band"] = irca_band(d["irca"])
    counts["kept"] = len(d)
    counts["kept_urban"] = int((d["zone"] == "urban").sum())
    counts["kept_rural"] = int((d["zone"] == "rural").sum())
    counts["municipalities"] = int(d["divipola"].nunique())
    return d.reset_index(drop=True), counts


def zmatrix(prepared: pd.DataFrame) -> np.ndarray:
    return prepared[[f"z_{c}" for c in FEATURES]].to_numpy()


# --- 2. choose k ---------------------------------------------------------------
def k_table(X: np.ndarray, zone=None, ks=K_RANGE, seed: int = SEED) -> pd.DataFrame:
    """Inertia and silhouette for each k (silhouette on a fixed-seed sample).

    With ``zone``, also the adjusted Rand index between the labels and the
    urban/rural split: 1 would mean the clusters just reproduce the zone.
    """
    rng = np.random.default_rng(seed)
    sample = rng.choice(len(X), size=min(SILHOUETTE_N, len(X)), replace=False)
    rows = []
    for k in ks:
        km = KMeans(n_clusters=k, random_state=seed, n_init=N_INIT).fit(X)
        sil = silhouette_score(X[sample], km.labels_[sample])
        row = {"k": k, "inertia": km.inertia_, "silhouette": sil}
        if zone is not None:
            row["ari_vs_zone"] = adjusted_rand_score(zone, km.labels_)
        rows.append(row)
    tab = pd.DataFrame(rows)
    tab["inertia_drop"] = -tab["inertia"].pct_change()   # share cut by adding the k-th cluster
    return tab


def choose_k(tab: pd.DataFrame) -> tuple[int, str]:
    """Elbow rule, checked against the silhouette.

    k = 2 is not considered: it mostly separates urban from rural rows (see
    ``ari_vs_zone``), which we already know. Pick the
    smallest k >= 3 after which one more cluster cuts inertia by less than
    ELBOW_DROP, provided its silhouette is within SILHOUETTE_TOL of the best k >= 3.
    """
    cand = tab[tab["k"] >= 3].reset_index(drop=True)
    best_sil = cand["silhouette"].max()
    for i, row in cand.iterrows():
        nxt = cand["inertia_drop"].iloc[i + 1] if i + 1 < len(cand) else 0.0
        if nxt < ELBOW_DROP and row["silhouette"] >= best_sil - SILHOUETTE_TOL:
            k = int(row["k"])
            reason = (f"k = {k}: the next cluster cuts inertia by only {nxt:.0%} "
                      f"(< {ELBOW_DROP:.0%}), and its silhouette {row['silhouette']:.3f} is "
                      f"within {SILHOUETTE_TOL} of the best k >= 3 ({best_sil:.3f}).")
            return k, reason
    k = int(cand.loc[cand["silhouette"].idxmax(), "k"])
    return k, f"k = {k}: no elbow; highest silhouette among k >= 3."


# --- 3. fit, order, check stability --------------------------------------------
def fit(X: np.ndarray, k: int, seed: int = SEED) -> tuple[np.ndarray, np.ndarray]:
    """k-means labels (1..k) and centroids, ordered by centroid IRCA (low to high)."""
    km = KMeans(n_clusters=k, random_state=seed, n_init=N_INIT).fit(X)
    order = np.argsort(km.cluster_centers_[:, FEATURES.index("irca")], kind="stable")
    relabel = np.empty(k, dtype=int)
    relabel[order] = np.arange(1, k + 1)
    return relabel[km.labels_], km.cluster_centers_[order]


def stability(X: np.ndarray, k: int, labels: np.ndarray, seeds=STABILITY_SEEDS) -> pd.DataFrame:
    """Adjusted Rand index between the chosen labels and refits with other seeds."""
    rows = []
    for s in seeds:
        other = KMeans(n_clusters=k, random_state=s, n_init=N_INIT).fit(X).labels_
        rows.append({"seed": s, "ari": adjusted_rand_score(labels, other)})
    return pd.DataFrame(rows)


def pca(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = PCA(n_components=2, random_state=SEED).fit(X)
    return p.transform(X), p.explained_variance_ratio_


# --- 4. run everything ------------------------------------------------------
def run(path: Path | str = DATA) -> dict:
    """Compute every result in memory. Writes nothing."""
    prepared, counts = prepare(load(path))
    X = zmatrix(prepared)
    ktab = k_table(X, zone=prepared["zone"])
    k, reason = choose_k(ktab)
    labels, centers = fit(X, k)
    stab = stability(X, k, labels)
    coords, var = pca(X)

    clustered = prepared.copy()
    clustered["cluster"] = labels
    clustered["pc1"], clustered["pc2"] = coords[:, 0], coords[:, 1]

    summary = {
        **counts, "k": k, "k_reason": reason,
        "silhouette_at_k": float(ktab.loc[ktab["k"] == k, "silhouette"].iloc[0]),
        "ari_min": float(stab["ari"].min()), "ari_mean": float(stab["ari"].mean()),
        "pca_variance_pc1": float(var[0]), "pca_variance_pc2": float(var[1]),
        "first_year": FIRST_YEAR, "last_year": LAST_YEAR, "seed": SEED, "n_init": N_INIT,
    }
    return {"prepared": prepared, "clusters": clustered, "k_table": ktab, "k": k,
            "stability": stab, "centers": centers, "summary": summary}


def output_columns() -> list[str]:
    flags = ([f"{c}_imputed" for c in FEATURES]
             + ["water_coverage_from_total", "sewer_coverage_from_total"])
    return (KEYS + ["cluster", "pc1", "pc2", "irca_band"]
            + RAW_FEATURES + ["log_sgp_water_pc"] + [f"z_{c}" for c in FEATURES]
            + flags + ["infant_mortality", "saber11_mean", "dropout_rate", "saber11_n"])


def write_outputs(res: dict, out: Path | str = OUTPUTS) -> list[Path]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "clusters.parquet": lambda p: res["clusters"][output_columns()].to_parquet(p, index=False),
        "k_selection.csv": lambda p: res["k_table"].to_csv(p, index=False),
        "stability.csv": lambda p: res["stability"].to_csv(p, index=False),
        "summary.json": lambda p: p.write_text(json.dumps(res["summary"], indent=2) + "\n"),
    }
    written = []
    for name, write in files.items():
        write(out / name)
        written.append(out / name)
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default=DATA, help="path to water_municipal.csv")
    ap.add_argument("--out", default=OUTPUTS, help="output folder")
    args = ap.parse_args()
    res = run(args.data)
    s = res["summary"]
    print(f"kept {s['kept']:,} rows ({s['kept_urban']:,} urban, {s['kept_rural']:,} rural) "
          f"from {s['municipalities']:,} municipalities")
    print(res["k_table"].round(3).to_string(index=False))
    print(s["k_reason"])
    print(f"stability: ARI >= {floor_to(s['ari_min'])} (min {s['ari_min']:.5f}) "
          f"across seeds {list(STABILITY_SEEDS)}")
    print(res["clusters"]["cluster"].value_counts().sort_index().to_string())
    for p in write_outputs(res, args.out):
        print("wrote", p.name)


if __name__ == "__main__":
    main()

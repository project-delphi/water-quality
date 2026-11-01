"""Cluster Colombian municipal zones by water, sanitation and context.

Compute once, publish many: every page of the water-quality project reads the
files this script writes to ``outputs/``.

Run it from the project folder, the one that holds ``data/`` and ``scripts/``:

    python scripts/analysis.py

Or import it and compute in memory (the workshop deck does this):

    import analysis
    res = analysis.run()          # a dict of DataFrames and numbers

Unit of analysis: one municipality x zone (urban/rural) x year, 2016-2023.
IRCA is the utility-supplied ("prestadores") IRCA in the INS open table
datos.gov.co nxt2-39c3, not INS's national total. Outcomes (infant mortality,
Saber 11, dropout) are never clustered on; they only describe the clusters.
Cluster comparisons are descriptive and do not show that water quality causes
any outcome.
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

# --- design choices ----------------------------------------------------------
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
SHORT_LABELS = {
    "irca": "IRCA", "water_coverage": "Water cov.", "sewer_coverage": "Sewer cov.",
    "ipm": "Poverty", "rural_share": "Rural share", "altitude_m": "Altitude (derived)",
    "rainfall_mm": "Rainfall", "mdm": "MDM", "log_sgp_water_pc": "log SGP/person",
}
OUTCOMES = {
    "infant_mortality": "Infant mortality (per 1,000 live births)",
    "saber11_mean": "Saber 11 mean score (0–500)",
    "dropout_rate": "School dropout, public schools (%)",
}
OUTCOME_LEVEL = {"infant_mortality": "municipality", "saber11_mean": "zone",
                 "dropout_rate": "municipality"}
# Infant mortality changes method in 2017 (modelled estimates before, observed rates
# after) and 2020 looks like another source (data/README.md, caveat 8), so every
# infant-mortality comparison uses 2017-2019 and 2021-2023 only.
INFANT_YEARS = (2017, 2018, 2019, 2021, 2022, 2023)
INFANT_NOTE = ("Infant mortality changes method in 2017 and 2020 looks like a different "
               "source (data/README.md, caveat 8), so only 2017–2019 and 2021–2023 are used.")
OUTCOME_YEARS = {"infant_mortality": INFANT_YEARS,                 # see INFANT_NOTE
                 "saber11_mean": (2016, 2017, 2019, 2020, 2022),  # published years
                 "dropout_rate": tuple(range(FIRST_YEAR, LAST_YEAR + 1))}
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
IRCA_BANDS_ES = ["Sin riesgo", "Bajo", "Medio", "Alto", "Inviable sanitariamente"]

# Cluster colours follow the cluster id on every page and output. The first
# four pass the dataviz validator for all pairs (scatter, maps) on white and on
# the #191919 slide background, including protan/deutan simulation.
CLUSTER_COLORS = ["#0072b2", "#009e73", "#9085e9", "#d55e00",
                  "#e69f00", "#56b4e9", "#cc79a7", "#f0e442"]
CLUSTER_MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
# Cluster colours used as *text* on the #191919 slides: each at least 4.5:1.
# Cluster 1's mark colour (#0072b2) is only 3.4:1 as text, so text uses a lighter blue.
CLUSTER_TEXT_COLORS = {"dark": ["#39b4dd", "#009e73", "#9085e9", "#d55e00",
                                "#e69f00", "#56b4e9", "#cc79a7", "#f0e442"]}
# IRCA bands are ordered: one orange hue, darker = more risk on white pages,
# brighter = more risk on dark slides (both pass the dataviz ordinal checks).
BAND_COLORS = {"light": ["#eea471", "#dc813b", "#c66000", "#a44700", "#803300"],
               "dark": ["#6e401e", "#9b5824", "#cb7229", "#f1944f", "#ffbe8a"]}
# No data must not read as the lowest band: near-white on white pages; on dark
# slides a near-background fill drawn with a hatch (NO_DATA_HATCH in NO_DATA_EDGE).
NO_DATA_COLOR = {"light": "#f4f4f2", "dark": "#262624"}
NO_DATA_EDGE = {"light": "#a3a39f", "dark": "#77776f"}
NO_DATA_HATCH = "////"
# z-score heatmaps: blue (below the year's mean) to red (above), grey midpoint.
DIVERGING = {"light": ["#2a78d6", "#f0efec", "#e34948"],
             "dark": ["#3987e5", "#383835", "#e66767"]}


# --- 1. load and select ------------------------------------------------------
def load(path: Path | str = DATA) -> pd.DataFrame:
    """Read the analysis table, keeping DIVIPOLA codes as text."""
    return pd.read_csv(path, dtype={"divipola": str, "dpto_code": str})


def load_geojson(path: Path | str = ROOT / "data" / "municipios.geojson",
                 for_plotly: bool = True) -> dict:
    """Municipal polygons, keyed by properties.divipola.

    The file follows RFC 7946 (exterior rings counter-clockwise). Plotly's
    d3-based maps expect the opposite winding and would draw each polygon as
    "the world minus the municipality", so rings are reversed in memory.
    """
    geo = json.loads(Path(path).read_text(encoding="utf-8"))
    if for_plotly:
        for feature in geo["features"]:
            g = feature["geometry"]
            polygons = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            for polygon in polygons:
                for ring in polygon:
                    ring.reverse()
    return geo


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


# --- 3. fit, order, check stability -------------------------------------------
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


# --- 4. name and profile -------------------------------------------------------
def name_rule(p: pd.Series) -> str:
    """Descriptive name from one cluster's profile row (see profiles()).

    "low-coverage" is relative: the cluster's mean piped-water coverage is at least
    0.5 SD below the year's average, not an absence of service. The risk word is the
    Resolución 2115 band of the cluster's median utility-supplied (prestadores) IRCA;
    individual zone-years can fall in other bands.
    """
    if p["urban_row_share"] < 0.4:
        setting = "Rural"
    elif p["z_rural_share"] <= -0.5:
        setting = "Cities and large towns"
    elif p["z_altitude_m"] <= -0.5:
        setting = "Lowland towns"
    elif p["z_altitude_m"] >= 0.5:
        setting = "Highland towns"
    else:
        setting = "Towns"
    if p["z_water_coverage"] <= -0.5:
        setting += ", low-coverage"
    risk = {"No risk": "no-risk", "Low": "low-risk", "Medium": "medium-risk",
            "High": "high-risk", "Unfit": "unfit"}[p["irca_median_band"]]
    return f"{setting}, {risk} water"


def once_per_municipality(rows: pd.DataFrame, col: str) -> pd.DataFrame:
    """Municipal outcomes repeat on both zone rows: keep one per cluster and year."""
    if OUTCOME_LEVEL[col] == "municipality":
        return rows.drop_duplicates(["cluster", "divipola", "year"])
    return rows


def profiles(clustered: pd.DataFrame) -> pd.DataFrame:
    """One row per cluster: size, mean raw and z features, outcome summaries."""
    g = clustered.groupby("cluster")
    prof = pd.DataFrame({
        "rows": g.size(),
        "municipalities": g["divipola"].nunique(),
        "urban_row_share": g["zone"].apply(lambda s: (s == "urban").mean()),
        "irca_median": g["irca"].median(),
    })
    prof["irca_median_band"] = irca_band(prof["irca_median"]).astype(str)
    prof = prof.join(g[FEATURES].mean().add_prefix("mean_"))
    prof = prof.join(g[[f"z_{c}" for c in FEATURES]].mean())
    for col in OUTCOMES:          # pooled over OUTCOME_YEARS[col]
        rows = clustered[clustered["year"].isin(OUTCOME_YEARS[col])].dropna(subset=[col])
        by = once_per_municipality(rows, col).groupby("cluster")[col]
        prof[f"{col}_mean"] = by.mean()
        prof[f"{col}_median"] = by.median()
        prof[f"{col}_n"] = by.count()
    prof["name"] = prof.apply(name_rule, axis=1)
    if prof["name"].duplicated().any():     # keep names unique if the rule ties
        dup = prof["name"].duplicated(keep=False)
        prof.loc[dup, "name"] = prof.loc[dup, "name"] + " (" + prof.index[dup].astype(str) + ")"
    prof["color"] = [CLUSTER_COLORS[(i - 1) % len(CLUSTER_COLORS)] for i in prof.index]
    return prof


def outcomes_by_year(clustered: pd.DataFrame) -> pd.DataFrame:
    """Median and n of each outcome by cluster and year (within-year comparison)."""
    long = clustered.melt(id_vars=["cluster", "divipola", "year"], value_vars=list(OUTCOMES),
                          var_name="outcome").dropna(subset=["value"])
    keep = [y in OUTCOME_YEARS[o] for o, y in zip(long["outcome"], long["year"])]
    long = long[keep]
    # Municipal outcomes repeat on both zone rows: count each municipality once per
    # cluster and year.
    municipal = long["outcome"].map(OUTCOME_LEVEL).eq("municipality")
    long = pd.concat([long[~municipal],
                      long[municipal].drop_duplicates(["outcome", "cluster", "divipola", "year"])])
    out = (long.groupby(["outcome", "cluster", "year"])["value"]
           .agg(median="median", n="count").reset_index())
    out["level"] = out["outcome"].map(OUTCOME_LEVEL)
    return out


def irca_vs_infant(clustered: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Within each cluster: Spearman rho of IRCA vs infant mortality, and band medians.

    Pools the observed-rate regime years INFANT_YEARS. Infant mortality is
    municipal; IRCA is zone-level (an ecological mismatch). Rows with a blank
    rate are left out, and a blank may mean no infant deaths were recorded.
    Unit: one municipality-year, within a cluster or pooled over all clusters. A
    municipality's rate is counted once, with the mean IRCA of its zones in that set.
    """
    rows = clustered[clustered["year"].isin(INFANT_YEARS)].dropna(subset=["infant_mortality"])
    agg = {"irca": ("irca", "mean"), "infant_mortality": ("infant_mortality", "first")}
    d = rows.groupby(["cluster", "divipola", "year"], as_index=False).agg(**agg)
    d["irca_band"] = irca_band(d["irca"])
    pooled = rows.groupby(["divipola", "year"]).agg(**agg)
    per_cluster = [{"cluster": c,
                    "spearman_rho": g["irca"].corr(g["infant_mortality"], method="spearman"),
                    "n": len(g), "municipalities": g["divipola"].nunique()}
                   for c, g in d.groupby("cluster")]
    rho = pd.DataFrame(per_cluster)
    rho["all_clusters_rho"] = pooled["irca"].corr(pooled["infant_mortality"], method="spearman")
    rho["all_clusters_n"] = len(pooled)
    bins = (d.groupby(["cluster", "irca_band"], observed=True)["infant_mortality"]
              .agg(median="median", n="count").reset_index())
    return rho, bins


def pca(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = PCA(n_components=2, random_state=SEED).fit(X)
    return p.transform(X), p.explained_variance_ratio_


# --- 5. run everything ---------------------------------------------------------
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
    prof = profiles(clustered)
    clustered["cluster_name"] = clustered["cluster"].map(prof["name"])
    rho, bins = irca_vs_infant(clustered)

    summary = {
        **counts, "k": k, "k_reason": reason,
        "silhouette_at_k": float(ktab.loc[ktab["k"] == k, "silhouette"].iloc[0]),
        "ari_min": float(stab["ari"].min()), "ari_mean": float(stab["ari"].mean()),
        "pca_variance_pc1": float(var[0]), "pca_variance_pc2": float(var[1]),
        "first_year": FIRST_YEAR, "last_year": LAST_YEAR, "seed": SEED, "n_init": N_INIT,
    }
    return {"prepared": prepared, "clusters": clustered, "k_table": ktab, "k": k,
            "stability": stab, "profiles": prof, "centers": centers,
            "outcomes_by_year": outcomes_by_year(clustered), "irca_infant": rho,
            "irca_infant_bins": bins, "summary": summary}


def output_columns() -> list[str]:
    flags = ([f"{c}_imputed" for c in FEATURES]
             + ["water_coverage_from_total", "sewer_coverage_from_total"])
    return (KEYS + ["cluster", "cluster_name", "pc1", "pc2", "irca_band"]
            + RAW_FEATURES + ["log_sgp_water_pc"] + [f"z_{c}" for c in FEATURES]
            + flags + list(OUTCOMES) + ["saber11_n"])


def write_outputs(res: dict, out: Path | str = OUTPUTS) -> list[Path]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "clusters.parquet": lambda p: res["clusters"][output_columns()].to_parquet(p, index=False),
        "cluster_profiles.csv": lambda p: res["profiles"].reset_index().to_csv(p, index=False),
        "k_selection.csv": lambda p: res["k_table"].to_csv(p, index=False),
        "stability.csv": lambda p: res["stability"].to_csv(p, index=False),
        "outcomes_by_year.csv": lambda p: res["outcomes_by_year"].to_csv(p, index=False),
        "irca_infant.csv": lambda p: res["irca_infant"].to_csv(p, index=False),
        "irca_infant_bins.csv": lambda p: res["irca_infant_bins"].to_csv(p, index=False),
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
    print(f"rows {FIRST_YEAR}-{LAST_YEAR}: {s['rows_2016_2023']:,}; municipalities only: "
          f"{s['municipality_rows']:,}")
    print(f"dropped: {s['dropped_no_irca']:,} without IRCA, "
          f"{s['dropped_too_many_missing']:,} with > {MAX_MISSING} features missing")
    print(f"kept {s['kept']:,} rows ({s['kept_urban']:,} urban, {s['kept_rural']:,} rural) "
          f"from {s['municipalities']:,} municipalities; "
          f"{s['rows_with_any_imputed']:,} rows have an imputed feature")
    print(res["k_table"].round(3).to_string(index=False))
    print(s["k_reason"])
    print(f"stability: ARI >= {floor_to(s['ari_min'])} (min {s['ari_min']:.5f}) "
          f"across seeds {list(STABILITY_SEEDS)}")
    cols = ["name", "rows", "municipalities", "urban_row_share", "irca_median"]
    print(res["profiles"][cols].round(2).to_string())
    print("IRCA vs infant mortality within clusters (municipality-years):")
    print(res["irca_infant"][["cluster", "spearman_rho", "n"]].round(3).to_string(index=False))
    for p in write_outputs(res, args.out):
        print("wrote", p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p)


if __name__ == "__main__":
    main()

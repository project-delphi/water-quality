"""Build the compact Boyacá table behind the Tunja 3D visuals page.

Reads ``data/`` (never writes to it) and writes ``visuals/boyaca.json``.
IRCA is the utility-supplied ("prestadores") IRCA, INS open data nxt2-39c3.
Municipality-level columns are repeated in both zone rows, so they are taken
once per municipality-year (from the urban row). Nothing is imputed: gaps are null.

    uv run python scripts/visuals_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DPTO = "15"          # Boyacá
TUNJA = "15001"
OUT = ROOT / "visuals" / "boyaca.json"


def clean(v):
    return None if pd.isna(v) else (int(v) if float(v).is_integer() else round(float(v), 2))


def main() -> None:
    df = pd.read_csv(ROOT / "data" / "water_municipal.csv",
                     dtype={"divipola": str, "dpto_code": str})
    df = df[df.dpto_code == DPTO]
    years = sorted(df.year.unique().tolist())
    geo = json.loads((ROOT / "data" / "municipios.geojson").read_text())
    shapes = {f["properties"]["divipola"]: f["geometry"] for f in geo["features"]}

    munis = []
    for code, g in df.groupby("divipola"):
        if code not in shapes:
            continue
        geom = shapes[code]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        polys = [[[[round(x, 4), round(y, 4)] for x, y in ring] for ring in p] for p in polys]
        urban = g[g.zone == "urban"].set_index("year").reindex(years)
        rural = g[g.zone == "rural"].set_index("year").reindex(years)
        first = g.iloc[0]
        munis.append({
            "id": code,
            "name": str(first.municipio).title(),
            "capital": int(first.department_capital),
            "alt": clean(first.altitude_m),
            "ipm_urban": clean(urban.ipm.iloc[0]),
            "ipm_rural": clean(rural.ipm.iloc[0]),
            "rain": [clean(v) for v in urban.rainfall_mm],
            "irca": {"urban": [clean(v) for v in urban.irca],
                     "rural": [clean(v) for v in rural.irca]},
            "pop": {"urban": [clean(v) for v in urban.population],
                    "rural": [clean(v) for v in rural.population]},
            "wc_total": [clean(v) for v in urban.water_coverage_total],
            "sc_total": [clean(v) for v in urban.sewer_coverage_total],
            "wc": {"urban": [clean(v) for v in urban.water_coverage],
                   "rural": [clean(v) for v in rural.water_coverage]},
            "imr": [clean(v) for v in urban.infant_mortality],
            "poly": polys,
        })
    munis.sort(key=lambda m: m["id"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"years": years, "tunja": TUNJA, "munis": munis},
                              separators=(",", ":"), ensure_ascii=False))
    print(f"{len(munis)} municipalities, {OUT.stat().st_size/1e3:.0f} kB -> {OUT}")


if __name__ == "__main__":
    main()

# AGENTS.md

## Scope

Describe Colombian municipal drinking-water quality and infant mortality from the files in
`data/` only (`water_municipal.csv`, `municipios.geojson`, documented in `data/README.md`).
One row is a municipality × zone (urban/rural) × year, 2010–2023. No other data sources,
and no invented or estimated values.

## Rules

1. **Keep `data/` unchanged.** Read it; never edit, overwrite or "clean" the files in place.
   Write derived tables to `outputs/`.
2. **Label IRCA as utility-supplied (prestadores).** `irca` is the INS open-data IRCA from
   datos.gov.co `nxt2-39c3`, which matches the *Prestadores* column of INCA, not INS's
   national total. Call it "IRCA (utility-supplied, prestadores)" in every table, figure
   and text.
3. **Never cluster on outcomes.** Infant mortality, Saber 11 and school dropout
   (`infant_mortality`, `saber11_mean`, `dropout_rate`) only describe clusters; they are
   never features.
4. **Comparisons are descriptive, not causal.** Say so wherever clusters, regions or
   IRCA bands are compared: they show association only and do not establish causal
   effects of water quality.

## Data caveats (from `data/README.md`)

- Read `divipola` as text (keep the leading zero).
- Municipality-level columns repeat on both zone rows: count each municipality-year once.
- Department capitals (codes ending `001`) have no urban/rural coverage split: use
  `water_coverage_total` / `sewer_coverage_total` and flag any fill.
- Rural IRCA is missing far more often than urban IRCA; missingness is not random.
- `idf` (to 2020) and `idf_new` (from 2020) are different methods: never join them.
- `sgp_water_pc` is nominal pesos; `ipm` is the 2018 census repeated every year;
  `altitude_m` is a derived SRTM point, not an official altitude.
- Infant mortality changes method in 2017 and 2020 looks like another source; a blank may
  mean no recorded deaths.
- Saber 11 covers 2014–2017, 2019, 2020 and 2022 only.
- `municipios.geojson` follows RFC 7946 winding: reverse the rings for Plotly.

## Commands

The Python environment is `pyproject.toml` + `uv.lock` (`.venv/`). Always run Quarto and
Python through `uv run`: `uv run python scripts/analysis.py`, `uv run quarto render`,
`uv run quarto preview`. Add packages with `uv add`, never `pip install`.

# Project instructions

## Scope

Describe Colombian municipal water safety and infant mortality (2010-2023) from the files in
`data/` only. The unit of analysis is one row of `data/water_municipal.csv`: municipality x
zone (urban/rural) x year. Read `data/README.md` before using any column.

## Rules

- Keep `data/` unchanged. Read it; never edit, overwrite or regenerate it. Write derived
  tables elsewhere.
- Label IRCA everywhere as "IRCA (utility-supplied, INS open data)": it comes from
  utility-supplied ("prestadores") reports, not INS's national total.
- Never cluster on outcomes (infant mortality, Saber 11, dropout). Cluster on profile
  features only; use outcomes just to describe clusters afterwards.
- Comparisons are descriptive, not causal. State that they do not establish effects of water
  quality, and name possible confounders.
- Read `divipola` as text to keep the leading zero (`05001`).

## Data caveats (from `data/README.md`)

- Rural IRCA is missing far more often than urban IRCA; the 2020 drop in rural IRCA may
  reflect which systems were sampled.
- Department capitals (`department_capital == 1`) have no urban/rural coverage split: use
  `water_coverage_total` / `sewer_coverage_total` and flag any fill.
- `idf` (to 2020) and `idf_new` (from 2020) are different methods; never join them.
- Saber 11 covers 2014-2017, 2019, 2020 and 2022 only.
- Infant mortality changes method in 2017 and is volatile for small municipalities.
- `altitude_m` is derived from SRTM; `ipm` is census 2018 only; `sgp_water_pc` is nominal.
- Municipality-level columns repeat in both zone rows: count each municipality-year once.
- Do not invent data, sources or numbers; report missing sources as TODOs.

## Environment

Run `quarto` and `python` through `uv run` (for example `uv run quarto render explore.qmd`,
`uv run python script.py`) so the project's `.venv/` is used.

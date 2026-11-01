# Colombian municipal water quality and context, 2010–2023

This folder holds the real, public data used in Part 2 of the workshop. Each row of
`water_municipal.csv` describes one **municipality × zone (urban or rural) × year**.
Every value comes from a public source named below. Nothing is invented or estimated,
and gaps are left empty. We do not impute missing values here: the workshop teaches
that step later.

| file | what it is |
|---|---|
| `water_municipal.csv` | the analysis table (UTF-8, comma-separated, empty cell = missing) |
| `municipios.geojson` | simplified DANE municipal boundaries (WGS84) for maps, joined on `divipola` |
| `README.md` | this guide; the blocks marked "generated" are rewritten by the build script |
| `raw/` | cached downloads and `raw/manifest.json`. Git ignores this folder. |

<!-- BEGIN GENERATED: summary -->
Rows: **31,416** (1,122 DIVIPOLA codes × 2 zones × 14 years); columns: **28**; file size 5.1 MB. GeoJSON: 1,121 polygons, 2.70 MB, simplification tolerance 0.0039°; CSV codes without a polygon: 27493. Built 2026-10-30.
<!-- END GENERATED: summary -->

## Unit of analysis

- **Universe.** All 1,122 entries in DANE's DIVIPOLA list of municipalities
  (datos.gov.co `gdxc-w37w`, cut-off 30 December 2024). That is 1,103 municipalities,
  the island of San Andrés (`entity_type = island`) and 18 *áreas no municipalizadas*
  (non-municipalised areas in Amazonas, Guainía and Vaupés; `entity_type =
  non_municipalised_area`). Non-municipalised areas **are included**, but most sources
  publish little or nothing for them, so their rows are mostly empty. Drop them with
  `entity_type != "non_municipalised_area"` if you only want municipalities.
- **Zone.** `urban` is the *cabecera municipal* (the head town). `rural` covers
  *centros poblados y rural disperso* (smaller settlements and the dispersed countryside).
  These are the DANE and INS area definitions.
- **Year.** Calendar years 2010–2023. Every municipality has 2 zones × 14 years = 28
  rows, even when a source has no data for some of them.
- **Municipality-level variables are repeated in both zone rows.** Only the columns
  marked "zone-specific" below differ between the urban and rural rows. If you sum or
  average a municipality-level column over all rows, count each municipality-year only
  once.
- **Static variables** (`region`, `entity_type`, `rurality_category`, `altitude_m`,
  `ipm`) have one value per municipality (or municipality × zone for `ipm`), repeated
  in every year.

## Column dictionary

"Zone-specific" means the urban and rural rows hold different values. The coverage
table below lists the years each column actually has data.

| column | description | unit | zone-specific | source (licence) |
|---|---|---|---|---|
| `divipola` | DANE municipality code; **read it as text** so you keep the leading zero (`05001`) | 5-character code | – | DANE DIVIPOLA `gdxc-w37w` (CC BY-SA 4.0) |
| `municipio` | municipality name as written in DIVIPOLA (upper case) | text | – | DIVIPOLA |
| `dpto_code` | department code (first two digits of `divipola`) | 2-character code | – | DIVIPOLA |
| `departamento` | department name as written in DIVIPOLA | text | – | DIVIPOLA |
| `region` | DANE region of the department: Caribe, Centro Oriente, Centro Sur, Eje Cafetero, Llanos, Pacífico or Bogotá | category | – (static) | DNP TerriData Dim1, indicator "Región" (source given as DANE), department rows |
| `entity_type` | `municipality`, `island` (San Andrés) or `non_municipalised_area` | category | – (static) | DIVIPOLA `tipo_municipio` |
| `zone` | `urban` (cabecera) or `rural` (centros poblados y rural disperso) | category | key | – |
| `year` | calendar year | year | key | – |
| `irca` | *Índice de Riesgo de la Calidad del Agua para consumo humano*: INS risk score for drinking water quality, from the surveillance samples of the year. 0 means no risk and 100 means unfit. The bands in Resolución 2115 de 2007, art. 15, are 0–5 no risk, 5.1–14 low, 14.1–35 medium, 35.1–80 high and 80.1–100 *inviable sanitariamente* (unfit). **This is utility-supplied ("prestadores") IRCA; see the caveats.** | % (0–100) | ✅ | INS, datos.gov.co `nxt2-39c3`, columns `ircaurbano` / `ircarural` (CC BY-SA 4.0) |
| `irca_missing` | 1 when `irca` is empty (INS reported "ND" or had no row for that municipality and year), else 0 | 0/1 | ✅ | derived from `irca` |
| `water_coverage` | aqueduct (piped water) coverage in the zone, from the *Reporte de Estratificación y Coberturas* (REC) that municipalities file with Superservicios | % (0–100) | ✅ | DNP TerriData Dim3, "Cobertura de acueducto urbana/rural (REC)" (source given as Superservicios) |
| `sewer_coverage` | sewerage coverage in the zone, also from the REC | % (0–100) | ✅ | DNP TerriData Dim3, "Cobertura de alcantarillado urbana/rural (REC)" |
| `water_coverage_total` | aqueduct coverage for the whole municipality (REC). It is the only REC coverage value for **department capitals**, because TerriData publishes no urban/rural split for them. | % (0–100) | – | DNP TerriData Dim3, "Cobertura de acueducto (REC)" |
| `sewer_coverage_total` | sewerage coverage for the whole municipality (REC); the same note applies to capitals | % (0–100) | – | DNP TerriData Dim3, "Cobertura de alcantarillado (REC)" |
| `population` | DANE population projection for the zone | people | ✅ | DANE municipal projections by area, 2005–2017 and 2018–2042 series |
| `rural_share` | rural population ÷ total municipal population, same year | fraction (0–1) | – | derived from DANE projections |
| `rurality_category` | DNP rurality category from the *Misión para la Transformación del Campo*: Ciudades y aglomeraciones, Intermedio, Rural or Rural disperso | category | – (static) | DNP TerriData Dim1, "Categoría de ruralidad" |
| `altitude_m` | **derived:** SRTM elevation at the DIVIPOLA head-town coordinates. This is not an official DANE altitude. | metres | – (static) | OpenTopoData public API, dataset `srtm90m` (SRTM GL3 v3, NASA/USGS) |
| `ipm` | *Índice de Pobreza Multidimensional*: share of people who are multidimensionally poor in the zone, from the **2018 census** only. The 2018 value is repeated in every year. | % (0–100) | ✅ (static) | DNP TerriData Dim14, "IPM - Cabecera (Censo)" / "IPM - Centros poblados y rural disperso (Censo)" (source given as DANE CNPV 2018) |
| `mdm` | *Medición de Desempeño Municipal*: DNP municipal performance score (management plus results) | points (0–100) | – | DNP TerriData Dim8, "Resumen MDM / MDM" |
| `idf` | *Índice de Desempeño Fiscal*, **old method** | points (0–100) | – | DNP TerriData Dim7, "Indicador de desempeño fiscal" (DNP-DDDR) |
| `idf_new` | *Índice de Desempeño Fiscal*, **new method** from 2020. It is not comparable with `idf`. | points (0–100) | – | DNP TerriData Dim7, "Puntaje nuevo Índice de Desempeño Fiscal" |
| `sgp_water_pc` | *Sistema General de Participaciones* allocation for drinking water and basic sanitation, divided by the DANE total municipal population of the same year | **nominal** Colombian pesos per person | – | DNP TerriData Dim7, "SGP - Distribución asignaciones SGP por sectores / Agua potable" (pesos corrientes, DNP-SICODIS) ÷ DANE population |
| `rainfall_mm` | annual precipitation, averaged over the municipal polygon and weighted by the fraction of each 0.05° cell inside it | mm per year | – | CHIRPS v3.0 annual LatAm GeoTIFFs (CC BY 4.0) over DANE MGN 2023 polygons |
| `infant_mortality` | deaths under 1 year per 1,000 live births. **The series changes method in 2017; see the caveats.** | per 1,000 live births | – | DNP TerriData Dim5, "Tasa de mortalidad infantil en menores de 1 año (x cada 1.000 nacidos vivos)" (source given as MinSalud) |
| `saber11_mean` | mean Saber 11 global score (0–500) of students whose **school** is in that municipality and zone. Both sittings of a year are pooled, weighted by number of students. | points (0–500) | ✅ | ICFES, datos.gov.co `kgxf-xxbe` and `rnvb-vnyh` (CC BY-SA 4.0) |
| `saber11_n` | number of distinct students with a global score behind `saber11_mean`. It is 0 when a published year has no tested students in that zone, and empty in years with no published data. | students | ✅ | ICFES (as above) |
| `dropout_rate` | intra-annual school dropout rate, official (public) sector, all levels | % (0–100) | – | MEN, datos.gov.co `nudc-7mev`, column `deserci_n` (CC BY-SA 4.0) |

## Coverage: share of non-missing values, computed from the final CSV

<!-- BEGIN GENERATED: coverage -->
| column | all rows, 2010–2023 (%) | years with data | rows in years with data (%) |
|---|---|---|---|
| `divipola` | 100.0 | 2010–2023 | 100.0 |
| `municipio` | 100.0 | 2010–2023 | 100.0 |
| `dpto_code` | 100.0 | 2010–2023 | 100.0 |
| `departamento` | 100.0 | 2010–2023 | 100.0 |
| `region` | 100.0 | 2010–2023 | 100.0 |
| `entity_type` | 100.0 | 2010–2023 | 100.0 |
| `zone` | 100.0 | 2010–2023 | 100.0 |
| `year` | 100.0 | 2010–2023 | 100.0 |
| `irca` | 66.3 | 2010–2023 | 66.3 (urban 85.5 / rural 47.1) |
| `irca_missing` | 100.0 | 2010–2023 | 100.0 (urban 100.0 / rural 100.0) |
| `water_coverage` | 89.9 | 2010–2023 | 89.9 (urban 90.3 / rural 89.5) |
| `sewer_coverage` | 89.9 | 2010–2023 | 89.9 (urban 90.3 / rural 89.5) |
| `water_coverage_total` | 93.4 | 2010–2023 | 93.4 |
| `sewer_coverage_total` | 93.3 | 2010–2023 | 93.3 |
| `population` | 99.9 | 2010–2023 | 99.9 (urban 99.9 / rural 99.9) |
| `rural_share` | 99.9 | 2010–2023 | 99.9 |
| `rurality_category` | 98.1 | 2010–2023 | 98.1 |
| `altitude_m` | 100.0 | 2010–2023 | 100.0 |
| `ipm` | 98.1 | 2010–2023 | 98.1 (urban 98.1 / rural 98.1) |
| `mdm` | 56.1 | 2016–2023 | 98.2 |
| `idf` | 77.0 | 2010–2020 | 98.0 |
| `idf_new` | 28.0 | 2020–2023 | 98.0 |
| `sgp_water_pc` | 98.2 | 2010–2023 | 98.2 |
| `rainfall_mm` | 99.9 | 2010–2023 | 99.9 |
| `infant_mortality` | 85.1 | 2010–2023 | 85.1 |
| `saber11_mean` | 44.4 | 2014–2022 (none in 2018, 2021) | 88.9 (urban 95.6 / rural 82.2) |
| `saber11_n` | 50.0 | 2014–2022 (none in 2018, 2021) | 100.0 (urban 100.0 / rural 100.0) |
| `dropout_rate` | 91.9 | 2011–2023 | 98.9 |
<!-- END GENERATED: coverage -->

Missing values are not random. Small, remote and non-municipalised areas are missing
more often, and so are rural zones. Bear this in mind when you choose a year or impute.

## Join coverage per source

How many DIVIPOLA codes each source matched. Codes that a source has but DIVIPOLA does
not are dropped.

<!-- BEGIN GENERATED: join -->
| source | codes in source | matched DIVIPOLA | DIVIPOLA codes without data | source codes not in DIVIPOLA (dropped) |
|---|---|---|---|---|
| TerriData idf | 1101 | 1101 | 21 | none |
| TerriData idf_new | 1102 | 1102 | 20 | none |
| TerriData infant_mortality | 1102 | 1102 | 20 | none |
| TerriData ipm_rural | 1101 | 1101 | 21 | none |
| TerriData ipm_urban | 1101 | 1101 | 21 | none |
| TerriData mdm | 1102 | 1102 | 20 | none |
| TerriData region | 1102 | 1102 | 20 | none |
| TerriData rurality_category | 1101 | 1101 | 21 | none |
| TerriData sewer_coverage_total | 1101 | 1101 | 21 | none |
| TerriData sewer_rural | 1070 | 1070 | 52 | none |
| TerriData sewer_urban | 1070 | 1070 | 52 | none |
| TerriData sgp_water | 1102 | 1102 | 20 | none |
| TerriData water_coverage_total | 1101 | 1101 | 21 | none |
| TerriData water_rural | 1070 | 1070 | 52 | none |
| TerriData water_urban | 1070 | 1070 | 52 | none |
| INS IRCA (nxt2-39c3) | 1093 | 1093 | 29 | none |
| DANE population projections by area | 1123 | 1122 | 0 | 94663 |
| ICFES Saber 11 (school municipality) | 1114 | 1112 | 10 | 27086, 94663 |
| MEN dropout (nudc-7mev) | 1123 | 1122 | 0 | 94663 |
| DANE MGN 2023 polygons | 1121 | 1121 | 1 | none |
<!-- END GENERATED: join -->

## Sources

SODA queries below are shown with their parameters; the exact request URLs, the
retrieval date and the SHA-256 of every cached file are in the
[raw files table](#raw-files-and-checksums). Licences were checked on 2026-10-30.

### DANE DIVIPOLA (universe and identifiers)

- `https://www.datos.gov.co/resource/gdxc-w37w.json?$limit=5000&$order=cod_mpio`
  ("DIVIPOLA- Códigos municipios", updated to 30 December 2024).
- Fields used: `cod_mpio`, `nom_mpio`, `cod_dpto`, `dpto`, `tipo_municipio`, and
  `latitud` / `longitud` (head town, written with decimal commas).
- Licence: CC BY-SA 4.0 on datos.gov.co. Attribution: Departamento Administrativo
  Nacional de Estadística (DANE).

### INS IRCA (water quality)

- `https://www.datos.gov.co/resource/nxt2-39c3.csv?$limit=50000&$order=departamentocodigo,municipiocodigo,a_o`
  ("Calidad del Agua para Consumo Humano en Colombia", 19,160 rows, 2007–2024).
- Fields used: `municipiocodigo`, `a_o`, `ircaurbano`, `ircarural`. All values are text.
  `ND` (no data) becomes empty. The 569 department aggregate rows
  (`municipiocodigo = "#TODOS"`) are dropped.
- Licence: CC BY-SA 4.0. Attribution: Instituto Nacional de Salud (INS), Bogotá D.C.

### DNP TerriData (coverage, rurality, region, IPM, MDM, IDF, SGP, infant mortality)

- Bulk files, pipe-delimited UTF-8 text inside zip archives:
  `https://terridata.dnp.gov.co/assets/docs/txt/dimensiones/TerriData_Dim{1,3,5,7,8,14}.txt.zip`.
  These are Dim1 (general description), Dim3 (housing and public services), Dim5
  (health), Dim7 (public finance), Dim8 (municipal performance) and Dim14 (poverty).
- TerriData writes numbers with `.` for thousands and `,` for decimals. The script checks
  every value against that pattern before converting it.
- Indicators are selected by exact `Subcategoría` + `Indicador`. For SGP the unit is
  also checked: "Agua potable" appears twice in Dim7, once in pesos and once as a
  percentage.
- Licence: DNP's site policy (<https://dnp.gov.co/Politica-de-seguridad>) says DNP
  open data may be reused under Creative Commons Attribution 4.0, citing the source. Cite
  as "DNP, TerriData" plus the original source TerriData names for each indicator
  (Superservicios, DANE, MinSalud, DNP-SICODIS).

### DANE population projections by area

- 2005–2017: `https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/DCD-area-proypoblacion-Mun-2005-2017_VP.xlsx`
  (sheet `NuevaMpal`).
- 2018–2042: `https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/PPED-AreaMun-2018-2042_VP.xlsx`
  (sheet `PobMunicipalxÁrea`, "Actualizado el 30 de Julio de 2025").
- `Cabecera Municipal` becomes urban, `Centros Poblados y Rural Disperso` becomes rural,
  and `Total` is the denominator for `rural_share` and `sgp_water_pc`.
- Terms: DANE authorises use, transformation and analysis of its information provided it
  is cited as "Fuente: Departamento Administrativo Nacional de Estadística:
  www.dane.gov.co" (<https://www.dane.gov.co/index.php/terminos-y-condiciones>).

### DANE MGN 2023 (municipal polygons)

- `https://geoportal.dane.gov.co/descargas/mgn_2023/MGN2023_MPIO_POLITICO.zip`
  (shapefile `MGN_ADM_MPIO_GRAFICO`, EPSG:4686 MAGNA-SIRGAS, 1,121 polygons).
- Used for the CHIRPS zonal means (full resolution) and for `municipios.geojson`. For the
  GeoJSON, shapes are reprojected to WGS84 and simplified with GEOS coverage
  simplification, which keeps shared borders shared so there are no gaps or overlaps.
  They are then snapped to a 0.0001° grid (about 11 m) and written with 4 decimals.
  Properties: `divipola`, `municipio`, `departamento`, with names taken from DIVIPOLA.
- Terms: DANE (as above).

### CHIRPS v3.0 (rainfall)

- `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/annual/latam/tifs/chirps-v3.0.{2010…2023}.tif`
  (0.05° grid, mm per year, EPSG:4326) and the product README
  `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/README-CHIRPSv3.0.txt`.
- The GeoTIFFs mark sea and no-data cells as −9999 without declaring a nodata value.
  The script declares −9999 as nodata before computing the zonal means with
  `exactextract`, which weights each cell by the fraction inside the polygon.
- Licence: the CHC page (<https://www.chc.ucsb.edu/data/chirps3>) says CHIRPS3 "is
  licensed under a Creative Commons Attribution 4.0 International License" and that the
  CHC "has waived all copyright and related or neighboring rights".
- Cite: Funk, C. et al. (2026), "The Climate Hazards Center Infrared Precipitation with
  Stations, Version 3", *Scientific Data* 13, 718, <https://doi.org/10.1038/s41597-026-07096-4>.
  Also cite the data repository, <https://doi.org/10.15780/G2JQ0P>, with your access date.
  This citation is the one the CHC page recommends; its DOI resolves to the *Scientific
  Data* article (checked 2026-10-30). The original CHIRPS paper is Funk, C. et al. (2015), *Scientific Data* 2,
  150066, <https://doi.org/10.1038/sdata.2015.66>.

### OpenTopoData / SRTM (altitude, derived)

- `https://api.opentopodata.org/v1/srtm90m?locations=lat,lon|…&interpolation=bilinear`,
  sending 100 points per request, at most one request per second (within the public API
  limits: 100 locations per request, 1 call per second, 1,000 calls per day).
- The public API's `srtm90m` dataset is SRTM GL3 version 3 (NASA/USGS), per
  <https://www.opentopodata.org/datasets/srtm/>. SRTM is a NASA product with no
  restrictions on use. Cite NASA JPL (2013), *NASA Shuttle Radar Topography Mission
  Global 3 arc second*, NASA LP DAAC, <https://doi.org/10.5067/MEaSUREs/SRTM/SRTMGL3.003>,
  and OpenTopoData as the access service.
- The value is the terrain height at one point, the head-town coordinate DIVIPOLA
  publishes, read from a roughly 90 m grid with bilinear interpolation. It is not the
  official altitude of the town.

### ICFES Saber 11 (school results)

- `https://www.datos.gov.co/resource/kgxf-xxbe.csv` ("Resultados únicos Saber 11") and
  `https://www.datos.gov.co/resource/rnvb-vnyh.csv` ("Saber 11° 2020-2"). There is one
  server-side SoQL query per sitting:

  ```sql
  SELECT estu_consecutivo, cole_cod_mcpio_ubicacion AS m, cole_area_ubicacion AS a,
         max(punt_global::number) AS g
  WHERE periodo = '<periodo>' AND punt_global IS NOT NULL
  GROUP BY estu_consecutivo, m, a
  |> SELECT m, a, avg(g) AS mean_global, count(*) AS n GROUP BY m, a
  ORDER BY m, a LIMIT 100000
  ```

  The first stage keeps **one row per student**. `kgxf-xxbe` contains exact duplicate
  student records: periodo 20194 has 1,096,524 rows for 546,211 distinct
  `estu_consecutivo`, and 20224 has 1,065,888 rows for 532,792. A plain `avg()` would
  count those students twice. A control query checks that the students aggregated equal
  `count(distinct estu_consecutivo)` for every sitting.
- Sitting → year mapping (calendar B, "…1", sits in the first half of the year;
  calendar A, "…2" or "…4", in the second half):

  | year | sittings used |
  |---|---|
  | 2014 | 20142 (20141 has no `punt_global`) |
  | 2015 | 20151 + 20152 |
  | 2016 | 20161 + 20162 |
  | 2017 | 20171 + 20172 |
  | 2018 | **none**: calendar A 2018-2 is not published on datos.gov.co, and 20181 (calendar B only) is not comparable |
  | 2019 | 20191 + 20194 |
  | 2020 | 20201 (`kgxf-xxbe`) + 20204 (`rnvb-vnyh`); `a8xr-en99` (2020-1) duplicates 20201 and is not used |
  | 2021 | **none**: calendar A 2021-2 is not published; 20211 (calendar B only) is not comparable |
  | 2022 | 20221 + 20224 |

- Location is the **school's** municipality and area (`cole_cod_mcpio_ubicacion`,
  `cole_area_ubicacion` URBANO/RURAL), not the student's home.
- Licence: CC BY-SA 4.0. Attribution: Instituto Colombiano para la Evaluación de la
  Educación (ICFES).

<!-- BEGIN GENERATED: saber11 -->
| dataset | periodo | year | rows_with_score | distinct_students | students_aggregated | no_area |
|---|---|---|---|---|---|---|
| kgxf-xxbe | 20142 | 2014 | 546727 | 544535 | 544535 | 5 |
| kgxf-xxbe | 20151 | 2015 | 25973 | 25947 | 25947 | 0 |
| kgxf-xxbe | 20152 | 2015 | 544491 | 542450 | 542450 | 0 |
| kgxf-xxbe | 20161 | 2016 | 13095 | 13064 | 13064 | 0 |
| kgxf-xxbe | 20162 | 2016 | 550275 | 548206 | 548206 | 0 |
| kgxf-xxbe | 20171 | 2017 | 13018 | 13018 | 13018 | 0 |
| kgxf-xxbe | 20172 | 2017 | 548269 | 546261 | 546261 | 0 |
| kgxf-xxbe | 20191 | 2019 | 12561 | 12540 | 12540 | 0 |
| kgxf-xxbe | 20194 | 2019 | 1096524 | 546211 | 546211 | 0 |
| kgxf-xxbe | 20201 | 2020 | 15435 | 15435 | 15435 | 0 |
| rnvb-vnyh | 20204 | 2020 | 504872 | 504872 | 504872 | 0 |
| kgxf-xxbe | 20221 | 2022 | 20049 | 20049 | 20049 | 0 |
| kgxf-xxbe | 20224 | 2022 | 1065888 | 532792 | 532792 | 1 |
<!-- END GENERATED: saber11 -->

### MEN school dropout

- `https://www.datos.gov.co/resource/nudc-7mev.csv?$select=a_o, c_digo_municipio, deserci_n&$limit=100000&$order=a_o, c_digo_municipio`
  ("MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR, BÁSICA Y MEDIA_POR_MUNICIPIO",
  2011–2024, published "sin atípicos", i.e. with outliers removed).
- `deserci_n` is the intra-annual dropout rate of the official (public) sector, in
  percent.
- Licence: CC BY-SA 4.0. Attribution: Ministerio de Educación Nacional (MEN).

## Known gaps and caveats (read before teaching)

1. **IRCA is utility-supplied ("prestadores") IRCA, not INS's national total.** An
   earlier check found that the department totals in `nxt2-39c3` match the
   *Prestadores* column of INS's INCA 2023 report, not its overall figure. The overall
   figure also covers samples where no utility was identified. A repeat check on
   2026-10-30 compared the 2023 department rows (`municipiocodigo = "#TODOS"`) with INCA
   2023 Tabla 4: they match *Prestadores* in 30 of 30 departments and the total in only 5.
   Call the variable "IRCA (utility-supplied, INS open data)" in slides and
   reports. Rural IRCA is missing far more often than urban IRCA, because many rural
   systems are not sampled. The mean rural IRCA across reporting municipalities falls
   from about 37–40 in 2016–2019 to about 22–27 in 2020–2023 (computed from this CSV).
   Check whether that reflects a change in which systems were sampled before calling
   it an improvement.
2. **Coverage values come from REC self-reports.** No source value is above 100 or
   below 0 (see build notes), so nothing was clipped. Exact 0s and 100s are common, and
   some 0s probably mean "not reported" rather than "no service". Tunja's municipal total,
   for example, is 0.00 in 2021 and about 60–93 in neighbouring years. The values are
   left as published.
   **Department capitals have no urban/rural REC split** in TerriData: the 31
   municipalities whose code ends in `001`, including Bogotá, Medellín and Cali. Their
   `water_coverage` / `sewer_coverage` are empty, and only `water_coverage_total` /
   `sewer_coverage_total` are available. The same is true of San Andrés (`88001`),
   Barrancominas (`94343`), the non-municipalised areas and Nuevo Belén de Bajirá.
   If you cluster on zone-specific coverage, decide explicitly how to treat capitals, for
   example by using the municipal total for the urban zone and saying so. Do not do it
   silently. The total REC series has two monthly cuts in 2016 and 2018 (September and
   December); the December cut is kept (see build notes).
3. **Altitude is derived**, not official. It is one SRTM point at the head-town
   coordinate.
4. **Saber 11 covers 2014–2017, 2019, 2020 and 2022.** 2018 and 2021 are empty (see the
   mapping table). Scores are 0–500 global scores, and calendar A and B sittings are
   pooled within a year. School location is not student residence.
5. **Two IDF methods.** `idf` is the old method (2010–2020) and `idf_new` the new method
   (2020–2023). Both exist for 2020, and the scales differ: in 2020 the new score is on
   average about 13 points lower. Never join them into one series.
6. **Nominal pesos.** `sgp_water_pc` is in current pesos of each year. It is not
   deflated (see TODO 3 below). Compare years with care.
7. **IPM is census-only.** The value is from the 2018 census and repeated for every
   year. It is a static profile, not a time series. The 2005 census value exists in
   TerriData but is not used.
8. **Infant mortality changes method in 2017.** In 2005–2016 almost every municipality
   has a smoothly declining value, which looks like a modelled DANE estimate. From 2017
   the values look like observed vital-statistics rates. They are more volatile, and
   29–35% of municipalities are blank each year. No zero appears anywhere in the
   series, so a blank may mean "no infant deaths recorded" rather than "unknown". Small
   municipalities produce extreme rates, some above 100 per 1,000 (see build notes).
   2020 is complete again, which suggests a different source for that year. Treat
   2010–2016, 2017–2019/2021–2023 and 2020 as separate regimes, and do not read the 2017
   drop as a real improvement.
9. **Population vintages.** 2010–2017 come from DANE's back-projection series and
   2018–2023 from the 2018–2042 series updated in July 2025. There may be a small step
   between 2017 and 2018.
10. **MGN 2023 has no polygon for Nuevo Belén de Bajirá (`27493`).** It appears in
    DIVIPOLA 2024 as a new municipality. Its rows have no rainfall and very little other
    data. Most other sources also predate it. Some sources carry codes that are not in
    DIVIPOLA 2024, and those codes are dropped (see the join table):
    - `94663` (Mapiripana, a former non-municipalised area in Guainía)
    - `27086` (Belén de Bajirá, an older code, in ICFES)
    - code `0` in MEN, which is a NACIONAL total for 2019–2021 written as a fraction
      rather than a percentage, and is dropped explicitly
11. **San Andrés (`88001`)** has no TerriData values. TerriData reports the archipelago
    only at department level (`88000`), and the department figure is not copied to the
    island.
12. **Region** is DANE's regional grouping as published in TerriData, assigned through
    each municipality's department. Antioquia, for instance, is in "Eje Cafetero", and
    Bogotá is its own region.
13. **Rates and scores are not causal evidence.** Comparing clusters or regions shows
    association only. Water quality is not shown to cause any outcome here.
14. **Polygon winding.** `municipios.geojson` follows RFC 7946: exterior rings run
    counter-clockwise. Plotly and d3 maps expect the opposite winding and draw each
    municipality inverted (the world minus the polygon). Reverse the rings in memory
    before `go.Choropleth`, as `scripts/analysis.py` does in `load_geojson()`.

### TODO: sources not included

1. **Service continuity** (*continuidad del servicio de acueducto*). SUI, Superservicios,
   <https://sui.superservicios.gov.co/>, is behind Incapsula bot protection, so it cannot
   be downloaded by a polite script.
2. **Under-5 acute diarrhoeal disease (EDA) incidence.** SIVIGILA open data
   (<https://portalsivigila.ins.gov.co/>) only has EDA *deaths* (event 590), which are
   too sparse. The workshop uses infant mortality as the health outcome instead.
   TerriData Dim5 also has "Mortalidad en menores de 5 años por enfermedad diarréica
   aguda (EDA)", which is a mortality rate, not incidence. It is not included.
3. **`sgp_water_pc_real`** (SGP deflated by CPI). DANE's CPI index series
   (<https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc>)
   has no stable machine-readable download URL, so we did not add it.
4. **Saber 11 calendar A 2018-2 and 2021-2.** Not on datos.gov.co. The microdata may be
   available from ICFES DataIcfes, <https://www.icfes.gov.co/investigaciones/data-icfes/>.

## Rebuilding

From the repository root (needs [uv](https://docs.astral.sh/uv/) and an internet
connection the first time):

```bash
uv run examples/water/scripts/build_dataset.py            # reuse cached downloads in data/raw/
uv run examples/water/scripts/build_dataset.py --refresh  # download every source again
```

uv reads the dependencies from the script's inline (PEP 723) metadata and builds a
private environment, so nothing is installed into the repository's conda environment.
A rebuild from cache took about 2 minutes on a 2026 laptop. A build from scratch
downloads about 185 MB in 67 files and took about 9 minutes, mostly for the TerriData
and MGN zips and the server-side Saber 11 queries. It needs about 1 GB of free disk for
the extracted files. Two builds on 2026-10-30, one from scratch and one from cache,
produced byte-identical `water_municipal.csv` and `municipios.geojson`.

The script:

1. downloads each source into its own folder under `raw/`, retrying with backoff
2. records the URL, date and SHA-256 in `raw/manifest.json`
3. extracts zips into empty folders
4. joins everything on `divipola`
5. checks that the key is unique and that values are in range
6. writes the CSV and GeoJSON
7. rewrites the generated blocks of this README

Online sources change over time. A `--refresh` build may differ from the committed CSV;
compare checksums in the table below.

## Build notes

<!-- BEGIN GENERATED: notes -->
- TerriData Dim3 water_coverage_total: 2181 entity-years have two monthly cuts (years [2016, 2018]); kept the latest month; 391 of them differ in value
- TerriData Dim3 sewer_coverage_total: 2181 entity-years have two monthly cuts (years [2016, 2018]); kept the latest month; 404 of them differ in value
- Region: TerriData department-level region used; municipality-level region exists for 1102 codes and differs from its department's for 0 []; codes without region: []
- DANE population: max |urban + rural - total| = 0 people
- Saber 11 2020-1: a8xr-en99 {'n': '15435', 'students': '15435', 'total': '4467419'} vs kgxf-xxbe 20201 {'n': '15435', 'students': '15435', 'total': '4467419'} -> identical totals, a8xr-en99 not used
- MEN dropout: dropped 3 national rows (code 0); municipal codes are zero-padded (2011 codes lack the leading 0)
- water_coverage: 0 zone-years > 100, 0 < 0, 7540 exactly 100, 3608 exactly 0, out of 28235 non-missing (2010-2023; values not altered)
- sewer_coverage: 0 zone-years > 100, 0 < 0, 4786 exactly 100, 7117 exactly 0, out of 28236 non-missing (2010-2023; values not altered)
- water_coverage_total: 0 municipality-years > 100, 0 < 0, 1605 exactly 100, 199 exactly 0, out of 14665 non-missing (2010-2023; values not altered)
- sewer_coverage_total: 0 municipality-years > 100, 0 < 0, 607 exactly 100, 912 exactly 0, out of 14663 non-missing (2010-2023; values not altered)
- REC coverage: 31 codes have municipal totals but no urban/rural split in any year (05001, 08001, 11001, 13001, 15001, 17001, 18001, 19001, 20001, 23001, 27001, 41001, 44001, 47001, 50001, 52001, 54001, 63001, 66001, 68001, 70001, 73001, 76001, 81001, 85001, 86001, 91001, 94001, 95001, 97001, 99001); 21 codes have neither (27493, 88001, 91263, 91405, 91407, 91430, 91460, 91530, 91536, 91669, 91798, 94343, 94883, 94884, 94885, 94886, 94887, 94888, 97511, 97777, 97889)
- idf (old method): 20 municipality-years equal 0 (kept as published; likely no fiscal report); idf_new: 0 zeros
- population: 27493 missing in [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017] (not in the DANE series for those years)
- population: DANE lists 27493 with 0 people in [2018, 2019, 2020, 2021, 2022, 2023], so rural_share and sgp_water_pc are empty there
- infant_mortality: 13 municipality-years > 100 per 1,000 live births (max 250.0); these are small-number rates and are not altered
- sgp_water_pc: max 620,932 COP/person
<!-- END GENERATED: notes -->

## Raw files and checksums

<!-- BEGIN GENERATED: manifest -->
| file | retrieved | bytes | SHA-256 |
|---|---|---|---|
| `chirps/README-CHIRPSv3.0.txt` | 2026-10-30 | 7,585 | `8957c7b9136be9ad40595515d0444c63e39c55a3ad36ad9b9eebfdac8eb1d495` |
| `chirps/chirps-v3.0.2010.tif` | 2026-10-30 | 4,171,664 | `b27884221e59260f381aeb397ed77191ff14a723e16da6a31d14bf08d6a8f099` |
| `chirps/chirps-v3.0.2011.tif` | 2026-10-30 | 4,183,210 | `23d5b7901c37be04ce6311b6c4d3e9095eca79b3082b597ee9e346b18e935990` |
| `chirps/chirps-v3.0.2012.tif` | 2026-10-30 | 4,192,762 | `d6c1dd46f703740b40d11a8bc7528f406a08df2fcfbce9727d488d1593b85413` |
| `chirps/chirps-v3.0.2013.tif` | 2026-10-30 | 4,189,130 | `273cff29f8b9ee0f197f61f8a72be78adadde54ac96b90da1d1f234adefa6486` |
| `chirps/chirps-v3.0.2014.tif` | 2026-10-30 | 4,198,396 | `7650e89f5b316414e5bcb35532c3c615a80b0531f983baf08b59331a67081f1b` |
| `chirps/chirps-v3.0.2015.tif` | 2026-10-30 | 4,195,106 | `ede004b8a6b19a6f7a6ba143ecad65650274506827ed7d2dc715cddfd1e3b581` |
| `chirps/chirps-v3.0.2016.tif` | 2026-10-30 | 4,180,026 | `34d6dd3e9e24b8b748c1bf49e0929ab032c54d36572d37c1b9628d996daa1014` |
| `chirps/chirps-v3.0.2017.tif` | 2026-10-30 | 4,183,628 | `5c293f974e859dccaed5918cc19edf5d16f88cf3707e4c8c1cbfbbe4f5c9f1ae` |
| `chirps/chirps-v3.0.2018.tif` | 2026-10-30 | 4,176,458 | `73bd1946c2edc481f34a103f3868839442e90d7fabbf8ed9b76829ac3a3afb78` |
| `chirps/chirps-v3.0.2019.tif` | 2026-10-30 | 4,189,338 | `606eb1baeedbf5eba5e81d653c892623c5b320e36fa831e8d85c92a757bb7995` |
| `chirps/chirps-v3.0.2020.tif` | 2026-10-30 | 4,183,026 | `6a0ff681aae2e8ea4f27d5680bacdfa4176736772cc29ccfcf21c6c547331a42` |
| `chirps/chirps-v3.0.2021.tif` | 2026-10-30 | 4,175,250 | `5418193398573e4a76794c74753d53837d377dfa83c73e0b8d822a0d1497e491` |
| `chirps/chirps-v3.0.2022.tif` | 2026-10-30 | 4,177,342 | `bbb062917f3e2839d5eeabdd61f417236d00b203115da54ed6d0532b3ef74ce7` |
| `chirps/chirps-v3.0.2023.tif` | 2026-10-30 | 4,188,850 | `633c0fcf4c4bcf80c7cabaeaf9337fe335234a110b32d51ad097788f7947fcc8` |
| `dane_population/DCD-area-proypoblacion-Mun-2005-2017_VP.xlsx` | 2026-10-30 | 1,600,037 | `0d7e6b896955f37e030e1d4d07389b8db96dc2731fe04095639e036d0ebf579b` |
| `dane_population/PPED-AreaMun-2018-2042_VP.xlsx` | 2026-10-30 | 3,948,350 | `1ea83594ad308becff39934a3977c102919c25740f60439be95d797396d11283` |
| `divipola/gdxc-w37w.json` | 2026-10-30 | 172,803 | `1028ab04c10a08fa860dd89e621de1eb9246710a56102c915f0988ae9e10d63d` |
| `icfes/a8xr-en99_20201_check.csv` | 2026-10-30 | 49 | `812680170a65957e89b09fc9b8f8ab35bdf9a96f359d9920b2134d1b0480bc64` |
| `icfes/kgxf-xxbe_20142_by_mpio_area.csv` | 2026-10-30 | 88,374 | `20be5493c6bbfafb20411b62021bbb67f09207f1fa1efecafce5e318397433ff` |
| `icfes/kgxf-xxbe_20142_count.csv` | 2026-10-30 | 33 | `97adf67dc21ea3d63f0476e615be044e4d175f1704e17f5163f61af18baeae9b` |
| `icfes/kgxf-xxbe_20151_by_mpio_area.csv` | 2026-10-30 | 7,338 | `f89c4b5b00a9e966a8da5fe8c176f8287506299b2a00e22f291e17b290b8c917` |
| `icfes/kgxf-xxbe_20151_count.csv` | 2026-10-30 | 31 | `71c9e5d5afdfc4983c897a0d964557c7adbe69d26209391265fec341f45c1434` |
| `icfes/kgxf-xxbe_20152_by_mpio_area.csv` | 2026-10-30 | 89,025 | `1a401a440040750aaebc267b966b89a96d803fc058c0ec8cfca5d9b1b722d4ce` |
| `icfes/kgxf-xxbe_20152_count.csv` | 2026-10-30 | 33 | `eafa019aec1ce0cdccb2d92f2571adb316a84106a5715be3c23198a4014da0c4` |
| `icfes/kgxf-xxbe_20161_by_mpio_area.csv` | 2026-10-30 | 2,230 | `9a7590ec7ecdd69dc9b4f91ac5b45c6048091b8c466f14e1e6cf659f253823a0` |
| `icfes/kgxf-xxbe_20161_count.csv` | 2026-10-30 | 31 | `f338ace4230eee1f75b34cd0e56ec4390225027dda7d861af65bd53fc2bfc51b` |
| `icfes/kgxf-xxbe_20162_by_mpio_area.csv` | 2026-10-30 | 88,732 | `c18a515aaa0438ee71ad7d07b84a8b9512071a55102019978dbf1184ed72b861` |
| `icfes/kgxf-xxbe_20162_count.csv` | 2026-10-30 | 33 | `cf13591b2c53d46a07d8e4e0438d8ec742073c934393dd917fb217079569de66` |
| `icfes/kgxf-xxbe_20171_by_mpio_area.csv` | 2026-10-30 | 2,319 | `421768cb62f73d87e7fd3f1077ba51ad85c6ea3ce8a8d9af14fe0a821e54cab0` |
| `icfes/kgxf-xxbe_20171_count.csv` | 2026-10-30 | 31 | `f708514a158e76dd00760973ec6e9d3b8842e1430d9240e4b2ec2e305df851b8` |
| `icfes/kgxf-xxbe_20172_by_mpio_area.csv` | 2026-10-30 | 90,282 | `e0766b156680382f8932f35cc3ead5045f821e6c21d297625744ebfab069db9b` |
| `icfes/kgxf-xxbe_20172_count.csv` | 2026-10-30 | 33 | `9a14e6bfeb3f6f917a6fe6b095b93b0aeec5afa73df184cd7556793b345a823a` |
| `icfes/kgxf-xxbe_20191_by_mpio_area.csv` | 2026-10-30 | 2,280 | `4b3d25fcef6197d32aa8142a7a16f0b861ee9d0ce1e0175ca7d601ca8d57c57e` |
| `icfes/kgxf-xxbe_20191_count.csv` | 2026-10-30 | 31 | `52976897ab1a13e516aadf6dafa5311dbd01b65ab3f276531fd8cf12d5a0e6c9` |
| `icfes/kgxf-xxbe_20194_by_mpio_area.csv` | 2026-10-30 | 90,423 | `7f783129d32d3bd5432a75535b8734b512721430c7bb728cdd190e7ffedfe6e8` |
| `icfes/kgxf-xxbe_20194_count.csv` | 2026-10-30 | 34 | `2aea25f512f485a2b3b17ab74721e83e85067a61951d6485906ce0a05a9da7f0` |
| `icfes/kgxf-xxbe_20201_by_mpio_area.csv` | 2026-10-30 | 5,472 | `7ba8538ab06e6148e5063fa96ad931ad7cf12b651cdb0b3f4b8040c76dd2f046` |
| `icfes/kgxf-xxbe_20201_check.csv` | 2026-10-30 | 49 | `812680170a65957e89b09fc9b8f8ab35bdf9a96f359d9920b2134d1b0480bc64` |
| `icfes/kgxf-xxbe_20201_count.csv` | 2026-10-30 | 31 | `c43765ad818e4817acab395162336109cd07c82f503b4daad00a3ffcdaef1f78` |
| `icfes/kgxf-xxbe_20221_by_mpio_area.csv` | 2026-10-30 | 8,284 | `386c953d01852d2cae4088db3154d531f1f1bc3e5de9d5897cd24dbb947bdd21` |
| `icfes/kgxf-xxbe_20221_count.csv` | 2026-10-30 | 31 | `5bd3988dd03c0908967d00ffbb2ab32e0b369643f184099a96b506bfc1116435` |
| `icfes/kgxf-xxbe_20224_by_mpio_area.csv` | 2026-10-30 | 91,011 | `574315a2b5cea6286f3135f5367d05e91a6c64bfc1263e99c1614127e596b4a8` |
| `icfes/kgxf-xxbe_20224_count.csv` | 2026-10-30 | 34 | `c0b8a7c675075f973dcde65723b4eee239f3cadcd35cf2560a2e7db49ff39ca4` |
| `icfes/rnvb-vnyh_20204_by_mpio_area.csv` | 2026-10-30 | 90,007 | `cfc464ed6930d7574ee60173f5e326b0d5970f370bc7e5fbc618506e0252cf41` |
| `icfes/rnvb-vnyh_20204_count.csv` | 2026-10-30 | 33 | `8b28626c162853745920f55cfb83ae332ea77189c0713002e9fb0f42cb76e85a` |
| `ins_irca/nxt2-39c3.csv` | 2026-10-30 | 1,916,563 | `8b9ec23a7672eaf92272599fe9062dba7e034751ce1bdd9899c363cfa51d9b0f` |
| `men/nudc-7mev_desercion.csv` | 2026-10-30 | 341,088 | `02a24e337335547448f072a715b3046c61f2a55e9511a2122acf11611811de1e` |
| `mgn/MGN2023_MPIO_POLITICO.zip` | 2026-10-30 | 68,233,930 | `d2449dd6b74af7e11ac0f899185d18b0de1e647b00f1ed82580c1561eb96a6c7` |
| `opentopodata/srtm90m_batch00.json` | 2026-10-30 | 14,673 | `e12c0742a834013da3e3c7bb639422f940a1873ddf2cb5e946801da4b59e3c3e` |
| `opentopodata/srtm90m_batch01.json` | 2026-10-30 | 14,609 | `8b108120c4c52ab2a94a1ee011a86163997387da009b71858036f9dfdab94fce` |
| `opentopodata/srtm90m_batch02.json` | 2026-10-30 | 14,707 | `2800335b189b24779dfa0611f323d299fc5d4303ed28d9f0bb38a51b46f038c5` |
| `opentopodata/srtm90m_batch03.json` | 2026-10-30 | 14,687 | `693b8a82bdd67ea211cc9b7f5fa33b3153f7de29bc225e21a80be95c78c322f0` |
| `opentopodata/srtm90m_batch04.json` | 2026-10-30 | 14,619 | `443aa991c1573a9890444e7de2128bbdcc47cd1b8b9d71b0a08b8171c9af98da` |
| `opentopodata/srtm90m_batch05.json` | 2026-10-30 | 14,646 | `0080688b53013101acb211ed4eedc2b12e2cf62557b7dea5e4e83134db7614c7` |
| `opentopodata/srtm90m_batch06.json` | 2026-10-30 | 14,630 | `5d4d1f5ce29e7f5a9f0962066171771d053c7c1f0b7957a1dfc85534b1445c5e` |
| `opentopodata/srtm90m_batch07.json` | 2026-10-30 | 14,667 | `492965e7fc36a84eb64a6830dfe9d6ed228fab47d52d88e6d2619ddcf37d76f6` |
| `opentopodata/srtm90m_batch08.json` | 2026-10-30 | 14,696 | `67e152b339aeea469b4626e792fb35a39c7866f74d80b738c3bab55940d3ff20` |
| `opentopodata/srtm90m_batch09.json` | 2026-10-30 | 14,648 | `14dc10d508f8000968cafed3b35906bf6aab45c2772ad74d04f26ff621c5ec3f` |
| `opentopodata/srtm90m_batch10.json` | 2026-10-30 | 14,650 | `0f6c4bf09eaeace2b1ab6b9e2d5cd5dfa26c4af8c7505ca67fd30ba3ddf42928` |
| `opentopodata/srtm90m_batch11.json` | 2026-10-30 | 3,242 | `b0526a5fda3cfed4091ebf102f96f7637c1b88641cbc0e3314708f2c6777d358` |
| `terridata/TerriData_Dim1.txt.zip` | 2026-10-30 | 1,607,052 | `53980128efd15db3a923953885cbe5a64ab580860ef997669ae76200564d191d` |
| `terridata/TerriData_Dim14.txt.zip` | 2026-10-30 | 952,989 | `17e66bfc7457bf75055a064e385157d9b94efc8310e3c9a762c58bcb1a310ab9` |
| `terridata/TerriData_Dim3.txt.zip` | 2026-10-30 | 4,078,146 | `13287823cb44bbad1087ec3cd9df10982c297ea154fda35f95d0bad433f1e71d` |
| `terridata/TerriData_Dim5.txt.zip` | 2026-10-30 | 8,304,207 | `5fadbf98e247dee24b1c7c8ab915c002137c83f13a8df0f15fe64792531d7caf` |
| `terridata/TerriData_Dim7.txt.zip` | 2026-10-30 | 29,610,199 | `17bb16ce43a4a83a278b4acfc5cf421a452b89e9c877d8a0a2eee70d4b60fba8` |
| `terridata/TerriData_Dim8.txt.zip` | 2026-10-30 | 3,067,381 | `3d590dc7e3a73c1cd954c0aba0210e5658c03ae99164762fcae581b66f16145b` |
<!-- END GENERATED: manifest -->

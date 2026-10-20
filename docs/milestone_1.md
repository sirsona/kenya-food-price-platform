# Milestone 1 — Source Profiling and Architecture

**Status:** ready for review  
**Primary source:** World Bank RTFP Kenya (`KEN_2021_RTFP_v02_M`, v2026-10-05)  
**Supporting source:** WFP Kenya / HDX observed prices  
**Reference geography:** OCHA COD-AB Kenya, 47 counties

## 1. What was built

- A live source profile for the World Bank RTFP Kenya dataset: schema, terms,
  update frequency, coverage and known limitations.
- A supporting profile for WFP Kenya / HDX observed prices, used for product
  breadth and observed-versus-modelled validation.
- An architecture diagram covering sources, Airflow, pandas, Parquet, Postgres,
  governance and Grafana.
- A star-schema design with seven dimensions and two facts, including grain and
  key decisions.
- A canonical product catalogue for the three RTFP commodities, with aliases for
  the equivalent WFP labels.
- A reproducible 47-county reference built from OCHA COD-AB, including a
  simplified GeoJSON and a CSV for the warehouse loader.
- A runnable PostgreSQL 16 DDL for the star schema.
- Design decision records for the source choice, pandas, Grafana, county
  mapping, fact grain, separate index fact and deferred streaming.

## 2. How it works

**Primary source — World Bank RTFP.** The Microdata Library exposes versioned
`KEN_RTFP_mkt_*.zip` files. The pipeline will select the latest version by date,
download it, record a SHA-256 checksum, extract the CSV and unpivot the modelled
close columns (`c_beans`, `c_maize_fao`, `c_livestock_goat_s_fao`) into a long
price table. All rows are flagged as modelled. The separate food price index is
kept in its own fact because it is an index, not a KES price.

**Supporting source — WFP / HDX.** The HDX CKAN API exposes the current
`Kenya - Food Prices` CSV. WFP supplies 51 commodity labels and observed
retail/wholesale prices. Its presence lets the platform compare observed and
modelled levels and extend product coverage beyond the three RTFP commodities.

**Geography.** Market coordinates are assigned to the 47 counties using a
point-in-polygon lookup against OCHA COD-AB admin-1. Districts are not treated as
counties. Markets outside the national boundary remain unmapped and are excluded
from county marts, not guessed.

**Star schema.** `fact_price_observation` is at source × market × product ×
observed date × price type × native unit. The native unit is part of the key so
`KG` and `90 KG` observations are preserved; `price_kes` standardises them to
kg/L/unit. `fact_food_price_index` is at source × market × month.

**Planned runtime.** Docker Compose will run PostgreSQL 16, Airflow 3 and
Grafana. Airflow will schedule weekly source DAGs and a daily warehouse build;
pandas will clean and normalise; Parquet will hold bronze/silver/gold layers;
Postgres will serve the star schema and marts.

## 3. How it was tested

- **Live source profile, 20 October 2026:** 55,692 RTFP rows × 46 columns, 234
  markets, 2007-01-01 to 2026-10-01; 28,463 WFP rows × 16 columns, 226 markets,
  51 commodity labels, 2006–2026.
- **County reference:** 47 county features, 47 unique codes, all geometries
  valid. Test coordinates for Nairobi and Mombasa map correctly; a coordinate
  outside Kenya returns no county.
- **DDL:** executed successfully against a disposable PostgreSQL 16 container;
  all nine warehouse tables created without errors.
- **Configuration:** `metadata/sources.yml`, `metadata/products.yml` and the
  county CSV were parsed and checked for required fields and uniqueness.
- **Automated tests:** five reference tests pass (`uv run pytest`), covering the
  source catalogue, product catalogue, 47-county CSV, GeoJSON validity/mapping
  and expected schema tables.
- **Scope note:** pipeline code, Airflow DAGs, warehouse loading and the
  dashboard are intentionally not part of Milestone 1; they are the next
  milestones.

## 4. Known limitations

- RTFP is modelled, not observed, and covers only beans, maize and live goat.
- Only 27 of 47 counties have market observations. Missing counties will be shown
  as no-data; the platform will not interpolate them.
- The RTFP index contains a 2023–24 structural break. It is documented now and
  will be handled in the analytics layer.
- WFP coverage is sparse and concentrated in arid and semi-arid markets.
- Neither source is the official KNBS CPI. KNBS is the official benchmark and a
  future validation adapter.

## 5. Evidence

- Source profile: [`source_profile.md`](source_profile.md)
- Architecture and ERD: [`architecture.md`](architecture.md)
- Data dictionary: [`data_dictionary.md`](data_dictionary.md)
- Design decisions: [`decisions.md`](decisions.md)
- Source catalogue: [`metadata/sources.yml`](../metadata/sources.yml)
- Product catalogue: [`metadata/products.yml`](../metadata/products.yml)
- County reference: [`metadata/counties.csv`](../metadata/counties.csv),
  [`metadata/geo/kenya_counties.geojson`](../metadata/geo/kenya_counties.geojson)
- Star-schema DDL: [`sql/star_schema.sql`](../sql/star_schema.sql)
- Reference build script: [`scripts/build_reference_data.py`](../scripts/build_reference_data.py)

## 6. Submission text

> **What I built**
>
> I profiled and documented the source and architecture for the Kenya Food Price
> & Inflation Platform. The primary permitted source is the World Bank RTFP
> Kenya dataset (`KEN_2021_RTFP_v02_M`, version 2026-10-05): monthly modelled food
> prices by product and market from January 2007 to October 2026, covering 234
> markets, three commodities and a market-level food price index. I recorded the
> 46-column schema, the open-data terms and citation requirement (Andrée, 2021,
> DOI `10.48529/2ZH0-JF55`), and the weekly version/monthly data update
> frequency.
>
> I also profiled WFP Kenya / HDX as a supporting observed-price source: 28,463
> rows, 226 markets, 51 commodity labels, 2006–2026, CC BY-IGO, updated weekly.
> WFP provides product breadth and observed prices; RTFP provides the complete
> monthly panel and food price index. This supports product comparison and an
> observed-versus-modelled validation check.
>
> The architecture uses Docker Compose: Airflow 3 will orchestrate ingestion,
> pandas will clean and normalise, Parquet will hold raw/bronze/silver/gold
> layers, PostgreSQL will store the star schema and marts, and Grafana will serve
> the dashboard. The star schema has `dim_date`, `dim_county` (47 counties),
> `dim_market`, `dim_product`, `dim_product_alias`, `dim_source` and `dim_unit`;
> `fact_price_observation` is at source × market × product × date × price type ×
> native unit, and `fact_food_price_index` is at source × market × month.
>
> The architecture and star schema are documented in `docs/architecture.md`; the
> data dictionary is in `docs/data_dictionary.md`; design decisions are in
> `docs/decisions.md`.
>
> **How it works**
>
> The RTFP pipeline will discover the latest World Bank ZIP, checksum and extract
> it, unpivot the modelled close prices, and flag every row as modelled. WFP will
> be discovered through HDX and retain observed/aggregate flags. Units will be
> converted to kg/L/unit, products mapped through a canonical catalogue, and
> market coordinates mapped to the 47 counties using OCHA COD-AB geometry. The
> price fact keeps the native unit in its key; the index fact is separate because
> it is not a KES price.
>
> **How I tested it**
>
> I profiled the live APIs on 20 October 2026 and verified row counts, columns,
> coverage and licences. I built the 47-county reference and validated the
> point-in-polygon mapping, including known Nairobi/Mombasa coordinates and a
> point outside Kenya. I executed the star-schema DDL against a disposable
> PostgreSQL 16 instance; all nine warehouse tables were created successfully. I
> also parsed and validated the source catalogue, product catalogue and county
> CSV.
>
> **Known limitation**
>
> Only 27 of 47 counties have market observations; missing counties will be shown
> as no-data and will not be interpolated. RTFP is modelled and covers only three
> commodities, so it will be labelled as modelled and cross-checked against WFP
> observed prices.
>
> **Evidence**
>
> `docs/source_profile.md`, `docs/architecture.md`, `docs/data_dictionary.md`,
> `docs/decisions.md`, `metadata/sources.yml`, `sql/star_schema.sql`.

## 7. Next milestone

Milestone 2 will add the re-runnable batch ingestion code, raw snapshots with
checksums, and sample runs. No M2 work is included here.

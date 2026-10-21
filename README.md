# Kenya Food Price & Inflation Platform

A batch data platform for tracking food prices in Kenyan markets, detecting
inflation patterns, and producing county-level evidence.

**Current milestone:** Milestone 1 — source profiling and architecture. The
pipeline code and dashboard are added in later milestones.

## Chosen source

**World Bank RTFP Kenya** — Monthly food price estimates by product and market.

| Item | Detail |
|---|---|
| Reference | `KEN_2021_RTFP_v02_M`, version 2026-10-05 |
| Publisher | World Bank, Development Economics Data Group |
| Access | [World Bank Microdata Library](https://microdata.worldbank.org/catalog/6167) |
| Licence | Open data; citation required |
| Citation | Andrée, B. P. J. (2021). DOI `10.48529/2ZH0-JF55` |
| Update frequency | Weekly versions; monthly observations |
| Coverage | January 2007 – October 2026 |
| Shape | 55,692 rows × 46 columns |
| Markets | 234 |
| Products | Beans, maize, live goat, plus a food price index |
| Currency | KES |

WFP Kenya / HDX will be added later as a supporting observed-price source.

## Schema summary

| Group | Main columns | Notes |
|---|---|---|
| Geography | `ISO3`, `adm1_name`, `adm2_name`, `mkt_name`, `lat`, `lon` | `adm2_name` is a district, not a county |
| Time | `price_date`, `year`, `month` | Monthly, first of month |
| Commodity estimates | `c_beans`, `c_maize_fao`, `c_livestock_goat_s_fao`, `trust_*` | `c_*` is the modelled close price |
| Food price index | `c_food_price_index`, `inflation_food_price_index` | Laspeyres index, January 2018 = 1 |

The raw observation columns are mostly empty; the modelled close columns are
complete for all market-months. Every RTFP price is therefore treated as
modelled.

## Architecture

Airflow schedules the batch, pandas cleans and normalises the data, and a
PostgreSQL warehouse stores the star schema and marts for Grafana.

See [`docs/architecture.md`](docs/architecture.md) for the diagram and
star-schema summary.

## Star schema

Dimensions: date, county, market, product, product alias, source, unit.

- `fact_price_observation`: one row per source × market × product × date ×
  price type × native unit.
- `fact_food_price_index`: one row per source × market × month.

The DDL is in [`sql/star_schema.sql`](sql/star_schema.sql).

## Limitations

- RTFP is modelled, not observed, and covers only three commodities.
- Only 27 of 47 counties have market observations; missing counties are not
  interpolated.
- The food price index contains a 2023–24 structural break.
- RTFP is not the official KNBS CPI.

## Milestone 1 evidence

- [Architecture](docs/architecture.md)
- [Star-schema DDL](sql/star_schema.sql)

## Attribution

World Bank RTFP is open data with a citation requirement. See the citation
above. OCHA COD-AB is used for county reference geography under CC BY-IGO.

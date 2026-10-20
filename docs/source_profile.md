# Source Profile

**Profile date:** 20 October 2026  
**Primary permitted source:** World Bank RTFP Kenya  
**Supporting source:** WFP Kenya / HDX observed prices  
**Reference geography:** OCHA COD-AB Kenya admin-1 (47 counties)

## 1. Primary source: World Bank RTFP Kenya

| Attribute | Detail |
|---|---|
| Dataset | Monthly food price estimates by product and market |
| Reference ID | `KEN_2021_RTFP_v02_M` |
| Version profiled | `2026-10-05` |
| Publisher | World Bank, Development Economics Data Group |
| Distribution | World Bank Microdata Library |
| Landing page | https://microdata.worldbank.org/catalog/6167 |
| Access | Public download API, no authentication |
| Licence | Open data; citation required |
| Update frequency | Weekly dataset versions; monthly observations |
| Coverage | 2007-01-01 to 2026-10-01 |
| Shape | 55,692 rows × 46 columns |
| Markets | 234 |
| Products | Beans, maize, live goat, plus a food price index |
| Currency | KES |

### Required citation

> Andrée, B. P. J. (2021). Monthly food price estimates by product and market
> (Version 2026-10-05). KEN_2021_RTFP_v02_M. Washington, DC: World Bank
> Microdata Library. https://doi.org/10.48529/2ZH0-JF55

### Schema groups

| Group | Representative columns | Notes |
|---|---|---|
| Geography | `ISO3`, `country`, `adm1_name`, `adm2_name`, `mkt_name`, `lat`, `lon`, `geo_id` | `adm2_name` is a district, not a county |
| Time | `price_date`, `year`, `month` | Monthly, first of month |
| Market diagnostics | `currency`, `components`, `start_dense_data`, `last_survey_point`, `data_coverage`, `data_coverage_recent`, `index_confidence_score`, `spatially_interpolated` | Coverage and confidence |
| Commodity estimates | `beans`, `maize_fao`, `livestock_goat_s_fao`, `o_*`, `h_*`, `l_*`, `c_*`, `inflation_*`, `trust_*` | `c_*` is the modelled close estimate |
| Food price index | `o_food_price_index`, `h_*`, `l_*`, `c_food_price_index`, `inflation_food_price_index`, `trust_food_price_index` | Laspeyres index, January 2018 = 1 |

### Profiling findings

- The modelled close columns are complete for all 55,692 market-months. The raw
  observation columns are mostly empty (94–97%), so `c_*` must be used.
- All values are modelled. They must be flagged `is_imputed = true` and labelled
  “modelled” in the dashboard.
- Only three commodities are available. The food price index is the fourth
  series and belongs in a separate fact table.
- The index contains a large structural break: the median index rises from 1.14
  in January 2023 to 7.55 in January 2024, then falls to 1.89 by June 2024. This
  is not plausible inflation and must be excluded from trend/heatmap medians.
- The source distinguishes market-level estimates from official KNBS CPI. It is
  not an official inflation release.

## 2. Supporting source: WFP Kenya / HDX

| Attribute | Detail |
|---|---|
| Dataset | Kenya - Food Prices |
| Publisher | World Food Programme |
| Distribution | Humanitarian Data Exchange (HDX) |
| Landing page | https://data.humdata.org/dataset/wfp-food-prices-for-kenya |
| Access | HDX CKAN API + CSV download |
| Licence | CC BY-IGO |
| Update frequency | Weekly |
| Coverage | 2006-01-15 to 2026-09-15 |
| Shape | 28,463 rows × 16 columns |
| Markets | 226 |
| Commodity labels | 51 |
| Currency | KES |

### Schema

`date`, `admin1`, `admin2`, `market`, `market_id`, `latitude`, `longitude`,
`category`, `commodity`, `commodity_id`, `unit`, `priceflag`, `pricetype`,
`currency`, `price`, `usdprice`.

### Profiling findings

- The panel is sparse and concentrated in arid and semi-arid markets. Only 24
  counties have at least one market.
- 13 unit formats appear (`KG`, `90 KG`, `50 KG`, `200 G`, `500 ML`, `Head`,
  `Bunch`, etc.). Unit conversion is mandatory before comparison.
- `priceflag` distinguishes actual observations from aggregate prices; 9,468
  rows are aggregate.
- All prices are KES. USD prices are present but no second currency is used.
- WFP provides observed retail/wholesale prices and product breadth that RTFP
  does not.

## 3. Reference geography: OCHA COD-AB Kenya

- 47 admin-1 counties.
- GeoJSON and shapefile resources are published on HDX.
- Licence: CC BY-IGO.
- Market coordinates are assigned to counties with a point-in-polygon lookup.
- Coverage: WFP reaches 24 counties, RTFP reaches 27; the union is 27 of 47.
- The 20 counties without market observations are mostly central and western
  high-potential agricultural counties. They will be shown as no-data, not
  interpolated.

## 4. Why not World Bank Open Data / WDI?

The World Bank Open Data API was checked on 20 October 2026:

- `FP.CPI.TOTL.ZG` returns one national annual inflation value per year.
- Food price index indicators (`FP.FPI.TOTL`, `FP.FPI.TOTL.ZG`) are not
  populated for Kenya.
- WDI has no monthly, market, county or commodity dimension.

WDI cannot support the brief’s product, county and monthly requirements. World
Bank RTFP is the World Bank product with the required granularity.

## 5. Why not KNBS CPI as the core source?

KNBS CPI is the official national monthly benchmark, but it is distributed as
PDF/Excel releases, the website is bot-protected, and it is national/urban rather
than a 47-county market panel. It is documented as the official benchmark and
future validation adapter, not the core price source.

## 6. Source validation plan

Each load will check:

1. Required columns present.
2. Minimum row count.
3. Parseable dates and freshness.
4. Positive prices below a configurable ceiling.
5. Units convertible to kg, litre or unit.
6. Commodities mapped to the canonical product catalogue.
7. Market coordinates mapped to a county.
8. No duplicate natural keys.
9. Outlier rate below a threshold.
10. Referential integrity in the warehouse.
11. Cross-source overlap and median difference for maize/beans.

The full source contract is machine-readable in
[`metadata/sources.yml`](../metadata/sources.yml).

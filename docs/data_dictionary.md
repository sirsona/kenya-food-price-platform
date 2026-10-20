# Data Dictionary

This is the target star schema for Milestone 1. The tables are defined in
[`sql/star_schema.sql`](../sql/star_schema.sql); loaders and marts are added in
later milestones.

## 1. Dimensions

### `warehouse.dim_date`

| Column | Type | Description |
|---|---|---|
| `date_key` | integer PK | `YYYYMMDD` |
| `full_date` | date unique | Calendar date |
| `year`, `quarter`, `month` | integer | Calendar parts |
| `month_name`, `month_short` | text | Month labels |
| `month_start`, `month_end` | date | Month boundaries |
| `is_month_start`, `is_month_end` | boolean | Calendar flags |

### `warehouse.dim_county`

| Column | Type | Description |
|---|---|---|
| `county_key` | serial PK | Surrogate key |
| `county_code` | text unique | OCHA code, e.g. `KE047` |
| `county_number` | integer unique | 1–47 |
| `county_name` | text unique | e.g. `Nairobi` |
| `region` | text | Former province, used for the 7-region rollup |
| `area_sqkm` | numeric | County area |
| `center_lat`, `center_lon` | numeric | Representative point |

### `warehouse.dim_market`

| Column | Type | Description |
|---|---|---|
| `market_key` | serial PK | Surrogate key |
| `source_key` | integer FK | Source that reported the market |
| `source_market_id` | text | WFP `market_id` or RTFP `geo_id` |
| `market_name` | text | Original name |
| `market_name_normalized` | text | Lowercase/punctuation-stripped name for cross-source joins |
| `county_key` | integer FK, nullable | County from point-in-polygon |
| `latitude`, `longitude` | numeric | Coordinates |
| `admin1_name`, `admin2_name` | text | Source administrative names |
| `first_seen`, `last_seen` | date | Observation span |

Unique: `(source_key, source_market_id)`.

### `warehouse.dim_product`

| Column | Type | Description |
|---|---|---|
| `product_key` | serial PK | Surrogate key |
| `product_name` | text unique | Canonical name, e.g. `Maize (white)` |
| `category` | text | `cereals`, `pulses`, `meat`, etc. |
| `default_unit` | text | `kg`, `L` or `unit` |
| `is_food` | boolean | `false` for fuel |

### `warehouse.dim_product_alias`

| Column | Type | Description |
|---|---|---|
| `alias_key` | serial PK | Surrogate key |
| `product_key` | integer FK | Canonical product |
| `alias_name` | text | Source label |
| `alias_normalized` | text unique | Case/space-insensitive match key |

### `warehouse.dim_source`

| Column | Type | Description |
|---|---|---|
| `source_key` | serial PK | Surrogate key |
| `source_code` | text unique | `wb_rtfp`, `wfp_kenya`, `cod_ab_ken` |
| `source_name`, `publisher` | text | Source identity |
| `source_type` | text | `modelled_market_prices`, `observed_market_prices`, `reference_geography` |
| `landing_url`, `license` | text | Access and licence |
| `update_frequency` | text | Weekly/annual |
| `citation` | text | Required attribution |
| `coverage_start`, `coverage_end` | date | Declared coverage |

### `warehouse.dim_unit`

| Column | Type | Description |
|---|---|---|
| `unit_key` | serial PK | Surrogate key |
| `unit_native` | text unique | e.g. `90 KG`, `500 ML` |
| `unit_standard` | text | `kg`, `L`, `unit` |
| `conversion_factor` | numeric | Multiplier to the standard unit |
| `description` | text | Human-readable conversion |

## 2. Facts

### `warehouse.fact_price_observation`

Grain: source × market × product × observed date × price type × native unit.

| Column | Type | Description |
|---|---|---|
| `price_observation_key` | bigserial PK | Surrogate key |
| `date_key` | integer FK | Observed date |
| `observed_date` | date | Survey/estimate date |
| `month` | date | Month start |
| `market_key`, `product_key`, `source_key` | integer FK | Dimensions |
| `price_type` | text | `retail`, `wholesale` or `market` |
| `price_flag` | text | `actual`, `aggregate`, `mixed` or `modelled` |
| `price_native` | numeric | Price in the native unit |
| `unit_native` | text | e.g. `90 KG` |
| `price_kes` | numeric | Standardised price in KES per kg/L/unit |
| `price_usd` | numeric, nullable | USD reference |
| `price_low`, `price_high` | numeric, nullable | RTFP modelled range |
| `unit_standard` | text | `kg`, `L`, `unit` |
| `conversion_factor` | numeric | Applied factor |
| `is_imputed` | boolean | `true` for RTFP |
| `confidence_score` | numeric(5,4) | 0–1 |
| `is_outlier` | boolean | IQR flag; rows are retained |
| `run_id` | uuid | Load run |
| `created_at` | timestamptz | Load timestamp |

Unique: `(source_key, market_key, product_key, observed_date, price_type,
unit_native, unit_standard)`.

### `warehouse.fact_food_price_index`

Grain: source × market × month.

| Column | Type | Description |
|---|---|---|
| `food_index_key` | bigserial PK | Surrogate key |
| `date_key` | integer FK | Month start |
| `month` | date | Month start |
| `market_key`, `source_key` | integer FK | Dimensions |
| `index_value` | numeric | RTFP Laspeyres index (Jan 2018 = 1) |
| `inflation_yoy_pct` | numeric | Reported YoY, retained for audit |
| `confidence_score` | numeric(5,4) | Trust / 10 |
| `spatially_interpolated` | boolean | RTFP flag |
| `is_outlier` | boolean | `abs(YoY) > 200` flag |
| `run_id` | uuid | Build run |

Unique: `(source_key, market_key, month)`.

## 3. Governance (planned)

- `governance.etl_run` — run id, DAG/task, source, input path/checksum, row
  counts, status, timestamps, error.
- `governance.lineage_edge` — upstream dataset, downstream dataset,
  transformation.
- `governance.dq_result` — check name, severity, status, observed/expected
  values.
- `governance.source_catalog` — machine-readable source contract.

## 4. Accepted values

| Field | Values |
|---|---|
| `price_type` | `retail`, `wholesale`, `market` |
| `price_flag` | `actual`, `aggregate`, `mixed`, `modelled` |
| `unit_standard` | `kg`, `L`, `unit` |
| `source_type` | `modelled_market_prices`, `observed_market_prices`, `reference_geography` |

## 5. Notes on comparability

- WFP `Retail` and `Wholesale` are separate price types; do not mix them.
- RTFP has no retail/wholesale distinction; its `price_type` is `market`.
- RTFP live goat is per head; WFP goat meat is per kg. They are different
  products.
- Cross-source agreement is valid only for `Maize (white)` and `Beans (dry)` in
  kg.
- A county with fewer than three markets is a weak signal. The platform will
  expose `markets_reporting` rather than hide it.

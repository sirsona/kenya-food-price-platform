# Architecture

## 1. Design goals

- Ingest public food-price data reproducibly.
- Preserve observed and modelled values as distinct facts.
- Normalise currencies, units, products and geography.
- Serve county-level price and inflation questions from a star schema.
- Make every run, rejection and lineage edge auditable.
- Keep the batch path simple enough to defend end-to-end.

## 2. System context

```mermaid
flowchart LR
  subgraph External sources
    WB[World Bank RTFP API]
    HDX[HDX / WFP API]
    OCHA[OCHA COD-AB GeoJSON]
  end

  subgraph Orchestration
    AF[Airflow 3]
  end

  subgraph Processing
    ING[Ingestion\nrequests + checksums]
    CLEAN[pandas\nunits, products, counties]
  end

  subgraph Storage
    RAW[(Raw snapshots\nCSV / ZIP + metadata)]
    LAKE[(Parquet lake\nbronze / silver / gold)]
    STG[(Postgres staging)]
    WH[(Postgres star schema)]
    GOV[(Governance schema)]
  end

  subgraph Serving
    GRAF[Grafana]
  end

  WB --> ING
  HDX --> ING
  OCHA --> CLEAN
  AF -. schedules .-> ING
  AF -. schedules .-> CLEAN
  ING --> RAW
  RAW --> CLEAN
  CLEAN --> LAKE
  CLEAN --> STG
  STG --> WH
  WH --> LAKE
  WH --> GOV
  WH --> GRAF
  GOV --> GRAF
```

## 3. Runtime topology

| Component | Planned implementation | Purpose |
|---|---|---|
| Postgres | PostgreSQL 16 | Airflow metadata, warehouse, governance |
| Airflow | Airflow 3, LocalExecutor | Weekly source DAGs and daily warehouse build |
| Processing | Python 3.12 + pandas | Download, clean, normalise, load |
| Lake | Local Parquet (bronze/silver/gold) | Replayable intermediate layers |
| Dashboard | Grafana 11 | Price trends, county inflation, product comparison |
| Reference server | nginx | Serve the 47-county GeoJSON if a map panel is added |

The stack will run with Docker Compose. No cloud service is required.

## 4. Data layers

| Layer | Content | Retention |
|---|---|---|
| Raw | Downloaded CSV/ZIP + metadata JSON + SHA-256 | Last 12 versions |
| Bronze | Parsed source-shaped Parquet | Latest version |
| Silver | Cleaned, typed, normalised Parquet | Latest version |
| Gold | Exported marts | Latest version |
| Warehouse | Dimensions, facts, marts | Full history |
| Rejected | Rows failing critical validation + reason | Latest version |

Raw files are immutable. The pipeline never edits a downloaded file; it writes a
new silver/gold file from it.

## 5. Star schema

```mermaid
erDiagram
  dim_date ||--o{ fact_price_observation : date_key
  dim_market ||--o{ fact_price_observation : market_key
  dim_product ||--o{ fact_price_observation : product_key
  dim_source ||--o{ fact_price_observation : source_key

  dim_county ||--o{ dim_market : county_key
  dim_source ||--o{ dim_market : source_key
  dim_product ||--o{ dim_product_alias : product_key

  dim_date ||--o{ fact_food_price_index : date_key
  dim_market ||--o{ fact_food_price_index : market_key
  dim_source ||--o{ fact_food_price_index : source_key

  dim_date {
    int date_key PK
    date full_date
    int year
    int month
    date month_start
    date month_end
  }
  dim_county {
    int county_key PK
    text county_code
    text county_name
    text region
    numeric center_lat
    numeric center_lon
  }
  dim_market {
    int market_key PK
    int source_key FK
    text source_market_id
    text market_name
    text market_name_normalized
    int county_key FK
    numeric latitude
    numeric longitude
  }
  dim_product {
    int product_key PK
    text product_name
    text category
    text default_unit
    boolean is_food
  }
  dim_source {
    int source_key PK
    text source_code
    text source_name
    text source_type
    text license
  }
  fact_price_observation {
    bigint price_observation_key PK
    int date_key FK
    date observed_date
    date month
    int market_key FK
    int product_key FK
    int source_key FK
    text price_type
    text price_flag
    numeric price_kes
    text unit_native
    text unit_standard
    boolean is_imputed
    boolean is_outlier
  }
  fact_food_price_index {
    bigint food_index_key PK
    int date_key FK
    date month
    int market_key FK
    int source_key FK
    numeric index_value
    numeric inflation_yoy_pct
    boolean spatially_interpolated
  }
```

### Grain decisions

- `fact_price_observation` is one row per **source × market × product × observed
  date × price type × native unit**. The native unit is in the key so `KG` and
  `90 KG` observations on the same day are preserved; `price_kes` standardises
  them to kg/L/unit.
- `fact_food_price_index` is one row per **source × market × month**. The index is
  not a price in KES and must not be mixed into the price fact.

## 6. Planned marts

| Mart | Grain | Questions |
|---|---|---|
| `mart_price_monthly` | month × county × market × product | What is the median price? |
| `mart_commodity_monthly` | month × product | How have prices changed over time? |
| `mart_county_inflation` | month × county | Which counties have the highest inflation? |
| `mart_product_county_latest` | product × county at latest covered month | Where is this product cheapest/most expensive? |
| `mart_source_agreement` | month × product × market | Do observed and modelled prices agree? |
| `mart_pipeline_health` | source | Is the pipeline fresh and passing checks? |

## 7. Planned orchestration

| DAG | Schedule | Responsibility |
|---|---|---|
| `wfp_kenya_ingest` | Weekly | HDX discovery, download, checksum, silver |
| `wb_rtfp_ingest` | Weekly | RTFP version discovery, download, checksum, silver |
| `build_food_price_warehouse` | Daily | Upsert dimensions/facts, refresh marts, quality checks |
| `kenya_food_prices_pipeline` | Manual | End-to-end backfill/demo |

Idempotency is enforced through natural-key upserts. Critical quality failures
fail the DAG; warnings are recorded and shown in the dashboard.

## 8. Design principles

1. **Observed vs modelled is explicit.** RTFP is modelled; WFP is observed.
2. **No silent interpolation.** Missing counties remain missing.
3. **Native and standard units are both stored.**
4. **Raw data is immutable and checksummed.**
5. **Every fact row carries a `run_id`.**
6. **Quality results are persisted, not just logged.**
7. **The dashboard reads marts, not raw facts.**
8. **Streaming is optional and comes after the batch path is reproducible.**

## 9. Out of scope for Milestone 1

- Source downloaders and cleaning code (Milestone 2–3).
- Airflow DAG implementation (Milestone 5).
- Dashboard implementation (Milestone 7).
- Kafka/Spark streaming (optional extension).

Milestone 1 delivers the source profile, architecture, star schema and design
decisions that the later milestones implement.

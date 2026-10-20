# Design Decisions

## ADR-001: World Bank RTFP is the primary source; WFP is supporting

**Decision:** Use World Bank RTFP Kenya as the primary permitted source, with WFP
Kenya / HDX as a supporting observed-price source.

**Why:** RTFP gives a complete monthly panel and a market-level food price index,
which the county analysis needs. WFP gives 51 observed commodity labels and
retail/wholesale prices, which RTFP does not. Using both supports product
comparison and an observed-versus-modelled validation join.

**Trade-off:** Two ingestion paths and a product/unit mapping layer. The platform
must clearly label modelled vs observed values.

## ADR-002: pandas for the batch path

**Decision:** Use pandas rather than PySpark for batch ingestion and cleaning.

**Why:** The dataset is small (tens of thousands of source rows, a few hundred
thousand fact rows after unpivoting). pandas is faster to develop, easier to
test and sufficient for one machine. Spark is reserved for the optional
streaming extension.

**Trade-off:** The pipeline is not horizontally scalable. The Parquet contract
keeps a future Spark/DuckDB migration possible.

## ADR-003: PostgreSQL star schema plus Parquet lake

**Decision:** Store raw and intermediate layers as Parquet, and serve analytics
from a PostgreSQL star schema.

**Why:** Parquet is cheap and replayable; Postgres supports SQL marts, Grafana
and transactional upserts. This avoids a separate analytical database at this
volume.

**Trade-off:** Two storage systems to operate. The lake is the source of truth
for rebuilds; Postgres is the serving layer.

## ADR-004: Map markets to 47 counties with point-in-polygon

**Decision:** Use OCHA COD-AB admin-1 (47 counties) and assign market coordinates
with a Shapely point-in-polygon lookup.

**Why:** WFP `admin2` and RTFP `adm2_name` are districts, not counties. A
canonical geometry avoids fragile name matching.

**Trade-off:** Coverage is limited to markets that exist. Only 27 of 47 counties
have data; missing counties are shown as no-data, not interpolated.

## ADR-005: Include the native unit in the price fact grain

**Decision:** `fact_price_observation` is keyed by source × market × product ×
date × price type × native unit.

**Why:** The same commodity can appear as `KG` and `90 KG` on the same date.
Collapsing them would either lose data or create duplicate keys. Storing both
native and standardised prices preserves the observation and enables comparison.

**Trade-off:** Slightly wider fact table. Marts group by the standard unit.

## ADR-006: Separate the food price index fact

**Decision:** Put the RTFP food price index in `fact_food_price_index`, not in
`fact_price_observation`.

**Why:** The index is dimensionless (January 2018 = 1), not a KES price. Mixing
it with prices would corrupt min/max/median calculations and unit semantics.

**Trade-off:** One extra fact table and one extra join path for the dashboard.

## ADR-007: Grafana for the dashboard

**Decision:** Use Grafana with a Postgres datasource.

**Why:** The environment is Linux, Grafana is free, it connects natively to
Postgres, and dashboards/datasources can be provisioned as code. Power BI would
require Windows or the Power BI Service.

**Trade-off:** Grafana’s map and categorical heatmap panels are less polished than
Power BI, but the required price, inflation and comparison views are covered.

## ADR-008: Batch first; streaming is optional

**Decision:** Deliver the reproducible batch path, governance and dashboard
before attempting Kafka/Spark streaming.

**Why:** The brief makes streaming optional and explicitly says to attempt it only
after the batch path is reproducible. A stable batch pipeline is worth more than
a brittle streaming demo.

**Trade-off:** No real-time market feed in the first submission. The fact schema
can support a future daily streaming fact.

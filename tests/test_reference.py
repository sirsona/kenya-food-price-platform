from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]


def test_source_catalogue_has_primary_and_supporting_sources() -> None:
    data = yaml.safe_load((ROOT / "metadata" / "sources.yml").read_text())
    sources = {row["code"]: row for row in data["sources"]}
    assert sources["wb_rtfp"]["role"] == "primary"
    assert sources["wfp_kenya"]["role"] == "supporting"
    for source in sources.values():
        for field in ("code", "name", "publisher", "license", "update_frequency"):
            assert source.get(field), f"{source.get('code')} missing {field}"


def test_product_catalogue_is_unique() -> None:
    data = yaml.safe_load((ROOT / "metadata" / "products.yml").read_text())
    names = [row["canonical_name"] for row in data["products"]]
    assert len(names) == len(set(names))
    assert {"Maize (white)", "Beans (dry)", "Goat (live)"} <= set(names)


def test_county_csv_has_47_unique_counties() -> None:
    frame = pd.read_csv(ROOT / "metadata" / "counties.csv")
    assert len(frame) == 47
    assert frame["county_code"].is_unique
    assert frame["county_name"].is_unique
    assert set(frame["region"]) == {
        "Coast",
        "North Eastern",
        "Eastern",
        "Central",
        "Rift Valley",
        "Western",
        "Nyanza",
        "Nairobi",
    }


def test_geojson_has_47_valid_polygons_and_known_points() -> None:
    payload = json.loads((ROOT / "metadata" / "geo" / "kenya_counties.geojson").read_text())
    features = payload["features"]
    assert len(features) == 47
    geometries = [shape(feature["geometry"]) for feature in features]
    assert all(geometry.is_valid for geometry in geometries)
    names = [feature["properties"]["county_name"] for feature in features]
    tree = STRtree(geometries)

    def lookup(latitude: float, longitude: float) -> str | None:
        point = Point(longitude, latitude)
        for index in tree.query(point):
            if geometries[index].covers(point):
                return names[index]
        return None

    assert lookup(-1.286, 36.817) == "Nairobi"
    assert lookup(-4.05, 39.67) == "Mombasa"
    assert lookup(51.5, -0.12) is None


def test_schema_declares_expected_tables() -> None:
    sql = (ROOT / "sql" / "star_schema.sql").read_text()
    for table in (
        "dim_date",
        "dim_county",
        "dim_market",
        "dim_product",
        "dim_product_alias",
        "dim_source",
        "dim_unit",
        "fact_price_observation",
        "fact_food_price_index",
    ):
        assert f"warehouse.{table}" in sql

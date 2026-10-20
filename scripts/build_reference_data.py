"""Build the 47-county reference files from OCHA COD-AB Kenya.

Usage:
    uv run --with shapely python scripts/build_reference_data.py

Outputs:
    metadata/geo/kenya_counties.geojson
    metadata/counties.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
GEO_DIR = ROOT / "metadata" / "geo"
GEO_DIR.mkdir(parents=True, exist_ok=True)

BOUNDARY_URL = (
    "https://data.humdata.org/dataset/2c0b7571-4bef-4347-9b81-b2174c13f9ef/"
    "resource/674ea496-5451-4312-bcab-8aa95fa3f36c/download/"
    "ken_admin_boundaries.geojson.zip"
)

# Former provinces. Counties remain the canonical geography; this rollup is
# only for a complete-coverage view when a county has no market data.
REGION = {
    "Mombasa": "Coast",
    "Kwale": "Coast",
    "Kilifi": "Coast",
    "Tana River": "Coast",
    "Lamu": "Coast",
    "Taita Taveta": "Coast",
    "Garissa": "North Eastern",
    "Wajir": "North Eastern",
    "Mandera": "North Eastern",
    "Marsabit": "Eastern",
    "Isiolo": "Eastern",
    "Meru": "Eastern",
    "Tharaka-Nithi": "Eastern",
    "Embu": "Eastern",
    "Kitui": "Eastern",
    "Machakos": "Eastern",
    "Makueni": "Eastern",
    "Nyandarua": "Central",
    "Nyeri": "Central",
    "Kirinyaga": "Central",
    "Murang'a": "Central",
    "Kiambu": "Central",
    "Turkana": "Rift Valley",
    "West Pokot": "Rift Valley",
    "Samburu": "Rift Valley",
    "Trans Nzoia": "Rift Valley",
    "Uasin Gishu": "Rift Valley",
    "Elgeyo-Marakwet": "Rift Valley",
    "Nandi": "Rift Valley",
    "Baringo": "Rift Valley",
    "Laikipia": "Rift Valley",
    "Nakuru": "Rift Valley",
    "Narok": "Rift Valley",
    "Kajiado": "Rift Valley",
    "Kericho": "Rift Valley",
    "Bomet": "Rift Valley",
    "Kakamega": "Western",
    "Vihiga": "Western",
    "Bungoma": "Western",
    "Busia": "Western",
    "Siaya": "Nyanza",
    "Kisumu": "Nyanza",
    "Homa Bay": "Nyanza",
    "Migori": "Nyanza",
    "Kisii": "Nyanza",
    "Nyamira": "Nyanza",
    "Nairobi": "Nairobi",
}


def download_zip(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(BOUNDARY_URL, headers={"User-Agent": "kenya-food-price-platform/0.1"})
    with urlopen(request, timeout=180) as response:
        destination.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, help="Optional local COD-AB GeoJSON ZIP")
    parser.add_argument("--simplify", type=float, default=0.002)
    args = parser.parse_args()

    zip_path = args.zip or Path("/tmp/opencode/cod-ab-ken.geojson.zip")
    if not zip_path.exists():
        print(f"downloading {BOUNDARY_URL}")
        download_zip(zip_path)

    with ZipFile(zip_path) as archive:
        admin1_name = next(
            name for name in archive.namelist() if name.endswith("ken_admin1.geojson")
        )
        source = json.loads(archive.read(admin1_name))

    features = []
    rows = []
    ordered = sorted(source["features"], key=lambda f: f["properties"]["adm1_pcode"])

    for number, feature in enumerate(ordered, start=1):
        props = feature["properties"]
        name = props["adm1_name"].strip()
        code = props["adm1_pcode"].strip()
        geometry = shape(feature["geometry"])
        simplified = geometry.simplify(args.simplify, preserve_topology=True)
        if simplified.is_empty:
            simplified = geometry
        center = geometry.representative_point()
        region = REGION.get(name)
        if region is None:
            raise ValueError(f"Missing region mapping for {name!r}")

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "county_code": code,
                    "county_number": number,
                    "county_name": name,
                    "region": region,
                    "area_sqkm": round(float(props.get("area_sqkm", 0)), 2),
                    "center_lat": round(center.y, 6),
                    "center_lon": round(center.x, 6),
                },
                "geometry": mapping(simplified),
            }
        )
        rows.append(
            {
                "county_code": code,
                "county_number": number,
                "county_name": name,
                "region": region,
                "area_sqkm": round(float(props.get("area_sqkm", 0)), 2),
                "center_lat": round(center.y, 6),
                "center_lon": round(center.x, 6),
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "name": "kenya_counties",
        "attribution": "OCHA COD-AB Kenya, CC BY-IGO",
        "features": features,
    }
    geo_path = GEO_DIR / "kenya_counties.geojson"
    geo_path.write_text(json.dumps(geojson, separators=(",", ":")), encoding="utf-8")

    csv_path = ROOT / "metadata" / "counties.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {geo_path} ({geo_path.stat().st_size / 1024:.0f} KiB)")
    print(f"wrote {csv_path} ({len(rows)} counties)")


if __name__ == "__main__":
    main()

"""Clip Geofabrik OSM and WorldPop context inputs to the Hanoi boundary."""
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

import osmium
import rasterio
from rasterio.mask import mask
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, mapping, shape

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw" / "public_datasets"
OSM = RAW / "geofabrik" / "vietnam-260930.osm.pbf"
POP = RAW / "worldpop" / "vnm_ppp_2020.tif"
OUT = ROOT / "data" / "public_pilot" / "context"
BOUNDARY = OUT / "hanoi_boundary.geojson"
CONTEXT = OUT / "hanoi_context.json"
RAW_MANIFEST = RAW / "manifest.json"


def boundary_from_pbf():
    found = []

    class BoundaryHandler(osmium.SimpleHandler):
        def area(self, area):
            tags = dict(area.tags)
            name = tags.get("name", "")
            if tags.get("boundary") != "administrative" or tags.get("admin_level") != "4" or "hà nội" not in name.lower():
                return
            polygons = []
            for outer in area.outer_rings():
                exterior = [(p.lon, p.lat) for p in outer]
                holes = [[(p.lon, p.lat) for p in ring] for ring in area.inner_rings(outer)]
                if len(exterior) >= 4:
                    poly = Polygon(exterior, holes)
                    if poly.is_valid and not poly.is_empty:
                        polygons.append(poly)
            if polygons:
                found.append((area.id, tags, MultiPolygon(polygons) if len(polygons) > 1 else polygons[0]))

    BoundaryHandler().apply_file(str(OSM), locations=True, idx="flex_mem")
    if not found:
        raise RuntimeError("Hanoi admin_level=4 polygon was not found in the Geofabrik extract")
    rel_id, tags, geom = max(found, key=lambda x: x[2].area)
    OUT.mkdir(parents=True, exist_ok=True)
    BOUNDARY.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"osm_relation_id": rel_id, "name": tags.get("name"), "admin_level": tags.get("admin_level")}, "geometry": mapping(geom)}]}, ensure_ascii=False), encoding="utf-8")
    return geom, rel_id, tags


def osm_context(boundary):
    counts = {"road_ways": 0, "public_transport_stops": 0, "education_features": 0, "health_features": 0, "other_amenities": 0}
    road_km = 0.0
    amenity_tags = {"school", "university", "college", "kindergarten", "hospital", "clinic", "doctors", "pharmacy", "dentist", "police", "fire_station", "marketplace", "library", "community_centre", "place_of_worship", "bank", "restaurant", "cafe", "supermarket", "park"}
    minx, miny, maxx, maxy = boundary.bounds

    class FeatureHandler(osmium.SimpleHandler):
        def node(self, node):
            nonlocal counts
            tags = dict(node.tags)
            if not tags or not node.location.valid():
                return
            lon, lat = node.location.lon, node.location.lat
            if lon < minx or lon > maxx or lat < miny or lat > maxy:
                return
            amenity = tags.get("amenity")
            is_stop = tags.get("highway") == "bus_stop" or tags.get("public_transport") in {"platform", "stop_position"}
            is_context = is_stop or amenity in amenity_tags or tags.get("leisure") in {"park", "playground", "garden"}
            if not is_context:
                return
            point = Point(lon, lat)
            if not boundary.covers(point):
                return
            if is_stop:
                counts["public_transport_stops"] += 1
            if amenity in {"school", "university", "college", "kindergarten"}:
                counts["education_features"] += 1
            elif amenity in {"hospital", "clinic", "doctors", "pharmacy", "dentist"}:
                counts["health_features"] += 1
            elif amenity in amenity_tags or tags.get("leisure") in {"park", "playground", "garden"}:
                counts["other_amenities"] += 1

        def way(self, way):
            nonlocal road_km
            tags = dict(way.tags)
            amenity = tags.get("amenity")
            is_road = bool(tags.get("highway"))
            if not is_road and amenity not in amenity_tags:
                return
            coords = [(n.lon, n.lat) for n in way.nodes if n.location.valid()]
            if len(coords) < 2:
                return
            xs = [p[0] for p in coords]
            ys = [p[1] for p in coords]
            if max(xs) < minx or min(xs) > maxx or max(ys) < miny or min(ys) > maxy:
                return
            line = LineString(coords)
            if not line.intersects(boundary):
                return
            clipped = line.intersection(boundary)
            if is_road:
                counts["road_ways"] += 1
                # Approximate clipped length using a local haversine sum; adequate for city context.
                lines = [clipped] if clipped.geom_type == "LineString" else list(getattr(clipped, "geoms", []))
                for segment in lines:
                    pts = list(segment.coords)
                    for a, b in zip(pts, pts[1:]):
                        from math import asin, cos, radians, sin, sqrt
                        lon1, lat1 = map(radians, a); lon2, lat2 = map(radians, b)
                        dlat, dlon = lat2 - lat1, lon2 - lon1
                        h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                        road_km += 6371.0088 * 2 * asin(sqrt(min(1.0, h)))
            if amenity:
                if amenity in {"school", "university", "college", "kindergarten"}:
                    counts["education_features"] += 1
                elif amenity in {"hospital", "clinic", "doctors", "pharmacy", "dentist"}:
                    counts["health_features"] += 1
                elif amenity in amenity_tags:
                    counts["other_amenities"] += 1

    FeatureHandler().apply_file(str(OSM), locations=True, idx="flex_mem")
    return {**counts, "road_length_km_approx": round(road_km, 2)}


def clip_population(boundary):
    clipped, transform = None, None
    with rasterio.open(POP) as src:
        clipped, transform = mask(src, [mapping(boundary)], crop=True, filled=False)
        profile = src.profile.copy()
        profile.update(height=clipped.shape[1], width=clipped.shape[2], transform=transform, compress="deflate")
        with rasterio.open(OUT / "worldpop_hanoi_2020.tif", "w", **profile) as dst:
            dst.write(clipped.filled(src.nodata if src.nodata is not None else 0))
        values = clipped[0].compressed()
        valid = values[values >= 0]
        return {"year": 2020, "valid_pixel_count": int(valid.size), "population_sum_estimate": round(float(valid.sum(dtype="float64")), 2), "pixel_value_unit": "people per pixel", "crs": src.crs.to_string(), "resolution_degrees": list(src.res)}


def main():
    parser = argparse.ArgumentParser(description="Clip OSM and WorldPop context to Hanoi.")
    parser.add_argument("--rebuild", action="store_true", help="reprocess pinned source files even when clipped context outputs already exist")
    args = parser.parse_args()
    if not args.rebuild and CONTEXT.exists() and (OUT / "worldpop_hanoi_2020.tif").exists():
        print(f"Using existing clipped context: {CONTEXT}")
        print(CONTEXT.read_text(encoding="utf-8"))
        return
    if BOUNDARY.exists():
        feature = json.loads(BOUNDARY.read_text(encoding="utf-8"))["features"][0]
        boundary = shape(feature["geometry"])
        rel_id = feature["properties"]["osm_relation_id"]
        tags = feature["properties"]
    else:
        boundary, rel_id, tags = boundary_from_pbf()
    osm = osm_context(boundary)
    pop = clip_population(boundary)
    raw_manifest = json.loads(RAW_MANIFEST.read_text(encoding="utf-8"))
    osm_source = next(item for item in raw_manifest["files"] if item["path"].endswith(OSM.name))
    worldpop_source = next(item for item in raw_manifest["files"] if item["path"].endswith("vnm_ppp_2020.tif"))
    reader = osmium.io.Reader(str(OSM))
    try:
        pbf_header = reader.header()
        snapshot_timestamp = pbf_header.get("osmosis_replication_timestamp")
        replication_sequence = int(pbf_header.get("osmosis_replication_sequence_number"))
    finally:
        reader.close()
    snapshot_date = datetime.strptime(OSM.stem.rsplit("-", 1)[1], "%y%m%d").date().isoformat()
    result = {
        "city": "H\u00e0 N\u1ed9i", "boundary_osm_relation_id": rel_id,
        "osm_extract_file": OSM.name, "osm_file_date": snapshot_date,
        "osm_snapshot_data_timestamp_utc": snapshot_timestamp,
        "osm_replication_sequence_number": replication_sequence,
        "osm_source_downloaded_at_utc": raw_manifest.get("downloaded_at_utc"),
        "osm_source_url": osm_source["url"], "osm_source_file_bytes": OSM.stat().st_size,
        "osm_source_sha256": osm_source["sha256"],
        "context_record_written_at_utc": datetime.now(timezone.utc).isoformat(),
        "osm_attribution": "\u00a9 OpenStreetMap contributors, ODbL",
        "osm_counts": osm, "worldpop": pop,
        "worldpop_source_file": POP.name, "worldpop_source_url": worldpop_source["url"],
        "worldpop_source_file_bytes": worldpop_source["bytes"],
        "worldpop_source_sha256": worldpop_source["sha256"],
        "worldpop_source_downloaded_at_utc": raw_manifest.get("downloaded_at_utc"),
        "worldpop_clipped_raster_file": (OUT / "worldpop_hanoi_2020.tif").name,
        "worldpop_clipped_raster_bytes": (OUT / "worldpop_hanoi_2020.tif").stat().st_size,
        "worldpop_attribution": "WorldPop (www.worldpop.org) / University of Southampton; CC BY 4.0; DOI: 10.5258/SOTON/WP00645",
        "join_resolution": "H\u00e0 N\u1ed9i city aggregate only; listing rows have no coordinates or structured district/ward values"
    }
    CONTEXT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

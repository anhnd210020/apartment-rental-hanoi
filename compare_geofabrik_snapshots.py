"""Compare two dated Geofabrik states using its official consecutive .osc.gz update."""
import argparse
import gzip
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import osmium
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parent
DEFAULT_OLD = ROOT / "data/public_pilot/snapshot_comparison/manifests/vietnam-260930.json"
DEFAULT_NEW = ROOT / "data/public_pilot/snapshot_comparison/manifests/vietnam-261001.json"
DEFAULT_OUT = ROOT / "data/public_pilot/snapshot_comparison/vietnam-260930_to_261001.json"
EDUCATION = {"school", "university", "college", "kindergarten"}
HEALTH = {"hospital", "clinic", "doctors", "pharmacy", "dentist"}
OTHER_AMENITIES = {"police", "fire_station", "marketplace", "library", "community_centre", "place_of_worship", "bank", "restaurant", "cafe", "supermarket", "park"}
AMENITIES = EDUCATION | HEALTH | OTHER_AMENITIES
LEISURE_CONTEXT = {"park", "playground", "garden"}
ACTIONS = {"create", "modify", "delete"}
OBJECTS = {"node", "way", "relation"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(project_relative: str) -> Path:
    path = Path(project_relative)
    return path if path.is_absolute() else ROOT / path


def pbf_header(path: Path) -> dict:
    reader = osmium.io.Reader(str(path))
    try:
        header = reader.header()
        return {
            "snapshot_data_timestamp_utc": header.get("osmosis_replication_timestamp"),
            "replication_sequence": int(header.get("osmosis_replication_sequence_number")),
            "generator": header.get("generator"),
        }
    finally:
        reader.close()


def verify_manifest(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    kind = manifest["artifact_kind"]
    if kind == "full_pbf_snapshot":
        source = manifest["local_pbf"]
        path = resolve(source["path"])
        if not path.exists():
            raise FileNotFoundError(path)
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        if actual_size != source["bytes"] or actual_hash != source["sha256"]:
            raise ValueError(f"PBF does not match dated manifest: {path}")
        header = pbf_header(path)
        if header["replication_sequence"] != manifest["replication_sequence"]:
            raise ValueError(f"PBF sequence does not match manifest: {path}")
        if header["snapshot_data_timestamp_utc"] != manifest["snapshot_data_timestamp_utc"]:
            raise ValueError(f"PBF timestamp does not match manifest: {path}")
        manifest["_path"] = path
        return manifest
    if kind == "target_state_via_geofabrik_diff":
        source = manifest["update_file"]
        path = resolve(source["path"])
        if not path.exists():
            raise FileNotFoundError(path)
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        if actual_size != source["bytes"] or actual_hash != source["sha256"]:
            raise ValueError(f"Update file does not match dated manifest: {path}")
        manifest["_path"] = path
        state_path = resolve(manifest["state_file_path"])
        if state_path.stat().st_size != manifest["state_file_bytes"] or sha256_file(state_path) != manifest["state_file_sha256"]:
            raise ValueError("Frozen Geofabrik state file does not match the dated manifest")
        state_text = state_path.read_text(encoding="utf-8")
        sequence = int(re.search(r"^sequenceNumber=(\d+)$", state_text, re.MULTILINE).group(1))
        timestamp = re.search(r"^timestamp=(.+)$", state_text, re.MULTILINE).group(1).replace(r"\:", ":")
        if sequence != manifest["replication_sequence"] or sequence != manifest["update_sequence"] or timestamp != manifest["snapshot_data_timestamp_utc"]:
            raise ValueError("Frozen Geofabrik state.txt does not match the target-state manifest")
        return manifest
    raise ValueError(f"Unsupported manifest artifact_kind: {kind}")


def categories(tags: dict[str, str]) -> set[str]:
    result = set()
    amenity = tags.get("amenity")
    if tags.get("highway"):
        result.add("road")
    if tags.get("highway") == "bus_stop" or tags.get("public_transport") in {"platform", "stop_position"}:
        result.add("public_transport")
    if amenity in EDUCATION:
        result.add("education")
    elif amenity in HEALTH:
        result.add("health")
    elif amenity in AMENITIES or tags.get("leisure") in LEISURE_CONTEXT:
        result.add("other_amenity")
    return result


def compare(old: dict, new: dict, output: Path) -> dict:
    if new["replication_sequence"] != old["replication_sequence"] + 1:
        raise ValueError("This batch comparator requires a single consecutive Geofabrik sequence update")
    if new["snapshot_data_timestamp_utc"] <= old["snapshot_data_timestamp_utc"]:
        raise ValueError("Target snapshot timestamp must follow the baseline timestamp")
    started = time.perf_counter()
    boundary_file = ROOT / "data/public_pilot/context/hanoi_boundary.geojson"
    boundary = shape(json.loads(boundary_file.read_text(encoding="utf-8"))["features"][0]["geometry"])
    operation_counts = Counter()
    by_type = Counter()
    context_memberships = Counter()
    hanoi_context_nodes = Counter()
    unique_operations = set()
    duplicate_operations = 0
    stack = []
    action_stack = []

    with gzip.open(new["_path"], "rb") as stream:
        for event, elem in ET.iterparse(stream, events=("start", "end")):
            name = elem.tag.rsplit("}", 1)[-1]
            if event == "start":
                stack.append(name)
                if name in ACTIONS:
                    action_stack.append(name)
                continue
            if name in OBJECTS:
                action = action_stack[-1] if action_stack else None
                if action not in ACTIONS:
                    raise ValueError(f"OSM object {name} is outside create/modify/delete section")
                object_id = elem.attrib.get("id")
                op_key = (action, name, object_id)
                if op_key in unique_operations:
                    duplicate_operations += 1
                else:
                    unique_operations.add(op_key)
                    operation_counts[action] += 1
                    by_type[(action, name)] += 1
                tags = {tag.attrib.get("k", ""): tag.attrib.get("v", "") for tag in elem if tag.tag.rsplit("}", 1)[-1] == "tag"}
                feature_categories = categories(tags)
                for category in feature_categories:
                    context_memberships[(action, category)] += 1
                if name == "node" and feature_categories and "lat" in elem.attrib and "lon" in elem.attrib:
                    if boundary.covers(Point(float(elem.attrib["lon"]), float(elem.attrib["lat"]))):
                        hanoi_context_nodes[action] += 1
                elem.clear()
            if name in ACTIONS:
                action_stack.pop()
            stack.pop()

    elapsed = round(time.perf_counter() - started, 3)
    boundary_hash = sha256_file(boundary_file)
    result = {
        "comparison_scope": "OSM object operations in the Vietnam extract update; tagged context memberships are classified from changed objects. Hanoi subcounts are limited to changed context-tagged nodes point-in-polygon against the fixed 2026-09-30 Hanoi boundary.",
        "baseline": {key: value for key, value in old.items() if not key.startswith("_")},
        "target_state": {key: value for key, value in new.items() if not key.startswith("_")},
        "change_counts": {
            "added_create": operation_counts["create"],
            "changed_modify": operation_counts["modify"],
            "removed_delete": operation_counts["delete"],
            "unique_object_operations": sum(operation_counts.values()),
            "duplicate_operations_ignored": duplicate_operations,
            "by_action_and_type": {f"{action}_{kind}": by_type[(action, kind)] for action in sorted(ACTIONS) for kind in sorted(OBJECTS)},
            "tagged_context_memberships_vietnam_wide": {f"{action}_{category}": context_memberships[(action, category)] for action in sorted(ACTIONS) for category in ["road", "public_transport", "education", "health", "other_amenity"]},
            "hanoi_context_tagged_node_operations_only": {action: hanoi_context_nodes[action] for action in sorted(ACTIONS)},
        },
        "fixed_hanoi_boundary": {"path": "data/public_pilot/context/hanoi_boundary.geojson", "sha256": boundary_hash, "osm_relation_id": 3807033},
        "processing_seconds": elapsed,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "The target PBF was not downloaded; the newer target state is represented by Geofabrik's official consecutive .osc.gz update and verified state.txt, with the target PBF URL and published size recorded in its manifest.",
            "Create/modify/delete counts cover all changed OSM nodes, ways, and relations in the Vietnam update, not only Hanoi.",
            "Tagged context memberships are based on changed-object tags and are Vietnam-wide. Only node operations with explicit coordinates are filtered to Hanoi; changed way geometry is not spatially resolved, so this is not a full Hanoi context delta.",
            "This comparison does not re-run OSM aggregation or WorldPop processing and is not rental-listing velocity evidence.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-manifest", type=Path, default=DEFAULT_OLD)
    parser.add_argument("--new-manifest", type=Path, default=DEFAULT_NEW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    old = verify_manifest(args.old_manifest)
    new = verify_manifest(args.new_manifest)
    result = compare(old, new, args.output)
    print(json.dumps({"output": str(args.output), **result["change_counts"], "processing_seconds": result["processing_seconds"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

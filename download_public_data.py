"""Download pinned public inputs and verify byte sizes/SHA-256 before use."""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "public_data_manifest.json"


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base = ROOT / "data" / "raw" / "public_datasets"
    for item in manifest["files"]:
        target = base / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.stat().st_size != item["bytes"]:
            request = urllib.request.Request(item["url"], headers={"User-Agent": "IT5427 public-data coursework prototype"})
            with urllib.request.urlopen(request, timeout=90) as response, target.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        digest = hashlib.sha256()
        with target.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = target.stat().st_size
        if actual != item["bytes"] or digest.hexdigest() != item["sha256"]:
            raise RuntimeError(f"Manifest verification failed: {item['path']} size={actual}, sha256={digest.hexdigest()}")
        print(f"OK {item['path']}: {actual} bytes sha256={digest.hexdigest()}")


if __name__ == "__main__":
    main()

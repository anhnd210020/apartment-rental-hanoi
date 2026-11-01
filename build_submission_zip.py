"""Build a source-preserving submission ZIP without local or restricted data."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parent
ARCHIVE_ROOT = "apartment-rental-hanoi"
ALWAYS_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "submission",
}
LOCAL_DATA_SUFFIXES = {
    ".csv",
    ".parquet",
    ".pbf",
    ".tif",
    ".tiff",
    ".zip",
}
KEEP_GENERIC_FINAL = {
    "docs/IT5427_Final_Report_2026-10-29.docx",
    "docs/IT5427_Final_Report_2026-10-29.pdf",
}
SHARED_METADATA = {
    "reproducibility/public_inputs.manifest.json",
    "reproducibility/curation/kaggle_hanoi_title_review.csv",
    "reproducibility/curation/kaggle_price_period_review.csv",
}


def include_file(path: Path) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    parts = rel.parts
    if any(part in ALWAYS_EXCLUDE_DIRS for part in parts):
        return False
    if parts[0] == "data":
        return len(parts) >= 3 and parts[1] == "fixtures"
    if parts[0] == "reproducibility":
        return rel.as_posix() in SHARED_METADATA
    if path.name.startswith(".") and path.name not in {".gitignore"}:
        return False
    if path.suffix.casefold() in LOCAL_DATA_SUFFIXES:
        return False
    if path.suffix.casefold() == ".jsonl" and not rel.as_posix().startswith("data/fixtures/"):
        return False
    if rel.as_posix() in {
        "docs/IT5427_Final_Report.docx",
        "docs/IT5427_Final_Report.pdf",
    }:
        return False
    if rel.as_posix().startswith("docs/") and path.suffix.casefold() in {".docx", ".pdf"}:
        return rel.as_posix() in KEEP_GENERIC_FINAL
    return path.is_file()


def package_files() -> list[Path]:
    result: list[Path] = []
    for current, directories, filenames in os.walk(PROJECT_ROOT):
        folder = Path(current)
        rel_folder = folder.relative_to(PROJECT_ROOT)
        directories[:] = [name for name in directories if name not in ALWAYS_EXCLUDE_DIRS]
        if rel_folder == Path("data"):
            directories[:] = [name for name in directories if name == "fixtures"]
        elif rel_folder.parts and rel_folder.parts[0] == "data" and rel_folder != Path("data/fixtures"):
            directories.clear()
        for filename in filenames:
            path = folder / filename
            if include_file(path):
                result.append(path)
    return sorted(result, key=lambda item: item.relative_to(PROJECT_ROOT).as_posix().casefold())


def build(output: Path) -> tuple[list[str], Path]:
    files = package_files()
    required = {
        "README.md",
        "requirements.txt",
        "requirements-synthetic.txt",
        "pipeline.py",
        "dashboard.py",
        "public_data_manifest.json",
        "data/fixtures/batdongsan.jsonl",
        "data/fixtures/homedy.jsonl",
        "data/fixtures/nhatot.jsonl",
        "docs/IT5427_Final_Report_2026-10-29.docx",
        "docs/IT5427_Final_Report_2026-10-29.pdf",
        "docs/IT5427_final_presentation.pptx",
    }
    present = {path.relative_to(PROJECT_ROOT).as_posix() for path in files}
    missing = sorted(required - present)
    if missing:
        raise RuntimeError(f"Required submission files missing: {missing}")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            name = f"{ARCHIVE_ROOT}/{rel}"
            archive.write(path, name)
            names.append(name)

    listing = output.with_suffix(".files.txt")
    listing.write_text("\n".join(names) + "\n", encoding="utf-8")
    return names, listing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "submission" / "IT5427_Final_Submission_2026-10-29.zip",
    )
    args = parser.parse_args()
    names, listing = build(args.output)
    print(f"ZIP: {args.output.resolve()} ({args.output.resolve().stat().st_size:,} bytes)")
    print(f"Files: {len(names)}")
    print(f"File list: {listing.resolve()}")


if __name__ == "__main__":
    main()

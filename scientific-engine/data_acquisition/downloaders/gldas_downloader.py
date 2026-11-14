from pathlib import Path
code = r'''"""
NASA GLDAS Downloader
=====================

Searches NASA Earthdata CMR for GLDAS gridded land-surface data and optionally
downloads granules.

Default product:
    GLDAS_NOAH025_3H.2.1
    GLDAS Noah Land Surface Model L4, 0.25 degree, 3-hourly, Version 2.1

Data access:
    NASA GES DISC / Earthdata CMR

Install:
    pip install requests python-dotenv

Configure root .env or ~/.netrc:
    EARTHDATA_USERNAME=your_earthdata_username
    EARTHDATA_PASSWORD=your_earthdata_password

Search example:
    python scientific-engine/data_acquisition/gldas_downloader.py ^
      --start-date 2020-01-01 --end-date 2020-01-03 ^
      --bbox "68,6,98,38" --max-granules 10

Download example:
    python scientific-engine/data_acquisition/gldas_downloader.py ^
      --start-date 2020-01-01 --end-date 2020-01-03 ^
      --bbox "68,6,98,38" --max-granules 5 --download

Important:
- This is a CMR granule search/download client, not a data-processing pipeline.
- GLDAS product short names and versions vary by temporal resolution and model.
  Use --short-name and --version to select another collection.
- GLDAS files may be large. Start with a small date range and a few granules.
- Inspect product documentation for variable names, units, fill values and
  scale factors before using the data in scientific analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

CMR_GRANULES_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

DEFAULT_SHORT_NAME = os.getenv(
    "GLDAS_SHORT_NAME", "GLDAS_NOAH025_3H"
)
DEFAULT_VERSION = os.getenv("GLDAS_VERSION", "2.1")
DEFAULT_PROVIDER = os.getenv("GLDAS_PROVIDER", "GES_DISC")

DATA_ROOT = Path(os.getenv("DATA_ROOT", "data"))
DEFAULT_OUTPUT_DIR = DATA_ROOT / "raw" / "gldas"
DEFAULT_METADATA_DIR = DATA_ROOT / "raw" / "gldas_metadata"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("gldas_downloader")


def validate_date(value: str) -> str:
    """Validate a YYYY-MM-DD date."""
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc
    return value


def parse_bbox(value: str) -> tuple[float, float, float, float]:
    """Parse west,south,east,north."""
    try:
        west, south, east, north = (
            float(part.strip()) for part in value.split(",")
        )
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            'Bounding box must be "west,south,east,north".'
        ) from exc

    if not (-180 <= west <= 180 and -180 <= east <= 180):
        raise argparse.ArgumentTypeError("Longitude must be between -180 and 180.")
    if not (-90 <= south <= 90 and -90 <= north <= 90):
        raise argparse.ArgumentTypeError("Latitude must be between -90 and 90.")
    if west >= east or south >= north:
        raise argparse.ArgumentTypeError(
            "Bounding box requires west < east and south < north."
        )
    return west, south, east, north


def make_session() -> requests.Session:
    """Create a requests session using Earthdata credentials if supplied."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Earth-Systems-Trend-Detective/1.0",
            "Accept": "application/json",
        }
    )

    username = os.getenv("EARTHDATA_USERNAME") or os.getenv("EARTHDATA_USER")
    password = os.getenv("EARTHDATA_PASSWORD")
    if username and password:
        session.auth = (username, password)
    else:
        logger.info(
            "No Earthdata credentials found in .env; downloads will rely "
            "on ~/.netrc if configured."
        )
    return session


def search_granules(
    session: requests.Session,
    short_name: str,
    version: str,
    provider: str | None,
    start_date: str,
    end_date: str,
    bbox: tuple[float, float, float, float] | None,
    page_size: int,
    max_granules: int,
) -> list[dict[str, Any]]:
    """Search NASA CMR and collect granule metadata."""
    params: dict[str, Any] = {
        "short_name": short_name,
        "version": version,
        "temporal": f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
        "page_size": min(page_size, 2000),
        "sort_key[]": "start_date",
        "sort_order": "asc",
    }
    if provider:
        params["provider"] = provider
    if bbox:
        west, south, east, north = bbox
        params["bounding_box"] = f"{west},{south},{east},{north}"

    results: list[dict[str, Any]] = []
    page = 1

    while len(results) < max_granules:
        params["page_num"] = page
        logger.info("Searching NASA CMR page %d...", page)

        response = session.get(CMR_GRANULES_URL, params=params, timeout=90)
        response.raise_for_status()
        payload = response.json()
        entries = payload.get("feed", {}).get("entry", [])

        if not entries:
            break

        for entry in entries:
            results.append(entry)
            if len(results) >= max_granules:
                break

        if len(entries) < params["page_size"]:
            break

        page += 1
        time.sleep(0.15)

    return results


def find_data_url(entry: dict[str, Any]) -> str | None:
    """Find a direct granule data URL while avoiding browse and OPeNDAP links."""
    links = entry.get("links", [])

    for link in links:
        href = link.get("href", "")
        rel = link.get("rel", "").lower()
        title = link.get("title", "").upper()
        if not href.startswith("http"):
            continue
        if "opendap" in href.lower():
            continue
        if "data#" in rel or "GET DATA" in title:
            return href

    # Fallback for CMR entries where the data relation is not explicitly labelled.
    valid_suffixes = (".nc", ".nc4", ".hdf", ".h5", ".he5", ".grb", ".grb2")
    for link in links:
        href = link.get("href", "")
        path = urlparse(href).path.lower()
        if href.startswith("https://") and path.endswith(valid_suffixes):
            if "opendap" not in href.lower():
                return href

    return None


def compact_record(entry: dict[str, Any]) -> dict[str, Any]:
    """Return selected metadata fields for CSV output."""
    return {
        "producer_granule_id": entry.get("producer_granule_id"),
        "granule_ur": entry.get("granule_ur"),
        "concept_id": entry.get("id"),
        "collection_concept_id": entry.get("collection_concept_id"),
        "start_time": entry.get("time_start"),
        "end_time": entry.get("time_end"),
        "updated": entry.get("updated"),
        "download_url": find_data_url(entry),
    }


def save_metadata(
    entries: list[dict[str, Any]],
    metadata_dir: Path,
    short_name: str,
    start_date: str,
    end_date: str,
) -> tuple[Path, Path]:
    """Save the complete CMR entries to JSON and a compact CSV index."""
    metadata_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{short_name}_{start_date}_{end_date}"
    json_path = metadata_dir / f"{stem}.json"
    csv_path = metadata_dir / f"{stem}.csv"

    json_path.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    fields = [
        "producer_granule_id",
        "granule_ur",
        "concept_id",
        "collection_concept_id",
        "start_time",
        "end_time",
        "updated",
        "download_url",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            record = compact_record(entry)
            writer.writerow({field: record.get(field) for field in fields})

    return json_path, csv_path


def download_file(
    session: requests.Session,
    url: str,
    destination: Path,
    timeout: int,
    retries: int,
) -> bool:
    """Stream a granule to disk with retry and partial-file cleanup."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and destination.stat().st_size > 0:
        logger.info("Already downloaded; skipping %s", destination.name)
        return True

    partial = destination.with_suffix(destination.suffix + ".part")

    for attempt in range(1, retries + 1):
        try:
            logger.info(
                "Downloading %s (attempt %d/%d)",
                destination.name,
                attempt,
                retries,
            )
            with session.get(
                url,
                stream=True,
                allow_redirects=True,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" in content_type:
                    raise RuntimeError(
                        "Server returned HTML instead of a data file. "
                        "Check Earthdata login and authorization."
                    )

                with partial.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)

            if not partial.exists() or partial.stat().st_size == 0:
                raise RuntimeError("Downloaded file is empty.")

            partial.replace(destination)
            logger.info(
                "Saved %s (%.2f MB)",
                destination,
                destination.stat().st_size / (1024 * 1024),
            )
            return True

        except Exception as exc:
            logger.warning("Download attempt %d failed: %s", attempt, exc)
            partial.unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(attempt * 2)

    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and download NASA GLDAS land-surface granules."
    )
    parser.add_argument("--start-date", required=True, type=validate_date)
    parser.add_argument("--end-date", required=True, type=validate_date)
    parser.add_argument(
        "--bbox",
        type=parse_bbox,
        help='Optional bounding box: "west,south,east,north".',
    )
    parser.add_argument("--short-name", default=DEFAULT_SHORT_NAME)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--max-granules", type=int, default=20)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--metadata-dir", type=Path, default=DEFAULT_METADATA_DIR)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--retries", type=int, default=3)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if date.fromisoformat(args.start_date) > date.fromisoformat(args.end_date):
        parser.error("--start-date must be <= --end-date.")
    if args.max_granules < 1 or args.page_size < 1:
        parser.error("--max-granules and --page-size must be positive.")
    if args.retries < 1:
        parser.error("--retries must be at least 1.")

    session = make_session()

    try:
        entries = search_granules(
            session=session,
            short_name=args.short_name,
            version=args.version,
            provider=args.provider or None,
            start_date=args.start_date,
            end_date=args.end_date,
            bbox=args.bbox,
            page_size=args.page_size,
            max_granules=args.max_granules,
        )
    except requests.RequestException as exc:
        logger.error("NASA CMR search failed: %s", exc)
        return 1

    logger.info(
        "Found %d granules for %s version %s.",
        len(entries),
        args.short_name,
        args.version,
    )

    json_path, csv_path = save_metadata(
        entries,
        args.metadata_dir,
        args.short_name,
        args.start_date,
        args.end_date,
    )
    logger.info("Saved JSON metadata: %s", json_path)
    logger.info("Saved CSV metadata: %s", csv_path)

    if not args.download:
        logger.info("Search-only mode. Add --download to retrieve the granules.")
        return 0

    success = 0
    failed = 0

    for index, entry in enumerate(entries, start=1):
        url = find_data_url(entry)
        if not url:
            logger.warning(
                "No direct data URL for %s",
                entry.get("producer_granule_id", f"granule-{index}"),
            )
            failed += 1
            continue

        filename = Path(urlparse(url).path).name or f"gldas_granule_{index}.dat"
        if download_file(
            session,
            url,
            args.output_dir / filename,
            timeout=args.timeout,
            retries=args.retries,
        ):
            success += 1
        else:
            failed += 1

    logger.info(
        "Download summary: %d successful, %d failed.",
        success,
        failed,
    )
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
'''
path = Path("/mnt/data/gldas_downloader.py")
path.write_text(code, encoding="utf-8")
import py_compile
py_compile.compile(str(path), doraise=True)
print(f"Created and syntax-checked {path} ({len(code.splitlines())} lines).")

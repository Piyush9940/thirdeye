
"""
NASA AIRS Downloader
====================

Dataset:
    AIRS/Aqua L3 Daily Standard Physical Retrieval (AIRS-only)
    Short name : AIRS3STD
    Version    : 7.0
    Provider   : GES_DISC
    Resolution : 1 degree x 1 degree
    Format     : HDF

Features:
    - Search NASA CMR for AIRS granules
    - Filter by date and bounding box
    - Save granule metadata as JSON and CSV
    - Optional Earthdata-authenticated downloads
    - Retry failed downloads
    - Skip existing files
    - Validate downloaded files
    - Load credentials from environment variables or .env

Install:
    pip install requests python-dotenv

Environment variables supported:
    EARTHDATA_TOKEN
    NASA_EARTHDATA_TOKEN
    EARTHDATA_USERNAME
    EARTHDATA_PASSWORD
    NASA_EARTHDATA_USERNAME
    NASA_EARTHDATA_PASSWORD

Example:
    python airs_downloader.py --start-date 2020-01-01 \
        --end-date 2020-01-07 --bbox "68,6,98,38"

Download:
    python airs_downloader.py --start-date 2020-01-01 \
        --end-date 2020-01-07 --bbox "68,6,98,38" --download
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, unquote

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "airs"
DEFAULT_METADATA_DIR = PROJECT_ROOT / "data" / "raw" / "airs_metadata"

CMR_GRANULES_URL = (
    "https://cmr.earthdata.nasa.gov/search/granules.json"
)

SHORT_NAME = "AIRS3STD"
VERSION = "7.0"
PROVIDER = "GES_DISC"

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"

DEFAULT_PAGE_SIZE = 100
DEFAULT_TIMEOUT = 90
DEFAULT_RETRIES = 3

LOGGER = logging.getLogger("airs_downloader")


# ============================================================
# LOGGING
# ============================================================

def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# ============================================================
# DATE AND BBOX VALIDATION
# ============================================================

def validate_date(value: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from exc

    return value


def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None

    try:
        parts = [float(item.strip()) for item in value.split(",")]
    except ValueError as exc:
        raise ValueError(
            "Bounding box must contain four numbers: "
            "west,south,east,north"
        ) from exc

    if len(parts) != 4:
        raise ValueError(
            "Bounding box must contain four values: "
            "west,south,east,north"
        )

    west, south, east, north = parts

    if not (-180 <= west <= 180):
        raise ValueError("West longitude must be between -180 and 180.")

    if not (-180 <= east <= 180):
        raise ValueError("East longitude must be between -180 and 180.")

    if not (-90 <= south <= 90):
        raise ValueError("South latitude must be between -90 and 90.")

    if not (-90 <= north <= 90):
        raise ValueError("North latitude must be between -90 and 90.")

    if south >= north:
        raise ValueError("South latitude must be smaller than north latitude.")

    if west == east:
        raise ValueError("West and east longitudes cannot be equal.")

    return west, south, east, north


def make_temporal_range(
    start_date: str,
    end_date: str,
) -> str:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    if start > end:
        raise ValueError("Start date must not be after end date.")

    return (
        f"{start_date}T00:00:00Z,"
        f"{end_date}T23:59:59Z"
    )


# ============================================================
# SESSION HELPERS
# ============================================================

def create_cmr_session() -> requests.Session:
    """
    CMR catalogue searches are public.
    Do not attach Earthdata credentials to CMR search requests.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    return session


def get_earthdata_credentials() -> dict[str, str | None]:
    token = (
        os.getenv("EARTHDATA_TOKEN")
        or os.getenv("NASA_EARTHDATA_TOKEN")
    )

    username = (
        os.getenv("EARTHDATA_USERNAME")
        or os.getenv("NASA_EARTHDATA_USERNAME")
    )

    password = (
        os.getenv("EARTHDATA_PASSWORD")
        or os.getenv("NASA_EARTHDATA_PASSWORD")
    )

    return {
        "token": token,
        "username": username,
        "password": password,
    }


def create_download_session() -> requests.Session:
    """
    Create a separate session for protected Earthdata downloads.

    Preferred:
        EARTHDATA_TOKEN

    Alternative:
        EARTHDATA_USERNAME + EARTHDATA_PASSWORD
    """
    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
    })

    credentials = get_earthdata_credentials()

    token = credentials["token"]
    username = credentials["username"]
    password = credentials["password"]

    if token:
        session.headers["Authorization"] = f"Bearer {token}"
        LOGGER.info("Earthdata bearer token configured.")

    elif username and password:
        session.auth = (username, password)
        LOGGER.info("Earthdata username/password configured.")

    else:
        LOGGER.warning(
            "No Earthdata credentials found. "
            "CMR search can still work, but protected downloads may fail."
        )

    return session


# ============================================================
# CMR CLIENT
# ============================================================

class CMRClient:
    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> None:
        self.timeout = timeout
        self.page_size = page_size
        self.session = create_cmr_session()

    def search_granules(
        self,
        start_date: str,
        end_date: str,
        bbox: tuple[float, float, float, float] | None = None,
        max_granules: int | None = None,
    ) -> list[dict[str, Any]]:
        temporal = make_temporal_range(start_date, end_date)

        params: dict[str, Any] = {
            "short_name": SHORT_NAME,
            "version": VERSION,
            "provider": PROVIDER,
            "temporal": temporal,
            "page_size": self.page_size,
            "sort_key[]": "start_date",
            "sort_order": "ascending",
        }

        if bbox:
            west, south, east, north = bbox
            params["bounding_box"] = (
                f"{west},{south},{east},{north}"
            )

        LOGGER.info("Searching NASA CMR...")
        LOGGER.info("Short name: %s", SHORT_NAME)
        LOGGER.info("Version: %s", VERSION)
        LOGGER.info("Provider: %s", PROVIDER)
        LOGGER.info("Temporal range: %s", temporal)

        if bbox:
            LOGGER.info("Bounding box: %s", bbox)

        results: list[dict[str, Any]] = []
        page_num = 1

        while True:
            params["page_num"] = page_num

            try:
                response = self.session.get(
                    CMR_GRANULES_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()

            except requests.RequestException as exc:
                LOGGER.error("CMR request failed: %s", exc)
                raise

            except ValueError as exc:
                LOGGER.error("CMR returned invalid JSON.")
                raise RuntimeError(
                    "Could not parse NASA CMR response."
                ) from exc

            items = (
                payload.get("feed", {})
                .get("entry", [])
            )

            if not items:
                break

            results.extend(items)

            LOGGER.info(
                "CMR page %s: received %s granules.",
                page_num,
                len(items),
            )

            if max_granules and len(results) >= max_granules:
                results = results[:max_granules]
                break

            if len(items) < self.page_size:
                break

            page_num += 1

        LOGGER.info("Total granules found: %s", len(results))
        return results


# ============================================================
# GRANULE METADATA
# ============================================================

def extract_download_links(
    granule: dict[str, Any],
) -> list[str]:
    links: list[str] = []

    for item in granule.get("links", []):
        href = item.get("href")
        rel = str(item.get("rel", "")).lower()

        if not href:
            continue

        if not href.startswith("https://") and not href.startswith("http://"):
            continue

        if "inherited" in rel:
            continue

        if "browse" in rel or "metadata" in rel:
            continue

        if "opendap" in href.lower():
            continue

        if "data#" in rel or "data" in rel:
            links.append(href)

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(links))


def extract_granule_metadata(
    granule: dict[str, Any],
) -> dict[str, Any]:
    links = extract_download_links(granule)

    return {
        "granule_id": granule.get("id"),
        "producer_granule_id": granule.get("producer_granule_id"),
        "collection_concept_id": granule.get("collection_concept_id"),
        "short_name": granule.get("dataset_id"),
        "version": granule.get("version"),
        "start_time": granule.get("time_start"),
        "end_time": granule.get("time_end"),
        "updated": granule.get("updated"),
        "orbit_number": granule.get("orbit_number"),
        "day_night_flag": granule.get("day_night_flag"),
        "cloud_cover": granule.get("cloud_cover"),
        "size_mb": granule.get("granule_size"),
        "download_links": links,
        "all_links": granule.get("links", []),
    }


def build_metadata_records(
    granules: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        extract_granule_metadata(granule)
        for granule in granules
    ]


# ============================================================
# METADATA STORAGE
# ============================================================

def save_metadata(
    records: list[dict[str, Any]],
    metadata_dir: Path,
    start_date: str,
    end_date: str,
) -> tuple[Path, Path]:
    metadata_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    base_name = (
        f"airs3std_{start_date}_{end_date}_{timestamp}"
    )

    json_path = metadata_dir / f"{base_name}.json"
    csv_path = metadata_dir / f"{base_name}.csv"

    payload = {
        "dataset": {
            "short_name": SHORT_NAME,
            "version": VERSION,
            "provider": PROVIDER,
            "description": (
                "AIRS/Aqua Level 3 Daily Standard Physical "
                "Retrieval, AIRS-only, Version 7.0"
            ),
            "nominal_resolution": "1 degree x 1 degree",
        },
        "search": {
            "start_date": start_date,
            "end_date": end_date,
            "generated_utc": timestamp,
            "granule_count": len(records),
        },
        "granules": records,
    }

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    csv_fields = [
        "granule_id",
        "producer_granule_id",
        "collection_concept_id",
        "short_name",
        "version",
        "start_time",
        "end_time",
        "updated",
        "orbit_number",
        "day_night_flag",
        "cloud_cover",
        "size_mb",
        "download_links",
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=csv_fields,
            extrasaction="ignore",
        )

        writer.writeheader()

        for record in records:
            row = dict(record)
            row["download_links"] = ";".join(
                record.get("download_links", [])
            )
            writer.writerow(row)

    LOGGER.info("JSON metadata saved: %s", json_path)
    LOGGER.info("CSV metadata saved: %s", csv_path)

    return json_path, csv_path


# ============================================================
# DOWNLOAD HELPERS
# ============================================================

def safe_filename(url: str, fallback: str) -> str:
    path = unquote(urlparse(url).path)
    filename = Path(path).name

    if not filename:
        filename = fallback

    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    return filename


def is_valid_download(path: Path) -> bool:
    """
    AIRS3STD files are HDF files.

    HDF4 signature:
        0E 03 13 01

    HDF5 signature:
        89 48 44 46 0D 0A 1A 0A

    Some servers may return a valid file with a different
    wrapper or response format. A non-empty file without
    an HTML error page is therefore also retained for inspection.
    """
    if not path.exists() or path.stat().st_size < 512:
        return False

    try:
        with path.open("rb") as file:
            header = file.read(16)
    except OSError:
        return False

    if header.startswith(b"\x0e\x03\x13\x01"):
        return True

    if header.startswith(b"\x89HDF\r\n\x1a\n"):
        return True

    if header.lstrip().lower().startswith(
        (b"<!doctype html", b"<html", b"<?xml")
    ):
        return False

    return True


def download_file(
    session: requests.Session,
    url: str,
    output_path: Path,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and is_valid_download(output_path):
        LOGGER.info("Already downloaded; skipping: %s", output_path.name)
        return True

    partial_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    for attempt in range(1, retries + 1):
        try:
            LOGGER.info(
                "Downloading %s (attempt %s/%s)",
                output_path.name,
                attempt,
                retries,
            )

            with session.get(
                url,
                stream=True,
                timeout=timeout,
                allow_redirects=True,
            ) as response:
                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if "text/html" in content_type:
                    raise RuntimeError(
                        "Server returned HTML instead of a data file. "
                        "Check Earthdata authentication and the download URL."
                    )

                with partial_path.open("wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

            if not is_valid_download(partial_path):
                raise RuntimeError(
                    "Downloaded file failed basic validation."
                )

            partial_path.replace(output_path)

            LOGGER.info(
                "Download complete: %s (%.2f MB)",
                output_path,
                output_path.stat().st_size / (1024 * 1024),
            )

            return True

        except Exception as exc:
            LOGGER.warning(
                "Download attempt %s failed: %s",
                attempt,
                exc,
            )

            if partial_path.exists():
                partial_path.unlink()

            if attempt < retries:
                time.sleep(min(2 ** attempt, 30))

    LOGGER.error("Failed to download: %s", url)
    return False


# ============================================================
# DOWNLOAD GRANULES
# ============================================================

def download_granules(
    records: list[dict[str, Any]],
    output_dir: Path,
    timeout: int,
    retries: int,
) -> tuple[int, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    session = create_download_session()

    success_count = 0
    failure_count = 0

    for index, record in enumerate(records, start=1):
        links = record.get("download_links", [])

        if not links:
            LOGGER.warning(
                "No direct data link found for granule: %s",
                record.get("producer_granule_id"),
            )
            failure_count += 1
            continue

        # AIRS3STD granules normally have one HDF data file.
        url = links[0]

        fallback = (
            record.get("producer_granule_id")
            or f"airs_granule_{index}.hdf"
        )

        filename = safe_filename(url, fallback)

        if not filename.lower().endswith(".hdf"):
            filename = f"{filename}.hdf"

        output_path = output_dir / filename

        LOGGER.info(
            "Granule %s/%s",
            index,
            len(records),
        )

        if download_file(
            session=session,
            url=url,
            output_path=output_path,
            timeout=timeout,
            retries=retries,
        ):
            success_count += 1
        else:
            failure_count += 1

    session.close()

    return success_count, failure_count


# ============================================================
# COMMAND LINE
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search and download NASA AIRS3STD Version 7.0 data."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--start-date",
        type=validate_date,
        required=True,
        help="Start date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--end-date",
        type=validate_date,
        required=True,
        help="End date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--bbox",
        type=str,
        default=None,
        help="Bounding box: west,south,east,north.",
    )

    parser.add_argument(
        "--max-granules",
        type=int,
        default=None,
        help="Maximum number of granules to return.",
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="CMR results per page.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for downloaded AIRS files.",
    )

    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=DEFAULT_METADATA_DIR,
        help="Directory for JSON and CSV metadata.",
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download granule data after searching.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="HTTP request timeout in seconds.",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help="Download retry count.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        if args.max_granules is not None and args.max_granules < 1:
            parser.error("--max-granules must be at least 1.")

        if args.page_size < 1 or args.page_size > 2000:
            parser.error("--page-size must be between 1 and 2000.")

        if args.timeout < 1:
            parser.error("--timeout must be positive.")

        if args.retries < 1:
            parser.error("--retries must be at least 1.")

        bbox = parse_bbox(args.bbox)

        LOGGER.info("=" * 65)
        LOGGER.info("NASA AIRS3STD DOWNLOADER")
        LOGGER.info("=" * 65)
        LOGGER.info("Dataset: %s", SHORT_NAME)
        LOGGER.info("Version: %s", VERSION)
        LOGGER.info("Provider: %s", PROVIDER)
        LOGGER.info("Start date: %s", args.start_date)
        LOGGER.info("End date: %s", args.end_date)

        client = CMRClient(
            timeout=args.timeout,
            page_size=args.page_size,
        )

        granules = client.search_granules(
            start_date=args.start_date,
            end_date=args.end_date,
            bbox=bbox,
            max_granules=args.max_granules,
        )

        records = build_metadata_records(granules)

        save_metadata(
            records=records,
            metadata_dir=args.metadata_dir,
            start_date=args.start_date,
            end_date=args.end_date,
        )

        if not records:
            LOGGER.warning(
                "No AIRS granules found for the selected filters."
            )
            return 0

        LOGGER.info("Granules found: %s", len(records))

        if args.download:
            success, failure = download_granules(
                records=records,
                output_dir=args.output_dir,
                timeout=args.timeout,
                retries=args.retries,
            )

            LOGGER.info("=" * 65)
            LOGGER.info("DOWNLOAD SUMMARY")
            LOGGER.info("Successful: %s", success)
            LOGGER.info("Failed: %s", failure)
            LOGGER.info("Output directory: %s", args.output_dir)
            LOGGER.info("=" * 65)

            return 0 if failure == 0 else 1

        LOGGER.info(
            "Search-only mode. Add --download to download the HDF files."
        )

        return 0

    except (ValueError, RuntimeError, requests.RequestException) as exc:
        LOGGER.error("%s", exc)
        return 1

    except KeyboardInterrupt:
        LOGGER.warning("Interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

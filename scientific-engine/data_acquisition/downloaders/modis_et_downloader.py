
"""
NASA MODIS Evapotranspiration Downloader
=========================================

Project:
    Earth Systems Trend Detective

Dataset:
    MOD16A2GF.061

Product:
    MODIS/Terra Net Evapotranspiration Gap-Filled

Resolution:
    500 metres

Temporal resolution:
    8 days

Format:
    HDF

Data access:
    NASA Earthdata CMR / LP DAAC

Install:
    pip install requests python-dotenv

.env:
    EARTHDATA_USERNAME=your_username
    EARTHDATA_PASSWORD=your_password

Search example (India):
    python scientific-engine/data_acquisition/modis_et_downloader.py `
        --start-date 2020-01-01 `
        --end-date 2020-01-31 `
        --bbox "68,6,98,38" `
        --max-granules 5

Download:
    python scientific-engine/data_acquisition/modis_et_downloader.py `
        --start-date 2020-01-01 `
        --end-date 2020-01-31 `
        --bbox "68,6,98,38" `
        --max-granules 5 `
        --download

Important:
    This script searches and downloads HDF granules.
    It does not yet extract ET layers, apply quality masks,
    mosaic tiles, or convert the data to HEALPix.
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


# ==================================================
# CONFIGURATION
# ==================================================

load_dotenv()

CMR_URL = (
    "https://cmr.earthdata.nasa.gov/"
    "search/granules.json"
)

SHORT_NAME = os.getenv(
    "MODIS_ET_SHORT_NAME",
    "MOD16A2GF"
)

VERSION = os.getenv(
    "MODIS_ET_VERSION",
    "061"
)

PROVIDER = os.getenv(
    "MODIS_ET_PROVIDER",
    "LPDAAC_ECS"
)

DATA_ROOT = Path(
    os.getenv("DATA_ROOT", "data")
)

DEFAULT_OUTPUT_DIR = (
    DATA_ROOT / "raw" / "modis_et"
)

DEFAULT_METADATA_DIR = (
    DATA_ROOT / "raw" / "modis_et_metadata"
)


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("modis_et_downloader")


# ==================================================
# DATE VALIDATION
# ==================================================

def validate_date(value: str) -> str:

    try:

        date.fromisoformat(value)

    except ValueError as exc:

        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}. Use YYYY-MM-DD."
        ) from exc

    return value


# ==================================================
# BOUNDING BOX
# ==================================================

def parse_bbox(value: str):

    try:

        west, south, east, north = (
            float(part.strip())
            for part in value.split(",")
        )

    except Exception as exc:

        raise argparse.ArgumentTypeError(
            'Use bbox format "west,south,east,north".'
        ) from exc

    if not (-180 <= west <= 180):
        raise argparse.ArgumentTypeError(
            "Invalid western longitude."
        )

    if not (-180 <= east <= 180):
        raise argparse.ArgumentTypeError(
            "Invalid eastern longitude."
        )

    if not (-90 <= south <= 90):
        raise argparse.ArgumentTypeError(
            "Invalid southern latitude."
        )

    if not (-90 <= north <= 90):
        raise argparse.ArgumentTypeError(
            "Invalid northern latitude."
        )

    if west >= east or south >= north:

        raise argparse.ArgumentTypeError(
            "West must be less than east and south less than north."
        )

    return west, south, east, north


# ==================================================
# EARTHDATA SESSION
# ==================================================

def create_session():

    session = requests.Session()

    session.headers.update({
        "User-Agent": "Earth-Systems-Trend-Detective/1.0",
        "Accept": "application/json"
    })

    username = (
        os.getenv("EARTHDATA_USERNAME")
        or os.getenv("EARTHDATA_USER")
    )

    password = os.getenv("EARTHDATA_PASSWORD")

    if username and password:

        session.auth = (
            username,
            password
        )

    else:

        logger.info(
            "Earthdata credentials not found in .env. "
            "Downloads will rely on ~/.netrc if configured."
        )

    return session


# ==================================================
# CMR GRANULE SEARCH
# ==================================================

def search_granules(
    session,
    start_date,
    end_date,
    bbox,
    max_granules,
    page_size
):

    params = {

        "short_name": SHORT_NAME,

        "version": VERSION,

        "provider": PROVIDER,

        "temporal": (
            f"{start_date}T00:00:00Z,"
            f"{end_date}T23:59:59Z"
        ),

        "page_size": min(page_size, 2000),

        "sort_key[]": "start_date",

        "sort_order": "asc"
    }

    if bbox:

        west, south, east, north = bbox

        params["bounding_box"] = (
            f"{west},{south},{east},{north}"
        )

    results = []

    page = 1

    while len(results) < max_granules:

        params["page_num"] = page

        logger.info(
            "Searching NASA CMR page %s",
            page
        )

        response = session.get(
            CMR_URL,
            params=params,
            timeout=90
        )

        response.raise_for_status()

        payload = response.json()

        entries = (
            payload
            .get("feed", {})
            .get("entry", [])
        )

        if not entries:
            break

        for entry in entries:

            results.append(entry)

            if len(results) >= max_granules:
                break

        if len(entries) < params["page_size"]:
            break

        page += 1

        time.sleep(0.2)

    return results


# ==================================================
# DOWNLOAD URL EXTRACTION
# ==================================================

def extract_download_url(entry):

    links = entry.get("links", [])

    # Prefer direct data links.

    for link in links:

        href = link.get("href", "")

        rel = link.get("rel", "").lower()

        title = link.get("title", "").upper()

        if not href.startswith("http"):
            continue

        if "opendap" in href.lower():
            continue

        if (
            "data#" in rel
            or "GET DATA" in title
        ):

            return href

    # Fallback for HDF files.

    for link in links:

        href = link.get("href", "")

        path = urlparse(href).path.lower()

        if (
            href.startswith("https://")
            and path.endswith(".hdf")
            and "opendap" not in href.lower()
        ):

            return href

    return None


# ==================================================
# METADATA RECORD
# ==================================================

def create_record(entry):

    return {

        "producer_granule_id":
            entry.get("producer_granule_id"),

        "granule_ur":
            entry.get("granule_ur"),

        "concept_id":
            entry.get("id"),

        "collection_concept_id":
            entry.get("collection_concept_id"),

        "start_time":
            entry.get("time_start"),

        "end_time":
            entry.get("time_end"),

        "updated":
            entry.get("updated"),

        "download_url":
            extract_download_url(entry)
    }


# ==================================================
# SAVE METADATA
# ==================================================

def save_metadata(
    entries,
    metadata_dir,
    start_date,
    end_date
):

    metadata_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"MOD16A2GF_"
        f"{start_date}_{end_date}"
    )

    json_path = (
        metadata_dir / f"{filename}.json"
    )

    csv_path = (
        metadata_dir / f"{filename}.csv"
    )

    json_path.write_text(
        json.dumps(
            entries,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    fields = [
        "producer_granule_id",
        "granule_ur",
        "concept_id",
        "collection_concept_id",
        "start_time",
        "end_time",
        "updated",
        "download_url"
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for entry in entries:

            writer.writerow(
                create_record(entry)
            )

    logger.info(
        "Metadata JSON saved: %s",
        json_path
    )

    logger.info(
        "Metadata CSV saved: %s",
        csv_path
    )


# ==================================================
# DOWNLOAD HDF FILE
# ==================================================

def download_file(
    session,
    url,
    destination,
    timeout=300,
    retries=3
):

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if (
        destination.exists()
        and destination.stat().st_size > 0
    ):

        logger.info(
            "Already downloaded: %s",
            destination.name
        )

        return True

    partial = destination.with_suffix(
        destination.suffix + ".part"
    )

    for attempt in range(1, retries + 1):

        try:

            logger.info(
                "Downloading %s | attempt %s/%s",
                destination.name,
                attempt,
                retries
            )

            with session.get(
                url,
                stream=True,
                allow_redirects=True,
                timeout=timeout
            ) as response:

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type",
                    ""
                ).lower()

                if "text/html" in content_type:

                    raise RuntimeError(
                        "Received HTML instead of HDF data. "
                        "Check Earthdata authentication."
                    )

                with partial.open("wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):

                        if chunk:
                            file.write(chunk)

            if (
                not partial.exists()
                or partial.stat().st_size == 0
            ):

                raise RuntimeError(
                    "Downloaded file is empty."
                )

            partial.replace(destination)

            logger.info(
                "Downloaded successfully: %s (%.2f MB)",
                destination,
                destination.stat().st_size / (1024 * 1024)
            )

            return True

        except Exception as exc:

            logger.warning(
                "Download attempt %s failed: %s",
                attempt,
                exc
            )

            partial.unlink(missing_ok=True)

            if attempt < retries:

                time.sleep(attempt * 2)

    return False


# ==================================================
# ARGUMENT PARSER
# ==================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description=(
            "NASA MODIS MOD16A2GF evapotranspiration downloader"
        )
    )

    parser.add_argument(
        "--start-date",
        required=True,
        type=validate_date
    )

    parser.add_argument(
        "--end-date",
        required=True,
        type=validate_date
    )

    parser.add_argument(
        "--bbox",
        type=parse_bbox,
        help='Bounding box: "west,south,east,north"'
    )

    parser.add_argument(
        "--max-granules",
        type=int,
        default=20
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=100
    )

    parser.add_argument(
        "--download",
        action="store_true"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR
    )

    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=DEFAULT_METADATA_DIR
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=3
    )

    return parser


# ==================================================
# MAIN
# ==================================================

def main():

    parser = build_parser()

    args = parser.parse_args()

    if date.fromisoformat(args.start_date) > date.fromisoformat(args.end_date):

        parser.error(
            "--start-date must be <= --end-date."
        )

    if args.max_granules < 1 or args.page_size < 1:

        parser.error(
            "--max-granules and --page-size must be positive."
        )

    if args.retries < 1 or args.timeout < 1:

        parser.error(
            "--retries and --timeout must be positive."
        )

    session = create_session()

    try:

        entries = search_granules(
            session=session,
            start_date=args.start_date,
            end_date=args.end_date,
            bbox=args.bbox,
            max_granules=args.max_granules,
            page_size=args.page_size
        )

    except requests.RequestException as exc:

        logger.error(
            "NASA CMR search failed: %s",
            exc
        )

        return 1

    logger.info(
        "Found %s MODIS ET granules.",
        len(entries)
    )

    # Save metadata.

    save_metadata(
        entries,
        args.metadata_dir,
        args.start_date,
        args.end_date
    )

    if not args.download:

        logger.info(
            "Search-only mode. Add --download to download granules."
        )

        return 0

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    successful = 0
    failed = 0

    for index, entry in enumerate(entries, start=1):

        url = extract_download_url(entry)

        if not url:

            logger.warning(
                "No download URL found for granule %s",
                entry.get(
                    "producer_granule_id",
                    index
                )
            )

            failed += 1
            continue

        filename = Path(
            urlparse(url).path
        ).name

        if not filename:

            filename = f"modis_et_granule_{index}.hdf"

        destination = args.output_dir / filename

        if download_file(
            session=session,
            url=url,
            destination=destination,
            timeout=args.timeout,
            retries=args.retries
        ):

            successful += 1

        else:

            failed += 1

    logger.info(
        "Download summary | Successful: %s | Failed: %s",
        successful,
        failed
    )

    return 0 if failed == 0 else 2


if __name__ == "__main__":

    sys.exit(main())


"""
NASA OCO-2 Downloader
=====================

Project:
    Earth Systems Trend Detective

Dataset:
    OCO2_L2_Lite_FP

Collection:
    C4203038017-GES_DISC

Version:
    11.3r

Main measurements:
    xco2
    xco2_uncertainty
    xco2_quality_flag
    xco2_apriori
    time
    sounding_id
    vertex_latitude
    vertex_longitude

Features:
    1. Search NASA CMR granules.
    2. Filter by date and bounding box.
    3. Save JSON and CSV metadata.
    4. Download NetCDF files.
    5. Resume downloads by skipping existing files.
    6. Support Earthdata token or .netrc authentication.

Install:
    pip install requests python-dotenv

Search:
    python oco2_downloader.py --start-date 2020-01-01 --end-date 2020-01-31

Download:
    Add --download
"""

import argparse
import csv
import json
import os
import re
import time

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =========================================================
# CONFIGURATION
# =========================================================

CMR_URL = (
    "https://cmr.earthdata.nasa.gov/search/granules.json"
)

SHORT_NAME = "OCO2_L2_Lite_FP"
VERSION = "11.3r"
PROVIDER = "GES_DISC"

COLLECTION_ID = "C4203038017-GES_DISC"

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw" / "oco2"

METADATA_DIR = (
    BASE_DIR / "data" / "raw" / "oco2_metadata"
)

EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN")

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"


# =========================================================
# HTTP SESSION
# =========================================================

def create_session():

    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    })

    if EARTHDATA_TOKEN:
        session.headers["Authorization"] = (
            f"Bearer {EARTHDATA_TOKEN}"
        )

    return session


# =========================================================
# DATE VALIDATION
# =========================================================

def validate_date(value):

    try:
        datetime.strptime(value, "%Y-%m-%d")

    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}. Use YYYY-MM-DD."
        )

    return value


# =========================================================
# BOUNDING BOX VALIDATION
# =========================================================

def validate_bbox(value):

    if not value:
        return None

    try:
        west, south, east, north = map(
            float,
            value.split(",")
        )

    except Exception:
        raise argparse.ArgumentTypeError(
            "Bounding box must be west,south,east,north."
        )

    if not (
        -180 <= west <= 180
        and -180 <= east <= 180
        and -90 <= south <= 90
        and -90 <= north <= 90
        and west < east
        and south < north
    ):
        raise argparse.ArgumentTypeError(
            "Invalid bounding box coordinates."
        )

    return f"{west},{south},{east},{north}"


# =========================================================
# NASA CMR GRANULE SEARCH
# =========================================================

def search_granules(
    session,
    start_date,
    end_date,
    bbox=None,
    page_size=100,
    max_granules=100
):

    print("\nSearching NASA CMR...")
    print(f"Dataset: {SHORT_NAME}")
    print(f"Collection: {COLLECTION_ID}")
    print(f"Version: {VERSION}")
    print(f"Date range: {start_date} to {end_date}")

    params = {
        "collection_concept_id": COLLECTION_ID,
        "short_name": SHORT_NAME,
        "version": VERSION,
        "provider": PROVIDER,
        "temporal": (
            f"{start_date}T00:00:00Z,"
            f"{end_date}T23:59:59Z"
        ),
        "page_size": min(page_size, 2000),
        "sort_key": "-start_date"
    }

    if bbox:
        params["bounding_box"] = bbox
        print(f"Bounding box: {bbox}")

    results = []
    page = 1

    while len(results) < max_granules:

        params["page_num"] = page

        try:

            response = session.get(
                CMR_URL,
                params=params,
                timeout=90
            )

            response.raise_for_status()

            payload = response.json()

        except requests.RequestException as exc:

            print(f"CMR search error: {exc}")
            break

        entries = (
            payload.get("feed", {})
            .get("entry", [])
        )

        if not entries:
            break

        results.extend(entries)

        print(
            f"Page {page}: {len(entries)} granules "
            f"(total: {len(results)})"
        )

        if len(entries) < params["page_size"]:
            break

        page += 1

    return results[:max_granules]


# =========================================================
# DOWNLOAD LINK EXTRACTION
# =========================================================

def extract_download_url(entry):

    links = entry.get("links", [])

    candidates = []

    for link in links:

        href = link.get("href", "")

        if not href.startswith("http"):
            continue

        rel = link.get("rel", "").lower()
        title = link.get("title", "").lower()
        url = href.lower()

        if (
            "opendap" in url
            or "browse" in url
            or "metadata" in url
        ):
            continue

        # Prefer NASA direct data links.
        if "data#" in rel:
            candidates.insert(0, href)
            continue

        if (
            url.endswith(".nc4")
            or ".nc4?" in url
            or url.endswith(".nc")
            or ".nc?" in url
            or url.endswith(".h5")
            or ".h5?" in url
            or "download" in title
        ):
            candidates.append(href)

    return candidates[0] if candidates else None


# =========================================================
# EXTRACT GRANULE METADATA
# =========================================================

def extract_metadata(entry):

    return {
        "granule_id": entry.get("id"),

        "producer_granule_id": entry.get(
            "producer_granule_id"
        ),

        "collection_concept_id": entry.get(
            "collection_concept_id"
        ),

        "short_name": entry.get("short_name"),

        "version": entry.get("version"),

        "start_date": entry.get("time_start"),

        "end_date": entry.get("time_end"),

        "latitude": entry.get("latitude"),

        "longitude": entry.get("longitude"),

        "orbit_number": entry.get("orbit_number"),

        "day_night_flag": entry.get("day_night_flag"),

        "cloud_cover": entry.get("cloud_cover"),

        "download_url": extract_download_url(entry)
    }


# =========================================================
# SAVE METADATA
# =========================================================

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

    records = [
        extract_metadata(entry)
        for entry in entries
    ]

    json_path = metadata_dir / (
        f"oco2_{start_date}_{end_date}.json"
    )

    csv_path = metadata_dir / (
        f"oco2_{start_date}_{end_date}.csv"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=4
        )

    fieldnames = [
        "granule_id",
        "producer_granule_id",
        "collection_concept_id",
        "short_name",
        "version",
        "start_date",
        "end_date",
        "latitude",
        "longitude",
        "orbit_number",
        "day_night_flag",
        "cloud_cover",
        "download_url"
    ]

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)

    print("\nMetadata saved:")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")

    return records


# =========================================================
# DOWNLOAD NETCDF FILE
# =========================================================

def download_file(
    session,
    url,
    output_dir,
    retries=3
):

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = Path(
        urlparse(url).path
    ).name

    if not filename:
        print(f"Invalid download URL: {url}")
        return False

    # Remove unsafe filename characters.
    filename = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        filename
    )

    if not filename.lower().endswith(
        (".nc4", ".nc", ".h5", ".hdf")
    ):
        print(
            f"Skipping unsupported file format: {filename}"
        )
        return False

    output_path = output_dir / filename

    if (
        output_path.exists()
        and output_path.stat().st_size > 0
    ):
        print(f"Already downloaded: {filename}")
        return True

    temp_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    for attempt in range(1, retries + 1):

        try:

            print(
                f"\nDownloading ({attempt}/{retries}): "
                f"{filename}"
            )

            with session.get(
                url,
                stream=True,
                timeout=(30, 600)
            ) as response:

                response.raise_for_status()

                with open(
                    temp_path,
                    "wb"
                ) as file:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):

                        if chunk:
                            file.write(chunk)

            if (
                not temp_path.exists()
                or temp_path.stat().st_size == 0
            ):
                raise IOError(
                    "Downloaded file is empty."
                )

            temp_path.replace(output_path)

            print(f"Saved: {output_path}")

            return True

        except Exception as exc:

            print(f"Download failed: {exc}")

            if temp_path.exists():
                temp_path.unlink()

            if attempt < retries:
                time.sleep(attempt * 3)

    return False


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "NASA OCO-2 L2 Lite FP XCO2 downloader"
        )
    )

    parser.add_argument(
        "--start-date",
        type=validate_date,
        required=True
    )

    parser.add_argument(
        "--end-date",
        type=validate_date,
        required=True
    )

    parser.add_argument(
        "--bbox",
        type=validate_bbox,
        default=None,
        help="west,south,east,north"
    )

    parser.add_argument(
        "--max-granules",
        type=int,
        default=100
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=100
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download NetCDF files"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RAW_DIR
    )

    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=METADATA_DIR
    )

    args = parser.parse_args()

    if args.start_date > args.end_date:
        parser.error(
            "Start date must not be after end date."
        )

    if args.max_granules < 1 or args.page_size < 1:
        parser.error(
            "Granule and page limits must be positive."
        )

    session = create_session()

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    entries = search_granules(
        session=session,
        start_date=args.start_date,
        end_date=args.end_date,
        bbox=args.bbox,
        page_size=args.page_size,
        max_granules=args.max_granules
    )

    if not entries:
        print("\nNo OCO-2 granules found.")
        return

    print(
        f"\nTotal granules found: {len(entries)}"
    )

    # -----------------------------------------------------
    # Save metadata
    # -----------------------------------------------------

    records = save_metadata(
        entries,
        args.metadata_dir,
        args.start_date,
        args.end_date
    )

    # -----------------------------------------------------
    # Search-only mode
    # -----------------------------------------------------

    if not args.download:

        print(
            "\nSearch completed successfully."
            "\nAdd --download to retrieve the NetCDF files."
        )

        return

    # -----------------------------------------------------
    # Download mode
    # -----------------------------------------------------

    print("\nStarting OCO-2 downloads...")

    successful = 0
    failed = 0

    for record in records:

        url = record.get("download_url")

        if not url:

            print(
                "No direct download link for: "
                f"{record.get('producer_granule_id')}"
            )

            failed += 1
            continue

        result = download_file(
            session,
            url,
            args.output_dir
        )

        if result:
            successful += 1
        else:
            failed += 1

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 55)
    print("OCO-2 DOWNLOAD SUMMARY")
    print("=" * 55)

    print(f"Granules found: {len(records)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()

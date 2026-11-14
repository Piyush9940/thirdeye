
"""
MODIS Land Surface Temperature (LST) Downloader
================================================

Dataset:
    MOD11A2.061
    MODIS/Terra Land Surface Temperature and Emissivity
    8-Day L3 Global 1km SIN Grid

Features:
    1. Search NASA CMR for MODIS LST granules.
    2. Filter by date and optional bounding box.
    3. Save granule metadata as JSON and CSV.
    4. Optionally download HDF files.
    5. Resume downloads by skipping existing files.
    6. Support NASA Earthdata authentication through:
       - EARTHDATA_TOKEN environment variable, or
       - ~/.netrc credentials.

Install:
    pip install requests python-dotenv

Example:
    python modis_lst_downloader.py \
        --start-date 2020-01-01 \
        --end-date 2020-01-31 \
        --bbox "68,6,98,38" \
        --max-granules 10

Download:
    Add --download
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

SHORT_NAME = "MOD11A2"
VERSION = "061"

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw" / "modis_lst"
METADATA_DIR = BASE_DIR / "data" / "raw" / "modis_lst_metadata"

EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN")

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"


# ---------------------------------------------------------
# SESSION
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DATE VALIDATION
# ---------------------------------------------------------

def validate_date(value: str) -> str:
    from datetime import datetime

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}. Use YYYY-MM-DD."
        )

    return value


# ---------------------------------------------------------
# BOUNDING BOX
# ---------------------------------------------------------

def validate_bbox(value: Optional[str]):
    if not value:
        return None

    try:
        west, south, east, north = map(
            float, value.split(",")
        )
    except Exception:
        raise argparse.ArgumentTypeError(
            "Bounding box must be west,south,east,north"
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


# ---------------------------------------------------------
# CMR SEARCH
# ---------------------------------------------------------

def search_granules(
    session,
    start_date,
    end_date,
    bbox=None,
    page_size=100,
    max_granules=100
):
    print("\nSearching NASA CMR...")
    print(f"Product: {SHORT_NAME}")
    print(f"Version: {VERSION}")
    print(f"Date range: {start_date} to {end_date}")

    params = {
        "short_name": SHORT_NAME,
        "version": VERSION,
        "temporal": (
            f"{start_date}T00:00:00Z,"
            f"{end_date}T23:59:59Z"
        ),
        "page_size": page_size,
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
                timeout=60
            )
            response.raise_for_status()
            payload = response.json()

        except requests.RequestException as exc:
            print(f"CMR request failed: {exc}")
            break

        entries = payload.get("feed", {}).get("entry", [])

        if not entries:
            break

        results.extend(entries)

        print(
            f"Page {page}: received {len(entries)} granules "
            f"(total: {len(results)})"
        )

        if len(entries) < page_size:
            break

        page += 1

    return results[:max_granules]


# ---------------------------------------------------------
# DOWNLOAD LINK EXTRACTION
# ---------------------------------------------------------

def extract_download_url(entry):
    links = entry.get("links", [])

    for link in links:
        href = link.get("href", "")

        if not href.startswith("http"):
            continue

        rel = link.get("rel", "").lower()
        title = link.get("title", "").lower()
        url = href.lower()

        if (
            "data#" in rel
            or "download" in title
            or url.endswith(".hdf")
            or ".hdf?" in url
        ):
            if "opendap" in url or "browse" in url:
                continue

            return href

    return None


# ---------------------------------------------------------
# METADATA EXTRACTION
# ---------------------------------------------------------

def extract_metadata(entry):
    links = entry.get("links", [])

    return {
        "granule_id": entry.get("id"),
        "producer_granule_id": entry.get(
            "producer_granule_id"
        ),
        "short_name": entry.get("collection_concept_id"),
        "start_date": entry.get("time_start"),
        "end_date": entry.get("time_end"),
        "latitude": entry.get("latitude"),
        "longitude": entry.get("longitude"),
        "cloud_cover": entry.get("cloud_cover"),
        "download_url": extract_download_url(entry),
        "browse_url": next(
            (
                link.get("href")
                for link in links
                if "browse" in link.get("rel", "").lower()
            ),
            None
        )
    }


# ---------------------------------------------------------
# SAVE METADATA
# ---------------------------------------------------------

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
        f"modis_lst_{start_date}_{end_date}.json"
    )

    csv_path = metadata_dir / (
        f"modis_lst_{start_date}_{end_date}.csv"
    )

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4)

    fieldnames = [
        "granule_id",
        "producer_granule_id",
        "short_name",
        "start_date",
        "end_date",
        "latitude",
        "longitude",
        "cloud_cover",
        "download_url",
        "browse_url"
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
    print(f"CSV : {csv_path}")

    return records


# ---------------------------------------------------------
# DOWNLOAD FILE
# ---------------------------------------------------------

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

    filename = Path(urlparse(url).path).name

    if not filename or filename in (".", ".."):
        print(f"Skipping invalid download URL: {url}")
        return False

    if not filename.lower().endswith(".hdf"):
        print(f"Skipping non-HDF link: {url}")
        return False

    output_path = output_dir / filename

    if output_path.exists() and output_path.stat().st_size > 0:
        print(f"Already downloaded: {filename}")
        return True

    for attempt in range(1, retries + 1):
        temp_path = output_path.with_suffix(
            output_path.suffix + ".part"
        )

        try:
            print(
                f"\nDownloading ({attempt}/{retries}): "
                f"{filename}"
            )

            with session.get(
                url,
                stream=True,
                timeout=(30, 300)
            ) as response:

                response.raise_for_status()

                with open(temp_path, "wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

            if not temp_path.exists() or temp_path.stat().st_size == 0:
                raise IOError("Downloaded file is empty.")

            temp_path.replace(output_path)

            print(f"Saved: {output_path}")
            return True

        except Exception as exc:
            print(f"Download failed: {exc}")

            if temp_path.exists():
                temp_path.unlink()

            if attempt < retries:
                time.sleep(3 * attempt)

    return False


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "NASA MODIS Terra Land Surface Temperature "
            "MOD11A2.061 downloader"
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
        help="Download HDF files after searching"
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
        parser.error("Start date must not be after end date.")

    if args.max_granules < 1 or args.page_size < 1:
        parser.error("Granule and page limits must be positive.")

    session = create_session()

    entries = search_granules(
        session=session,
        start_date=args.start_date,
        end_date=args.end_date,
        bbox=args.bbox,
        page_size=args.page_size,
        max_granules=args.max_granules
    )

    if not entries:
        print("\nNo granules found.")
        return

    print(f"\nTotal granules found: {len(entries)}")

    records = save_metadata(
        entries,
        args.metadata_dir,
        args.start_date,
        args.end_date
    )

    if not args.download:
        print(
            "\nSearch completed. Add --download "
            "to download the HDF files."
        )
        return

    print("\nStarting downloads...")

    successful = 0
    failed = 0

    for record in records:
        url = record.get("download_url")

        if not url:
            print(
                "No direct HDF download link for: "
                f"{record.get('producer_granule_id')}"
            )
            failed += 1
            continue

        if download_file(
            session,
            url,
            args.output_dir
        ):
            successful += 1
        else:
            failed += 1

    print("\nDownload summary")
    print("----------------")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print(f"Output:     {args.output_dir}")


if __name__ == "__main__":
    main()

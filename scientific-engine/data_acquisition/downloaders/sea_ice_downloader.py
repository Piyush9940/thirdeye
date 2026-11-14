
"""
NSIDC Sea Ice Index Downloader
==============================

Dataset:
    Sea Ice Index, Version 4
    G02135

Provider:
    NOAA @ NSIDC

Source:
    https://noaadata.apps.nsidc.org/NOAA/G02135/

Downloads:
    Northern Hemisphere daily sea-ice extent CSV
    Southern Hemisphere daily sea-ice extent CSV
    Northern Hemisphere daily climatology CSV
    Southern Hemisphere daily climatology CSV

Features:
    1. Download official NOAA/NSIDC files.
    2. Preserve original raw files.
    3. Generate date-filtered CSV files.
    4. Save metadata JSON.
    5. Skip existing downloads unless --force is used.
    6. Support both Arctic and Antarctic records.

Install:
    pip install requests python-dotenv

Example:
    python sea_ice_downloader.py

Date-filtered:
    python sea_ice_downloader.py \
        --start-date 2000-01-01 \
        --end-date 2025-12-31

Force re-download:
    Add --force

Important:
    Daily extent CSVs are time-series records, not gridded
    sea-ice concentration maps. Use GeoTIFF products for
    spatial concentration and extent analysis.
"""

import argparse
import csv
import json
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

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data" / "raw" / "sea_ice"

BASE_URL = (
    "https://noaadata.apps.nsidc.org/NOAA/G02135"
)

VERSION = "4.0"

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"

HEMISPHERES = {
    "north": {
        "name": "Northern Hemisphere",
        "prefix": "N"
    },
    "south": {
        "name": "Southern Hemisphere",
        "prefix": "S"
    }
}


# =========================================================
# DATASET URLS
# =========================================================

def get_dataset_urls(hemisphere):

    prefix = HEMISPHERES[hemisphere]["prefix"]

    base = (
        f"{BASE_URL}/{hemisphere}/daily/data"
    )

    return {
        "daily_extent": (
            f"{base}/{prefix}_seaice_extent_daily_v{VERSION}.csv"
        ),

        "daily_climatology": (
            f"{base}/{prefix}_seaice_extent_climatology_1981-2010_v{VERSION}.csv"
        )
    }


# =========================================================
# HTTP SESSION
# =========================================================

def create_session():

    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/csv,text/plain,*/*"
    })

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
# DOWNLOAD FILE
# =========================================================

def download_file(
    session,
    url,
    output_path,
    force=False,
    retries=3
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if (
        output_path.exists()
        and output_path.stat().st_size > 0
        and not force
    ):

        print(f"Already downloaded: {output_path.name}")

        return output_path

    temp_path = output_path.with_suffix(
        output_path.suffix + ".part"
    )

    for attempt in range(1, retries + 1):

        try:

            print(
                f"\nDownloading ({attempt}/{retries}): "
                f"{output_path.name}"
            )

            with session.get(
                url,
                stream=True,
                timeout=(30, 180)
            ) as response:

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type", ""
                ).lower()

                if "text/html" in content_type:
                    raise ValueError(
                        "Server returned HTML instead of CSV."
                    )

                with open(temp_path, "wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 256
                    ):

                        if chunk:
                            file.write(chunk)

            if (
                not temp_path.exists()
                or temp_path.stat().st_size == 0
            ):
                raise IOError("Downloaded file is empty.")

            # Reject HTML error pages even if content-type
            # was not correctly provided by the server.
            with open(temp_path, "rb") as file:
                beginning = file.read(512).lower()

            if b"<html" in beginning or b"<!doctype html" in beginning:
                raise ValueError(
                    "Downloaded content is an HTML page, not data."
                )

            temp_path.replace(output_path)

            print(f"Saved: {output_path}")

            return output_path

        except Exception as exc:

            print(f"Download error: {exc}")

            if temp_path.exists():
                temp_path.unlink()

            if attempt < retries:
                time.sleep(attempt * 3)

    return None


# =========================================================
# IDENTIFY DATE IN CSV ROW
# =========================================================

def parse_row_date(row):

    if not row:
        return None

    first_value = row[0].strip().strip('"')

    # YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):

        try:
            return datetime.strptime(
                first_value,
                fmt
            ).date()

        except ValueError:
            pass

    # YYYYMMDD
    if re.fullmatch(r"\d{8}", first_value):

        try:
            return datetime.strptime(
                first_value,
                "%Y%m%d"
            ).date()

        except ValueError:
            pass

    return None


# =========================================================
# FILTER CSV BY DATE
# =========================================================

def filter_csv_by_date(
    input_path,
    output_path,
    start_date=None,
    end_date=None
):

    start = (
        datetime.strptime(start_date, "%Y-%m-%d").date()
        if start_date else None
    )

    end = (
        datetime.strptime(end_date, "%Y-%m-%d").date()
        if end_date else None
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    total_rows = 0
    kept_rows = 0

    with open(
        input_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as source:

        with open(
            output_path,
            "w",
            encoding="utf-8",
            newline=""
        ) as destination:

            for line in source:

                stripped = line.strip()

                # Preserve metadata and comments.
                if not stripped or stripped.startswith("#"):
                    destination.write(line)
                    continue

                row = next(
                    csv.reader([line])
                )

                row_date = parse_row_date(row)

                # Preserve column headers and descriptive rows.
                if row_date is None:
                    destination.write(line)
                    continue

                total_rows += 1

                if start and row_date < start:
                    continue

                if end and row_date > end:
                    continue

                destination.write(line)
                kept_rows += 1

    print("\nDate filtering complete:")
    print(f"Original dated rows: {total_rows}")
    print(f"Rows retained: {kept_rows}")
    print(f"Filtered file: {output_path}")

    return {
        "total_rows": total_rows,
        "filtered_rows": kept_rows
    }


# =========================================================
# PROCESS HEMISPHERE
# =========================================================

def process_hemisphere(
    session,
    hemisphere,
    output_dir,
    start_date=None,
    end_date=None,
    force=False
):

    config = HEMISPHERES[hemisphere]

    print("\n" + "=" * 60)
    print(f"PROCESSING {config['name'].upper()}")
    print("=" * 60)

    raw_dir = output_dir / hemisphere / "raw"
    processed_dir = output_dir / hemisphere / "processed"
    metadata_dir = output_dir / hemisphere / "metadata"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    urls = get_dataset_urls(hemisphere)

    results = {}

    for dataset_name, url in urls.items():

        filename = Path(
            urlparse(url).path
        ).name

        raw_path = raw_dir / filename

        # -------------------------------------------------
        # Download original NOAA file
        # -------------------------------------------------

        downloaded_path = download_file(
            session=session,
            url=url,
            output_path=raw_path,
            force=force
        )

        if not downloaded_path:
            print(f"Failed to download {dataset_name}.")
            results[dataset_name] = False
            continue

        # -------------------------------------------------
        # Filter daily extent records only
        # -------------------------------------------------

        if dataset_name == "daily_extent":

            filtered_path = (
                processed_dir /
                f"{config['prefix']}_seaice_extent_daily_filtered.csv"
            )

            filter_result = filter_csv_by_date(
                input_path=raw_path,
                output_path=filtered_path,
                start_date=start_date,
                end_date=end_date
            )

        else:

            # Climatology is a fixed 1981-2010 reference.
            # Preserve it without filtering by observation dates.
            filtered_path = (
                processed_dir /
                f"{config['prefix']}_seaice_extent_climatology_1981-2010.csv"
            )

            filter_result = {
                "total_rows": None,
                "filtered_rows": None
            }

            with open(
                raw_path,
                "rb"
            ) as source:

                with open(
                    filtered_path,
                    "wb"
                ) as destination:

                    destination.write(source.read())

        results[dataset_name] = True

        # -------------------------------------------------
        # Metadata
        # -------------------------------------------------

        metadata = {
            "dataset": "Sea Ice Index",
            "dataset_id": "G02135",
            "version": VERSION,
            "provider": "NOAA National Snow and Ice Data Center",
            "hemisphere": config["name"],
            "dataset_type": dataset_name,
            "source_url": url,
            "raw_file": str(raw_path),
            "processed_file": str(filtered_path),
            "start_date_filter": start_date,
            "end_date_filter": end_date,
            "total_rows": filter_result["total_rows"],
            "filtered_rows": filter_result["filtered_rows"],
            "downloaded_at_utc": datetime.utcnow().isoformat(),
            "citation": (
                "Fetterer, F., Knowles, K., Meier, W. N., "
                "Savoie, M., Windnagel, A. K. & Stafford, T. "
                "(2025). Sea Ice Index (G02135, Version 4). "
                "National Snow and Ice Data Center. "
                "https://doi.org/10.7265/a98x-0f50"
            )
        }

        metadata_path = (
            metadata_dir /
            f"{dataset_name}_metadata.json"
        )

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4
            )

        print(f"Metadata saved: {metadata_path}")

    return results


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download NOAA/NSIDC Sea Ice Index Version 4"
        )
    )

    parser.add_argument(
        "--start-date",
        type=validate_date,
        default=None
    )

    parser.add_argument(
        "--end-date",
        type=validate_date,
        default=None
    )

    parser.add_argument(
        "--hemisphere",
        choices=["north", "south", "both"],
        default="both"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Download files again even if they already exist."
    )

    args = parser.parse_args()

    if (
        args.start_date
        and args.end_date
        and args.start_date > args.end_date
    ):
        parser.error(
            "Start date must not be after end date."
        )

    if args.hemisphere == "both":
        selected = ["north", "south"]
    else:
        selected = [args.hemisphere]

    session = create_session()

    print("\nNSIDC SEA ICE INDEX DOWNLOADER")
    print("--------------------------------")
    print(f"Dataset: G02135")
    print(f"Version: {VERSION}")
    print(f"Hemisphere: {args.hemisphere}")
    print(f"Start date: {args.start_date or 'Full record'}")
    print(f"End date: {args.end_date or 'Latest available'}")
    print(f"Output: {args.output_dir}")

    all_results = {}

    for hemisphere in selected:

        all_results[hemisphere] = process_hemisphere(
            session=session,
            hemisphere=hemisphere,
            output_dir=args.output_dir,
            start_date=args.start_date,
            end_date=args.end_date,
            force=args.force
        )

    print("\n" + "=" * 60)
    print("FINAL SEA ICE DOWNLOAD SUMMARY")
    print("=" * 60)

    for hemisphere, results in all_results.items():

        print(f"\n{hemisphere.upper()}")

        for dataset_name, success in results.items():

            status = "SUCCESS" if success else "FAILED"

            print(f"  {dataset_name}: {status}")

    print(f"\nOutput directory: {args.output_dir}")


if __name__ == "__main__":
    main()

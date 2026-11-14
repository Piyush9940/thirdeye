
"""
NASA Ocean Color Downloader
============================

Project:
    Earth Systems Trend Detective

Source:
    NASA Ocean Biology Distributed Active Archive Center
    (NASA OB.DAAC)

Default dataset:
    Aqua MODIS Level-3 Standard Mapped Image
    Chlorophyll-a (chlor_a), 4 km

Supported:
    Sensors: Aqua MODIS, Terra MODIS
    Periods: Daily, 8-day, Monthly
    Variable: chlor_a
    Format: NetCDF (.nc)

Features:
    1. Search NASA Ocean Color file archive.
    2. Filter by date and sensor.
    3. Save download URLs.
    4. Save JSON and CSV metadata.
    5. Optionally download NetCDF files.
    6. Skip existing files.
    7. Support Earthdata bearer token.

Install:
    pip install requests python-dotenv

Optional .env:
    EARTHDATA_TOKEN=your_token

Example:
    python ocean_color_downloader.py

    python ocean_color_downloader.py \
        --sensor aqua \
        --period MO \
        --start-date 2020-01-01 \
        --end-date 2020-12-31 \
        --download
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

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data" / "raw" / "ocean_color"

METADATA_DIR = BASE_DIR / "data" / "raw" / "ocean_color_metadata"

FILE_SEARCH_URL = (
    "https://oceandata.sci.gsfc.nasa.gov/file_search"
)

EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN")

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"

SENSORS = {
    "aqua": {
        "name": "Aqua MODIS",
        "sensor_id": 7,
        "dtid": 1043,
        "prefix": "AQUA_MODIS"
    },
    "terra": {
        "name": "Terra MODIS",
        "sensor_id": 8,
        "dtid": 1083,
        "prefix": "TERRA_MODIS"
    }
}

PERIODS = {
    "DAY": "Daily",
    "8D": "8-day",
    "MO": "Monthly"
}

VARIABLES = {
    "chlor_a": {
        "suite": "CHL",
        "unit": "mg m-3",
        "description": "Chlorophyll-a concentration"
    }
}


# =========================================================
# HTTP SESSION
# =========================================================

def create_session():

    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "*/*"
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
# BUILD FILENAME SEARCH PATTERN
# =========================================================

def build_search_pattern(
    sensor_prefix,
    period,
    variable,
    resolution
):

    suite = VARIABLES[variable]["suite"]

    return (
        f"{sensor_prefix}.*"
        f"L3m.{period}.{suite}.{variable}."
        f"{resolution}.nc"
    )


# =========================================================
# SEARCH NASA OCEAN COLOR ARCHIVE
# =========================================================

def search_files(
    session,
    sensor,
    period,
    variable,
    resolution,
    start_date,
    end_date
):

    sensor_config = SENSORS[sensor]

    search_pattern = build_search_pattern(
        sensor_config["prefix"],
        period,
        variable,
        resolution
    )

    payload = {
        "sensor_id": sensor_config["sensor_id"],
        "sensor": sensor,
        "dtype": "L3m",
        "dtid": sensor_config["dtid"],
        "sdate": f"{start_date} 00:00:00",
        "edate": f"{end_date} 23:59:59",
        "addurl": "1",
        "results_as_file": "1",
        "search": search_pattern,
        "format": "txt",
        "std_only": "1"
    }

    print("\nSearching NASA Ocean Color archive...")
    print(f"Sensor: {sensor_config['name']}")
    print(f"Period: {PERIODS[period]}")
    print(f"Variable: {variable}")
    print(f"Resolution: {resolution}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Filename pattern: {search_pattern}")

    try:

        response = session.post(
            FILE_SEARCH_URL,
            data=payload,
            timeout=120
        )

        response.raise_for_status()

        content = response.text

    except requests.RequestException as exc:

        print(f"NASA Ocean Color search failed: {exc}")
        return []

    if "<html" in content[:2000].lower():

        print(
            "The archive returned an HTML response instead "
            "of a text file listing."
        )

        print(content[:500])

        return []

    urls = []

    for line in content.splitlines():

        line = line.strip()

        if not line:
            continue

        # The response may include a message instead of files.
        if line.startswith("#"):
            continue

        if line.startswith("http://") or line.startswith("https://"):

            if ".nc" in line.lower():
                urls.append(line)

        elif line.lower().endswith(".nc"):

            urls.append(
                "https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/"
                + line
            )

    # Remove duplicate URLs while preserving order.
    urls = list(dict.fromkeys(urls))

    print(f"\nFiles found: {len(urls)}")

    return urls


# =========================================================
# EXTRACT DATE FROM FILENAME
# =========================================================

def extract_file_date(filename):

    match = re.search(
        r"\.(\d{8})(?:_(\d{8}))?\.",
        filename
    )

    if not match:
        return None, None

    start = match.group(1)
    end = match.group(2) or start

    return start, end


# =========================================================
# CREATE METADATA RECORDS
# =========================================================

def create_metadata_records(
    urls,
    sensor,
    period,
    variable,
    resolution
):

    records = []

    for url in urls:

        filename = Path(
            urlparse(url).path
        ).name

        start, end = extract_file_date(filename)

        records.append({

            "filename": filename,

            "sensor": SENSORS[sensor]["name"],

            "period": period,

            "variable": variable,

            "description": VARIABLES[variable]["description"],

            "unit": VARIABLES[variable]["unit"],

            "resolution": resolution,

            "start_date": start,

            "end_date": end,

            "download_url": url,

            "source": "NASA Ocean Biology DAAC"

        })

    return records


# =========================================================
# SAVE METADATA
# =========================================================

def save_metadata(
    records,
    metadata_dir,
    sensor,
    period,
    start_date,
    end_date
):

    metadata_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    json_path = metadata_dir / (
        f"ocean_color_{sensor}_{period}_"
        f"{start_date}_{end_date}.json"
    )

    csv_path = metadata_dir / (
        f"ocean_color_{sensor}_{period}_"
        f"{start_date}_{end_date}.csv"
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
        "filename",
        "sensor",
        "period",
        "variable",
        "description",
        "unit",
        "resolution",
        "start_date",
        "end_date",
        "download_url",
        "source"
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

    if not filename.lower().endswith(".nc"):

        print(f"Skipping non-NetCDF file: {url}")
        return False

    output_path = output_dir / filename

    if (
        output_path.exists()
        and output_path.stat().st_size > 0
    ):

        print(f"Already downloaded: {filename}")
        return True

    temp_path = output_path.with_suffix(
        ".nc.part"
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

                with open(temp_path, "wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):

                        if chunk:
                            file.write(chunk)

            if (
                not temp_path.exists()
                or temp_path.stat().st_size == 0
            ):

                raise IOError("Downloaded file is empty.")

            # Basic NetCDF file signature check.
            with open(temp_path, "rb") as file:
                signature = file.read(8)

            valid_signature = (
                signature.startswith(b"CDF")
                or signature.startswith(b"\x89HDF")
            )

            if not valid_signature:

                raise IOError(
                    "Downloaded content does not appear "
                    "to be a NetCDF/HDF file. "
                    "Check Earthdata authentication."
                )

            temp_path.replace(output_path)

            print(f"Saved: {output_path}")

            return True

        except Exception as exc:

            print(f"Download failed: {exc}")

            if temp_path.exists():
                temp_path.unlink()

            if attempt < retries:
                time.sleep(attempt * 4)

    return False


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "NASA Ocean Color MODIS chlorophyll-a downloader"
        )
    )

    parser.add_argument(
        "--sensor",
        choices=["aqua", "terra"],
        default="aqua"
    )

    parser.add_argument(
        "--period",
        choices=["DAY", "8D", "MO"],
        default="MO"
    )

    parser.add_argument(
        "--variable",
        choices=list(VARIABLES.keys()),
        default="chlor_a"
    )

    parser.add_argument(
        "--resolution",
        choices=["4km", "9km"],
        default="4km"
    )

    parser.add_argument(
        "--start-date",
        type=validate_date,
        default="2020-01-01"
    )

    parser.add_argument(
        "--end-date",
        type=validate_date,
        default="2020-12-31"
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download NetCDF files"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR
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

    session = create_session()

    urls = search_files(
        session=session,
        sensor=args.sensor,
        period=args.period,
        variable=args.variable,
        resolution=args.resolution,
        start_date=args.start_date,
        end_date=args.end_date
    )

    if not urls:

        print(
            "\nNo matching files found. "
            "Check the date range, period, and product availability."
        )

        return

    records = create_metadata_records(
        urls=urls,
        sensor=args.sensor,
        period=args.period,
        variable=args.variable,
        resolution=args.resolution
    )

    save_metadata(
        records=records,
        metadata_dir=args.metadata_dir,
        sensor=args.sensor,
        period=args.period,
        start_date=args.start_date,
        end_date=args.end_date
    )

    if not args.download:

        print(
            "\nSearch completed. Add --download "
            "to download the NetCDF files."
        )

        return

    print("\nStarting NetCDF downloads...")

    successful = 0
    failed = 0

    for record in records:

        result = download_file(
            session,
            record["download_url"],
            args.output_dir
        )

        if result:
            successful += 1
        else:
            failed += 1

    print("\nDOWNLOAD SUMMARY")
    print("----------------")
    print(f"Found:      {len(records)}")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print(f"Output:     {args.output_dir}")


if __name__ == "__main__":
    main()

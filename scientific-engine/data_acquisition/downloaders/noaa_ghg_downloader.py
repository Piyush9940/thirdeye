
"""
NOAA Greenhouse Gas Downloader
===============================

Source:
    NOAA Global Monitoring Laboratory (GML)

Global monthly mean datasets:
    CO2 - Carbon Dioxide (ppm)
    CH4 - Methane (ppb)
    N2O - Nitrous Oxide (ppb)
    SF6 - Sulfur Hexafluoride (ppt)

Downloads:
    1. Original NOAA text files.
    2. Clean CSV files.
    3. JSON metadata.
    4. Date-filtered monthly observations.

Important:
    These are globally averaged atmospheric measurements,
    not gridded spatial observations.

Install:
    pip install requests python-dotenv

Example:
    python noaa_ghg_downloader.py

    python noaa_ghg_downloader.py \
        --gases co2,ch4,n2o,sf6 \
        --start-date 2000-01-01 \
        --end-date 2025-12-31

Output:
    data/raw/noaa_ghg/
"""

import argparse
import csv
import json
import re
import time

from datetime import datetime
from pathlib import Path

import requests


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "data" / "raw" / "noaa_ghg"

BASE_URL = "https://gml.noaa.gov/webdata/ccgg/trends"

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"

# NOAA GML global monthly mean records.
DATASETS = {
    "co2": {
        "name": "Carbon Dioxide",
        "url": f"{BASE_URL}/co2/co2_mm_gl.txt",
        "unit": "ppm",
        "source": "NOAA GML Global CO2 Monthly Mean"
    },
    "ch4": {
        "name": "Methane",
        "url": f"{BASE_URL}/ch4/ch4_mm_gl.txt",
        "unit": "ppb",
        "source": "NOAA GML Global CH4 Monthly Mean"
    },
    "n2o": {
        "name": "Nitrous Oxide",
        "url": f"{BASE_URL}/n2o/n2o_mm_gl.txt",
        "unit": "ppb",
        "source": "NOAA GML Global N2O Monthly Mean"
    },
    "sf6": {
        "name": "Sulfur Hexafluoride",
        "url": f"{BASE_URL}/sf6/sf6_mm_gl.txt",
        "unit": "ppt",
        "source": "NOAA GML Global SF6 Monthly Mean"
    }
}


# =========================================================
# HTTP SESSION
# =========================================================

def create_session():

    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/plain,*/*"
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
# DOWNLOAD NOAA TEXT FILE
# =========================================================

def download_text_file(
    session,
    url,
    output_path,
    retries=3
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    for attempt in range(1, retries + 1):

        try:

            print(
                f"\nDownloading ({attempt}/{retries}): "
                f"{url}"
            )

            response = session.get(
                url,
                timeout=90
            )

            response.raise_for_status()

            content = response.text

            if not content.strip():
                raise ValueError("NOAA returned an empty file.")

            # Reject HTML error pages disguised as text.
            if "<html" in content[:1000].lower():
                raise ValueError(
                    "Received HTML instead of a data file."
                )

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(content)

            print(f"Saved: {output_path}")

            return content

        except Exception as exc:

            print(f"Download error: {exc}")

            if attempt < retries:
                time.sleep(attempt * 3)

    return None


# =========================================================
# PARSE NOAA TEXT DATA
# =========================================================

def parse_noaa_file(content):

    lines = content.splitlines()

    header = None
    records = []

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        # NOAA metadata and column descriptions are comments.
        if stripped.startswith("#"):

            possible_header = stripped.lstrip("#").strip()

            if (
                "year" in possible_header.lower()
                and "month" in possible_header.lower()
            ):

                header = re.split(
                    r"\s+",
                    possible_header
                )

            continue

        parts = stripped.split()

        if len(parts) < 3:
            continue

        try:

            year = int(parts[0])
            month = int(parts[1])

            if not 1 <= month <= 12:
                continue

            decimal_date = float(parts[2])

            values = []

            for value in parts[3:]:
                try:
                    values.append(float(value))
                except ValueError:
                    values.append(None)

            records.append({
                "year": year,
                "month": month,
                "decimal_date": decimal_date,
                "values": values
            })

        except (ValueError, IndexError):
            continue

    if not records:
        raise ValueError(
            "No valid monthly observations found in NOAA file."
        )

    return header, records


# =========================================================
# NORMALIZE RECORDS
# =========================================================

def normalize_records(
    records,
    header,
    gas_config,
    start_date=None,
    end_date=None
):

    normalized = []

    # NOAA monthly mean files typically contain:
    # year, month, decimal, average, average_unc,
    # trend, trend_unc.
    #
    # Keep any additional columns rather than discarding them.

    for record in records:

        year = record["year"]
        month = record["month"]

        observation_date = datetime(
            year,
            month,
            1
        )

        if start_date:
            if observation_date < datetime.strptime(
                start_date, "%Y-%m-%d"
            ):
                continue

        if end_date:
            if observation_date > datetime.strptime(
                end_date, "%Y-%m-%d"
            ):
                continue

        values = record["values"]

        row = {
            "date": observation_date.strftime("%Y-%m-%d"),
            "year": year,
            "month": month,
            "decimal_date": record["decimal_date"],
            "gas": gas_config["name"],
            "unit": gas_config["unit"]
        }

        # Map the common NOAA columns.
        column_names = [
            "average",
            "average_uncertainty",
            "trend",
            "trend_uncertainty"
        ]

        for index, column_name in enumerate(column_names):

            row[column_name] = (
                values[index]
                if len(values) > index
                else None
            )

        # Preserve extra numeric columns if present.
        for index, value in enumerate(values[4:], start=5):
            row[f"extra_value_{index}"] = value

        normalized.append(row)

    return normalized


# =========================================================
# SAVE CLEAN CSV
# =========================================================

def save_csv(records, output_path):

    if not records:
        print("No observations in selected date range.")
        return False

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    fieldnames = list(records[0].keys())

    with open(
        output_path,
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

    print(f"CSV saved: {output_path}")

    return True


# =========================================================
# SAVE METADATA
# =========================================================

def save_metadata(
    gas_code,
    config,
    records,
    raw_path,
    csv_path,
    metadata_dir,
    start_date,
    end_date
):

    metadata_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    metadata = {
        "dataset": config["source"],
        "gas_code": gas_code.upper(),
        "gas_name": config["name"],
        "unit": config["unit"],
        "source": "NOAA Global Monitoring Laboratory",
        "source_url": config["url"],
        "start_date": start_date,
        "end_date": end_date,
        "records_downloaded": len(records),
        "raw_file": str(raw_path),
        "csv_file": str(csv_path),
        "downloaded_at_utc": datetime.utcnow().isoformat(),
        "data_type": "Global monthly mean atmospheric concentration",
        "spatial_coverage": "Global marine surface network average",
        "citation": (
            "NOAA Global Monitoring Laboratory, "
            "Trends in Atmospheric Greenhouse Gases."
        )
    }

    metadata_path = metadata_dir / (
        f"{gas_code}_metadata.json"
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


# =========================================================
# PROCESS ONE GAS
# =========================================================

def process_gas(
    session,
    gas_code,
    config,
    start_date,
    end_date,
    output_dir
):

    print("\n" + "=" * 60)
    print(f"PROCESSING {config['name'].upper()}")
    print("=" * 60)

    gas_dir = output_dir / gas_code

    raw_dir = gas_dir / "raw"
    processed_dir = gas_dir / "processed"
    metadata_dir = gas_dir / "metadata"

    raw_path = raw_dir / f"{gas_code}_mm_global.txt"
    csv_path = processed_dir / f"{gas_code}_mm_global.csv"

    # -----------------------------------------------------
    # Download original file
    # -----------------------------------------------------

    content = download_text_file(
        session,
        config["url"],
        raw_path
    )

    if content is None:
        print(f"Could not download {gas_code.upper()}.")
        return False

    # -----------------------------------------------------
    # Parse
    # -----------------------------------------------------

    try:

        header, raw_records = parse_noaa_file(content)

        normalized = normalize_records(
            raw_records,
            header,
            config,
            start_date,
            end_date
        )

    except Exception as exc:

        print(f"Parsing error for {gas_code.upper()}: {exc}")
        return False

    if not normalized:

        print(
            f"No {gas_code.upper()} observations "
            "in the selected date range."
        )

        return False

    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------

    success = save_csv(
        normalized,
        csv_path
    )

    if not success:
        return False

    # -----------------------------------------------------
    # Save metadata
    # -----------------------------------------------------

    save_metadata(
        gas_code=gas_code,
        config=config,
        records=normalized,
        raw_path=raw_path,
        csv_path=csv_path,
        metadata_dir=metadata_dir,
        start_date=start_date,
        end_date=end_date
    )

    print("\nDataset summary")
    print("----------------")
    print(f"Gas: {config['name']}")
    print(f"Unit: {config['unit']}")
    print(f"Records: {len(normalized)}")
    print(f"First date: {normalized[0]['date']}")
    print(f"Last date: {normalized[-1]['date']}")

    return True


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download NOAA GML global greenhouse gas "
            "monthly mean records."
        )
    )

    parser.add_argument(
        "--gases",
        default="co2,ch4,n2o,sf6",
        help=(
            "Comma-separated gases: "
            "co2,ch4,n2o,sf6 or all"
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
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR
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

    if args.gases.strip().lower() == "all":
        selected_gases = list(DATASETS.keys())

    else:

        selected_gases = [
            gas.strip().lower()
            for gas in args.gases.split(",")
            if gas.strip()
        ]

    invalid_gases = [
        gas for gas in selected_gases
        if gas not in DATASETS
    ]

    if invalid_gases:
        parser.error(
            f"Unsupported gases: {invalid_gases}. "
            "Choose co2,ch4,n2o,sf6."
        )

    session = create_session()

    successful = []
    failed = []

    print("\nNOAA GREENHOUSE GAS DATA DOWNLOADER")
    print("-----------------------------------")
    print(f"Gases: {', '.join(selected_gases)}")
    print(f"Start date: {args.start_date or 'Full available record'}")
    print(f"End date: {args.end_date or 'Latest available record'}")
    print(f"Output: {args.output_dir}")

    for gas_code in selected_gases:

        result = process_gas(
            session=session,
            gas_code=gas_code,
            config=DATASETS[gas_code],
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir
        )

        if result:
            successful.append(gas_code)
        else:
            failed.append(gas_code)

    print("\n" + "=" * 60)
    print("FINAL DOWNLOAD SUMMARY")
    print("=" * 60)

    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    print(f"\nOutput directory: {args.output_dir}")

    if failed:
        print(
            "\nSome datasets could not be downloaded. "
            "Check the URL and NOAA service availability."
        )


if __name__ == "__main__":
    main()

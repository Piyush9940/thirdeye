
"""
NOAA SST Downloader
===================

Dataset:
    NOAA/NCEI 1/4 Degree Daily Optimum Interpolation SST (OISST)
    Version 2.1 - Final

Variables:
    sst  : Daily sea surface temperature (degree Celsius)
    anom : Daily sea surface temperature anomaly (degree Celsius)
    err  : Estimated SST error (degree Celsius)
    ice  : Sea ice concentration (fraction)

Resolution:
    0.25 degree, daily, global ocean

Source:
    NOAA ERDDAP - oisst_rclone

Install:
    pip install requests python-dotenv

Example:
    python scientific-engine/data_acquisition/sst_downloader.py
"""

import argparse
import calendar
import json
import logging
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

load_dotenv()

BASE_URL = (
    "https://upwell.pfeg.noaa.gov/"
    "erddap/griddap/oisst_rclone.nc"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "sst"
METADATA_DIR = PROJECT_ROOT / "data" / "raw" / "sst_metadata"

VARIABLES = ["sst", "anom", "err", "ice"]

RESOLUTION = 0.25

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"

REQUEST_TIMEOUT = 300
MAX_RETRIES = 3


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("SSTDownloader")


# ---------------------------------------------------------
# DATE UTILITIES
# ---------------------------------------------------------

def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}. Use YYYY-MM-DD."
        )


def month_ranges(start_date, end_date):
    """Generate inclusive monthly date ranges."""

    current = start_date

    while current <= end_date:
        last_day = calendar.monthrange(
            current.year,
            current.month,
        )[1]

        month_end = date(
            current.year,
            current.month,
            last_day,
        )

        chunk_end = min(month_end, end_date)

        yield current, chunk_end

        current = chunk_end + timedelta(days=1)


# ---------------------------------------------------------
# BOUNDING BOX
# ---------------------------------------------------------

def parse_bbox(value):
    """
    Expected format:
        west,south,east,north

    Example:
        68,6,98,38

    Longitudes are converted to 0-360 degrees because
    the NOAA dataset uses that longitude convention.
    """

    try:
        west, south, east, north = map(
            float,
            value.split(","),
        )
    except Exception:
        raise ValueError(
            "Invalid bbox. Use west,south,east,north."
        )

    if not (-90 <= south < north <= 90):
        raise ValueError("Invalid latitude boundaries.")

    if not (-180 <= west <= 180):
        raise ValueError("West longitude must be between -180 and 180.")

    if not (-180 <= east <= 180):
        raise ValueError("East longitude must be between -180 and 180.")

    if west > east:
        raise ValueError(
            "Bounding boxes crossing the international date line "
            "are not supported by this version."
        )

    west = west % 360
    east = east % 360

    return west, south, east, north


def snap_coordinate(value, origin):
    """Snap a requested boundary to the nearest grid coordinate."""

    return round(
        origin + round((value - origin) / RESOLUTION) * RESOLUTION,
        4,
    )


def prepare_bbox(bbox):
    west, south, east, north = bbox

    # Dataset grid:
    # Latitude:  -89.875 to 89.875
    # Longitude:   0.125 to 359.875

    west = snap_coordinate(west, 0.125)
    east = snap_coordinate(east, 0.125)

    south = snap_coordinate(south, -89.875)
    north = snap_coordinate(north, -89.875)

    return west, south, east, north


# ---------------------------------------------------------
# ERDDAP QUERY
# ---------------------------------------------------------

def build_query(
    start_date,
    end_date,
    bbox,
    variables,
):
    west, south, east, north = prepare_bbox(bbox)

    start_time = start_date.strftime(
        "%Y-%m-%dT12:00:00Z"
    )

    end_time = end_date.strftime(
        "%Y-%m-%dT12:00:00Z"
    )

    variable_queries = []

    for variable in variables:
        query = (
            f"{variable}"
            f"[({start_time}):1:({end_time})]"
            f"[(0)]"
            f"[({south}):0.25:({north})]"
            f"[({west}):0.25:({east})]"
        )

        variable_queries.append(query)

    return ",".join(variable_queries)


# ---------------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------------

def download_file(
    session,
    url,
    destination,
):
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if destination.exists() and destination.stat().st_size > 0:
        logger.info("Already exists: %s", destination.name)
        return True

    temporary_file = destination.with_suffix(
        destination.suffix + ".part"
    )

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            logger.info(
                "Downloading %s (attempt %s/%s)",
                destination.name,
                attempt,
                MAX_RETRIES,
            )

            with session.get(
                url,
                stream=True,
                timeout=REQUEST_TIMEOUT,
            ) as response:

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type",
                    "",
                ).lower()

                if "text/html" in content_type:
                    raise RuntimeError(
                        "ERDDAP returned HTML instead of NetCDF."
                    )

                with open(temporary_file, "wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

            if not temporary_file.exists():
                raise RuntimeError("Download produced no file.")

            if temporary_file.stat().st_size < 100:
                raise RuntimeError(
                    "Downloaded file is unexpectedly small."
                )

            temporary_file.replace(destination)

            logger.info(
                "Saved: %s (%.2f MB)",
                destination,
                destination.stat().st_size / (1024 * 1024),
            )

            return True

        except Exception as error:
            logger.warning(
                "Download failed: %s",
                error,
            )

            if temporary_file.exists():
                temporary_file.unlink()

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 3)

    logger.error(
        "Could not download %s",
        destination.name,
    )

    return False


# ---------------------------------------------------------
# METADATA
# ---------------------------------------------------------

def save_metadata(
    start_date,
    end_date,
    bbox,
    variables,
    downloaded_files,
):
    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = {
        "dataset": "NOAA OISST v2.1 Final",
        "dataset_id": "oisst_rclone",
        "source": BASE_URL,
        "institution": "NOAA/National Centers for Environmental Information",
        "resolution": "0.25 degree",
        "temporal_resolution": "Daily",
        "variables": variables,
        "units": {
            "sst": "degree_Celsius",
            "anom": "degree_Celsius",
            "err": "degree_Celsius",
            "ice": "fraction",
        },
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "bbox_west_south_east_north": list(bbox),
        "downloaded_files": downloaded_files,
        "downloaded_at_utc": datetime.utcnow().isoformat(),
    }

    metadata_file = (
        METADATA_DIR / "sst_download_metadata.json"
    )

    with open(
        metadata_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )

    logger.info("Metadata saved: %s", metadata_file)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Download NOAA OISST v2.1 daily SST data."
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=date(2020, 1, 1),
    )

    parser.add_argument(
        "--end-date",
        type=parse_date,
        default=date(2020, 1, 7),
    )

    parser.add_argument(
        "--bbox",
        default="68,6,98,38",
        help="west,south,east,north. Default: India region.",
    )

    parser.add_argument(
        "--variables",
        default="sst,anom,err,ice",
        help="Comma-separated variables: sst,anom,err,ice",
    )

    parser.add_argument(
        "--output-dir",
        default=str(RAW_DIR),
    )

    args = parser.parse_args()

    if args.start_date > args.end_date:
        parser.error("Start date must be before end date.")

    try:
        bbox = parse_bbox(args.bbox)
    except ValueError as error:
        parser.error(str(error))

    variables = [
        item.strip()
        for item in args.variables.split(",")
        if item.strip()
    ]

    invalid_variables = set(variables) - set(VARIABLES)

    if invalid_variables:
        parser.error(
            f"Unsupported variables: {sorted(invalid_variables)}"
        )

    output_dir = Path(args.output_dir)

    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
    })

    downloaded_files = []

    logger.info("=" * 65)
    logger.info("NOAA OISST v2.1 SST DATA DOWNLOADER")
    logger.info("=" * 65)

    logger.info("Start date: %s", args.start_date)
    logger.info("End date:   %s", args.end_date)
    logger.info("Bounding box: %s", bbox)
    logger.info("Variables: %s", variables)

    for chunk_start, chunk_end in month_ranges(
        args.start_date,
        args.end_date,
    ):

        query = build_query(
            chunk_start,
            chunk_end,
            bbox,
            variables,
        )

        encoded_query = quote(
            query,
            safe="[]():,.+-TZ",
        )

        download_url = f"{BASE_URL}?{encoded_query}"

        filename = (
            f"oisst_v2_1_"
            f"{chunk_start:%Y%m%d}_"
            f"{chunk_end:%Y%m%d}.nc"
        )

        destination = output_dir / filename

        success = download_file(
            session,
            download_url,
            destination,
        )

        if success:
            downloaded_files.append(
                str(destination)
            )

    save_metadata(
        args.start_date,
        args.end_date,
        bbox,
        variables,
        downloaded_files,
    )

    session.close()

    logger.info("=" * 65)
    logger.info(
        "Download complete: %s file(s)",
        len(downloaded_files),
    )
    logger.info("Output directory: %s", output_dir)
    logger.info("=" * 65)


if __name__ == "__main__":
    main()

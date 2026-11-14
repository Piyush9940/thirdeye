
"""
NASA MODIS MAIAC Aerosol Downloader
===================================

Project:
    Earth Systems Trend Detective

Dataset:
    MCD19A2.061

Product:
    MODIS Terra and Aqua MAIAC Land Aerosol Optical Depth

Resolution:
    1 km

Temporal resolution:
    Daily

Format:
    HDF

Provider:
    LPDAAC_ECS

Source:
    NASA Earthdata Common Metadata Repository (CMR)

Features:
    1. Search NASA CMR granules
    2. Filter by date
    3. Filter by bounding box
    4. Export JSON metadata
    5. Export CSV metadata
    6. Download HDF granules
    7. Earthdata authentication
    8. Retry failed downloads
    9. Skip previously downloaded files

Install:
    pip install requests python-dotenv

Optional .env:
    EARTHDATA_USERNAME=your_username
    EARTHDATA_PASSWORD=your_password

Run search:
    python scientific-engine/data_acquisition/downloaders/aerosol_downloader.py

Run download:
    python scientific-engine/data_acquisition/downloaders/aerosol_downloader.py --download
"""

import argparse
import csv
import json
import logging
import os
import re
import time

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "aerosol"

METADATA_DIR = (
    PROJECT_ROOT / "data" / "raw" / "aerosol_metadata"
)

CMR_URL = (
    "https://cmr.earthdata.nasa.gov/search/granules.json"
)

SHORT_NAME = "MCD19A2"
VERSION = "061"
PROVIDER = "LPDAAC_ECS"

PAGE_SIZE = 100
MAX_RETRIES = 3

REQUEST_TIMEOUT = 300

USER_AGENT = "Earth-Systems-Trend-Detective/1.0"


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("AerosolDownloader")


# =========================================================
# DATE VALIDATION
# =========================================================

def parse_date(value):

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except ValueError as error:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Use YYYY-MM-DD."
        ) from error


# =========================================================
# BOUNDING BOX
# =========================================================

def parse_bbox(value):

    if not value:
        return None

    try:
        west, south, east, north = map(
            float,
            value.split(","),
        )

    except (ValueError, AttributeError) as error:
        raise ValueError(
            "Invalid bounding box. "
            "Use west,south,east,north."
        ) from error

    if not (-180 <= west <= 180):
        raise ValueError("West longitude must be between -180 and 180.")

    if not (-180 <= east <= 180):
        raise ValueError("East longitude must be between -180 and 180.")

    if not (-90 <= south < north <= 90):
        raise ValueError("Invalid latitude boundaries.")

    if west > east:
        raise ValueError(
            "Bounding boxes crossing the date line "
            "are not supported."
        )

    return west, south, east, north


# =========================================================
# EARTHDATA SESSION
# =========================================================

def create_session():

    session = requests.Session()

    session.headers.update({
        "User-Agent": USER_AGENT,
    })

    token = os.getenv("EARTHDATA_TOKEN")

    username = (
        os.getenv("EARTHDATA_USERNAME")
        or os.getenv("EARTHDATA_USER")
    )

    password = (
        os.getenv("EARTHDATA_PASSWORD")
        or os.getenv("EARTHDATA_PASS")
    )

    if token:

        session.headers.update({
            "Authorization": f"Bearer {token}"
        })

        logger.info("Using Earthdata bearer token.")

    elif username and password:

        session.auth = (username, password)

        logger.info("Using Earthdata credentials from .env.")

    else:

        logger.info(
            "No credentials found in .env. "
            "Requests will use your configured .netrc "
            "credentials, if available."
        )

    return session


# =========================================================
# NASA CMR CLIENT
# =========================================================

class CMRClient:

    def __init__(self, session):

        self.session = session

    def search_granules(
        self,
        start_date,
        end_date,
        bbox=None,
        max_granules=5,
    ):

        logger.info("Searching NASA CMR...")
        logger.info("Dataset: %s", SHORT_NAME)
        logger.info("Version: %s", VERSION)
        logger.info("Provider: %s", PROVIDER)

        params = {
            "short_name": SHORT_NAME,
            "version": VERSION,
            "provider": PROVIDER,
            "temporal": (
                f"{start_date.isoformat()}T00:00:00Z,"
                f"{end_date.isoformat()}T23:59:59Z"
            ),
            "page_size": PAGE_SIZE,
            "page_num": 1,
            "sort_key[]": "start_date",
        }

        if bbox:

            params["bounding_box"] = ",".join(
                str(value) for value in bbox
            )

        granules = []

        while True:

            response = self.session.get(
                CMR_URL,
                params=params,
                timeout=90,
            )

            response.raise_for_status()

            result = response.json()

            entries = (
                result.get("feed", {}).get("entry", [])
            )

            if not entries:
                break

            granules.extend(entries)

            logger.info(
                "Retrieved %s granules.",
                len(granules),
            )

            if (
                max_granules
                and len(granules) >= max_granules
            ):

                granules = granules[:max_granules]
                break

            if len(entries) < PAGE_SIZE:
                break

            params["page_num"] += 1

        logger.info(
            "Total matching granules: %s",
            len(granules),
        )

        return granules


# =========================================================
# DOWNLOAD URL EXTRACTION
# =========================================================

def get_download_url(granule):

    links = granule.get("links", [])

    candidates = []

    for link in links:

        href = link.get("href", "")

        if not href.startswith("https://"):
            continue

        if link.get("inherited"):
            continue

        title = str(
            link.get("title", "")
        ).lower()

        rel = str(
            link.get("rel", "")
        ).lower()

        if any(
            word in title
            for word in [
                "browse",
                "metadata",
                "opendap",
                "documentation",
            ]
        ):
            continue

        if any(
            word in rel
            for word in [
                "browse",
                "metadata",
                "opendap",
            ]
        ):
            continue

        path = urlparse(href).path.lower()

        if path.endswith((".hdf", ".h5")):
            candidates.append((0, href))

        elif (
            "data#" in rel
            or "get data" in title
        ):
            candidates.append((1, href))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])

    return candidates[0][1]


# =========================================================
# FILENAME
# =========================================================

def safe_filename(url, granule):

    filename = Path(
        urlparse(url).path
    ).name

    if filename and filename.lower().endswith(
        (".hdf", ".h5")
    ):
        return filename

    title = granule.get(
        "title",
        "aerosol_granule",
    )

    title = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        title,
    )

    return f"{title}.hdf"


# =========================================================
# DOWNLOAD FUNCTION
# =========================================================

def download_granule(
    session,
    granule,
    output_dir,
):

    url = get_download_url(granule)

    if not url:

        logger.warning(
            "No downloadable HDF link found: %s",
            granule.get("title"),
        )

        return None

    filename = safe_filename(
        url,
        granule,
    )

    destination = output_dir / filename

    if (
        destination.exists()
        and destination.stat().st_size > 0
    ):

        logger.info(
            "Already downloaded: %s",
            filename,
        )

        return str(destination)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = destination.with_name(
        destination.name + ".part"
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            logger.info(
                "Downloading %s (%s/%s)",
                filename,
                attempt,
                MAX_RETRIES,
            )

            with session.get(
                url,
                stream=True,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            ) as response:

                response.raise_for_status()

                content_type = response.headers.get(
                    "Content-Type",
                    "",
                ).lower()

                if "text/html" in content_type:

                    raise RuntimeError(
                        "Server returned HTML instead of HDF. "
                        "Check Earthdata authentication."
                    )

                with open(
                    temporary_file,
                    "wb",
                ) as file:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):

                        if chunk:
                            file.write(chunk)

            if (
                not temporary_file.exists()
                or temporary_file.stat().st_size < 100
            ):

                raise RuntimeError(
                    "Downloaded file is empty or too small."
                )

            temporary_file.replace(destination)

            logger.info(
                "Download successful: %s (%.2f MB)",
                filename,
                destination.stat().st_size / (1024 * 1024),
            )

            return str(destination)

        except Exception as error:

            logger.warning(
                "Download attempt %s failed: %s",
                attempt,
                error,
            )

            if temporary_file.exists():
                temporary_file.unlink()

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 5)

    logger.error(
        "Download failed permanently: %s",
        filename,
    )

    return None


# =========================================================
# METADATA EXPORT
# =========================================================

def save_metadata(
    granules,
    start_date,
    end_date,
    bbox,
    downloaded_files=None,
):

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = {
        "dataset": "MODIS MAIAC Aerosol Optical Depth",
        "short_name": SHORT_NAME,
        "version": VERSION,
        "provider": PROVIDER,
        "satellites": [
            "Terra",
            "Aqua",
        ],
        "resolution": "1 km",
        "temporal_resolution": "Daily",
        "format": "HDF",
        "measurement": "Aerosol Optical Depth",
        "source": "NASA Earthdata CMR",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "bounding_box": (
            list(bbox) if bbox else None
        ),
        "granule_count": len(granules),
        "downloaded_files": downloaded_files or [],
        "retrieved_at_utc": datetime.utcnow().isoformat(),
        "granules": granules,
    }

    json_path = (
        METADATA_DIR / "aerosol_granules.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    csv_path = (
        METADATA_DIR / "aerosol_granules.csv"
    )

    fields = [
        "title",
        "id",
        "time_start",
        "time_end",
        "updated",
        "download_url",
    ]

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()

        for granule in granules:

            writer.writerow({
                "title": granule.get("title"),
                "id": granule.get("id"),
                "time_start": granule.get("time_start"),
                "time_end": granule.get("time_end"),
                "updated": granule.get("updated"),
                "download_url": get_download_url(granule),
            })

    logger.info("JSON saved: %s", json_path)
    logger.info("CSV saved: %s", csv_path)


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description="NASA MODIS MAIAC aerosol downloader."
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        default=parse_date("2020-01-01"),
    )

    parser.add_argument(
        "--end-date",
        type=parse_date,
        default=parse_date("2020-01-07"),
    )

    parser.add_argument(
        "--bbox",
        default="68,6,98,38",
        help="west,south,east,north",
    )

    parser.add_argument(
        "--max-granules",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the matching HDF files.",
    )

    parser.add_argument(
        "--output-dir",
        default=str(RAW_DIR),
    )

    args = parser.parse_args()

    if args.start_date > args.end_date:
        parser.error(
            "Start date cannot be after end date."
        )

    if args.max_granules < 1:
        parser.error(
            "--max-granules must be at least 1."
        )

    try:
        bbox = parse_bbox(args.bbox)

    except ValueError as error:
        parser.error(str(error))

    logger.info("=" * 65)
    logger.info("NASA MODIS MAIAC AEROSOL DOWNLOADER")
    logger.info("=" * 65)

    logger.info("Date range: %s to %s",
                args.start_date, args.end_date)

    logger.info("Bounding box: %s", bbox)

    session = create_session()

    try:

        client = CMRClient(session)

        granules = client.search_granules(
            start_date=args.start_date,
            end_date=args.end_date,
            bbox=bbox,
            max_granules=args.max_granules,
        )

        downloaded_files = []

        if not granules:

            logger.warning(
                "No matching granules found."
            )

            save_metadata(
                [],
                args.start_date,
                args.end_date,
                bbox,
            )

            return

        logger.info("Matching granules:")

        for index, granule in enumerate(
            granules,
            start=1,
        ):

            logger.info(
                "%s. %s",
                index,
                granule.get("title"),
            )

        if args.download:

            output_dir = Path(
                args.output_dir
            )

            for granule in granules:

                result = download_granule(
                    session,
                    granule,
                    output_dir,
                )

                if result:
                    downloaded_files.append(result)

        else:

            logger.info(
                "Search completed. "
                "Use --download to download HDF files."
            )

        save_metadata(
            granules,
            args.start_date,
            args.end_date,
            bbox,
            downloaded_files,
        )

        logger.info("=" * 65)
        logger.info(
            "Granules found: %s",
            len(granules),
        )
        logger.info(
            "Files downloaded: %s",
            len(downloaded_files),
        )
        logger.info(
            "Output directory: %s",
            args.output_dir,
        )
        logger.info("=" * 65)

    except requests.RequestException as error:

        logger.exception(
            "NASA CMR or download request failed: %s",
            error,
        )

        raise

    finally:

        session.close()


if __name__ == "__main__":
    main()

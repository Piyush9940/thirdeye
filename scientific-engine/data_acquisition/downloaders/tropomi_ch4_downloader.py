
"""
TROPOMI CH4 Downloader
======================

Project:
    Earth Systems Trend Detective

Satellite:
    Sentinel-5 Precursor (Sentinel-5P)

Instrument:
    TROPOMI

Product:
    L2__CH4___ - Level-2 Methane

Main measurement:
    XCH4 - Dry-air column-averaged methane mole fraction

Typical units:
    ppb (parts per billion)

Data format:
    NetCDF (.nc)

Access:
    Copernicus Data Space Ecosystem OData API

Install:
    pip install requests python-dotenv

Environment variables in project .env:
    CDSE_USERNAME=your_copernicus_username
    CDSE_PASSWORD=your_copernicus_password

Alternative accepted names:
    COPERNICUS_USERNAME
    COPERNICUS_PASSWORD

Example:
    python scientific-engine/data_acquisition/tropomi_ch4_downloader.py

India:
    python scientific-engine/data_acquisition/tropomi_ch4_downloader.py ^
        --start-date 2020-01-01 ^
        --end-date 2020-01-07 ^
        --bbox "68,6,98,38" ^
        --max-products 5

Search only:
    Add --search-only

Download:
    Add --download
"""

import argparse
import csv
import json
import logging
import os
import re
import time

from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "tropomi_ch4"

METADATA_DIR = (
    PROJECT_ROOT / "data" / "raw" / "tropomi_ch4_metadata"
)

CATALOGUE_URL = (
    "https://catalogue.dataspace.copernicus.eu/"
    "odata/v1/Products"
)

DOWNLOAD_URL = (
    "https://download.dataspace.copernicus.eu/"
    "odata/v1/Products"
)

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

COLLECTION_NAME = "SENTINEL-5P"

PRODUCT_TYPE = "L2__CH4___"

CLIENT_ID = "cdse-public"

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

logger = logging.getLogger("TROPOMI_CH4")


# =========================================================
# DATE UTILITIES
# =========================================================

def parse_date(value):

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except ValueError:

        raise argparse.ArgumentTypeError(
            f"Invalid date: {value}. Expected YYYY-MM-DD."
        )


def iso_datetime(value):

    return value.strftime("%Y-%m-%dT00:00:00.000Z")


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

    except Exception:

        raise ValueError(
            "Invalid bbox. Use west,south,east,north."
        )

    if not (-180 <= west <= 180):
        raise ValueError("Invalid west longitude.")

    if not (-180 <= east <= 180):
        raise ValueError("Invalid east longitude.")

    if not (-90 <= south < north <= 90):
        raise ValueError("Invalid latitude boundaries.")

    if west > east:
        raise ValueError(
            "Bounding boxes crossing the date line "
            "are not supported."
        )

    return west, south, east, north


def footprint_intersects_bbox(footprint, bbox):

    """
    Check whether a product footprint intersects a bbox.

    Uses Shapely if installed.

    If Shapely is unavailable or the footprint cannot
    be interpreted, the product is retained rather than
    incorrectly discarded.
    """

    if not bbox or not footprint:
        return True

    try:

        from shapely.geometry import shape, box

        west, south, east, north = bbox

        product_geometry = shape(footprint)

        requested_geometry = box(
            west,
            south,
            east,
            north,
        )

        return product_geometry.intersects(
            requested_geometry
        )

    except ImportError:

        logger.warning(
            "Shapely is not installed. "
            "Skipping local footprint filtering."
        )

        return True

    except Exception as error:

        logger.warning(
            "Could not evaluate product footprint: %s",
            error,
        )

        return True


# =========================================================
# AUTHENTICATION
# =========================================================

class CDSEAuthenticator:

    def __init__(self):

        self.username = (
            os.getenv("CDSE_USERNAME")
            or os.getenv("COPERNICUS_USERNAME")
            or os.getenv("CDSE_USER")
        )

        self.password = (
            os.getenv("CDSE_PASSWORD")
            or os.getenv("COPERNICUS_PASSWORD")
            or os.getenv("CDSE_PASS")
        )

        self.access_token = None

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT,
        })

    def authenticate(self):

        if not self.username or not self.password:

            raise RuntimeError(
                "Copernicus credentials not found.\n"
                "Add CDSE_USERNAME and CDSE_PASSWORD "
                "to your project .env file."
            )

        logger.info(
            "Authenticating with Copernicus Data Space..."
        )

        payload = {
            "client_id": CLIENT_ID,
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }

        response = self.session.post(
            TOKEN_URL,
            data=payload,
            timeout=60,
        )

        response.raise_for_status()

        token_data = response.json()

        self.access_token = token_data.get(
            "access_token"
        )

        if not self.access_token:

            raise RuntimeError(
                "Authentication response did not contain "
                "an access token."
            )

        logger.info(
            "Copernicus authentication successful."
        )

        return self.access_token

    def get_headers(self):

        if not self.access_token:
            self.authenticate()

        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            )
        }


# =========================================================
# CATALOGUE CLIENT
# =========================================================

class TROPOMICH4Client:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        })

        self.auth = CDSEAuthenticator()

    def build_filter(
        self,
        start_date,
        end_date,
    ):

        """
        Build OData catalogue filter.

        Product type:
            L2__CH4___

        Collection:
            SENTINEL-5P
        """

        start_time = iso_datetime(start_date)

        # OData date end is exclusive.
        end_exclusive = (
            end_date.fromordinal(end_date.toordinal() + 1)
        )

        end_time = iso_datetime(end_exclusive)

        filters = [
            f"Collection/Name eq '{COLLECTION_NAME}'",

            (
                "Attributes/OData.CSC.StringAttribute/"
                "any(att:att/Name eq 'productType' "
                f"and att/OData.CSC.StringAttribute/Value "
                f"eq '{PRODUCT_TYPE}')"
            ),

            (
                "ContentDate/Start ge "
                f"{start_time}"
            ),

            (
                "ContentDate/Start lt "
                f"{end_time}"
            ),
        ]

        return " and ".join(filters)

    def search_products(
        self,
        start_date,
        end_date,
        bbox=None,
        max_products=10,
    ):

        logger.info(
            "Searching Sentinel-5P TROPOMI CH4 products..."
        )

        logger.info(
            "Date range: %s to %s",
            start_date,
            end_date,
        )

        filter_query = self.build_filter(
            start_date,
            end_date,
        )

        params = {
            "$filter": filter_query,
            "$orderby": "ContentDate/Start asc",
            "$top": PAGE_SIZE,
            "$select": (
                "Id,Name,ContentDate,ContentLength,"
                "GeoFootprint,OriginDate"
            ),
        }

        products = []

        next_url = CATALOGUE_URL

        while next_url:

            try:

                if next_url == CATALOGUE_URL:

                    response = self.session.get(
                        next_url,
                        params=params,
                        timeout=90,
                    )

                else:

                    response = self.session.get(
                        next_url,
                        timeout=90,
                    )

                response.raise_for_status()

                result = response.json()

                page_products = result.get(
                    "value",
                    [],
                )

                if not page_products:
                    break

                for product in page_products:

                    if bbox:

                        footprint = product.get(
                            "GeoFootprint"
                        )

                        if not footprint_intersects_bbox(
                            footprint,
                            bbox,
                        ):
                            continue

                    products.append(product)

                    if (
                        max_products
                        and len(products) >= max_products
                    ):
                        break

                logger.info(
                    "Products collected: %s",
                    len(products),
                )

                if (
                    max_products
                    and len(products) >= max_products
                ):
                    break

                next_url = result.get("@odata.nextLink")

            except requests.RequestException as error:

                logger.error(
                    "Catalogue search failed: %s",
                    error,
                )

                raise

        logger.info(
            "Total matching products: %s",
            len(products),
        )

        return products


# =========================================================
# METADATA
# =========================================================

def save_metadata(products):

    METADATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        METADATA_DIR / "tropomi_ch4_products.json"
    )

    metadata = {
        "dataset": "Sentinel-5P TROPOMI Methane",
        "collection": COLLECTION_NAME,
        "product_type": PRODUCT_TYPE,
        "instrument": "TROPOMI",
        "variable": "XCH4",
        "measurement": (
            "Dry-air column-averaged methane mole fraction"
        ),
        "typical_units": "ppb",
        "source": (
            "Copernicus Data Space Ecosystem"
        ),
        "retrieved_at_utc": datetime.utcnow().isoformat(),
        "number_of_products": len(products),
        "products": products,
    }

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4,
        )

    csv_file = (
        METADATA_DIR / "tropomi_ch4_products.csv"
    )

    fields = [
        "Id",
        "Name",
        "ContentLength",
        "ContentDate",
    ]

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore",
        )

        writer.writeheader()

        for product in products:

            writer.writerow({
                "Id": product.get("Id"),
                "Name": product.get("Name"),
                "ContentLength": product.get(
                    "ContentLength"
                ),
                "ContentDate": product.get(
                    "ContentDate"
                ),
            })

    logger.info(
        "JSON metadata saved: %s",
        output_file,
    )

    logger.info(
        "CSV metadata saved: %s",
        csv_file,
    )


# =========================================================
# DOWNLOAD CLIENT
# =========================================================

def download_product(
    client,
    product,
    output_dir,
):

    product_id = product.get("Id")

    product_name = product.get("Name")

    if not product_id or not product_name:

        logger.warning(
            "Skipping product with missing ID or name."
        )

        return False

    # Sentinel-5P products are provided as NetCDF files.
    if not product_name.lower().endswith(".nc"):

        logger.warning(
            "Unexpected product extension: %s",
            product_name,
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_name = Path(product_name).name

    destination = output_dir / safe_name

    if (
        destination.exists()
        and destination.stat().st_size > 0
    ):

        logger.info(
            "Already downloaded: %s",
            safe_name,
        )

        return True

    url = (
        f"{DOWNLOAD_URL}({product_id})/$value"
    )

    temporary_file = destination.with_suffix(
        destination.suffix + ".part"
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            logger.info(
                "Downloading %s (attempt %s/%s)",
                safe_name,
                attempt,
                MAX_RETRIES,
            )

            headers = client.auth.get_headers()

            with client.auth.session.get(
                url,
                headers=headers,
                stream=True,
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT,
            ) as response:

                response.raise_for_status()

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
                "Downloaded: %s (%.2f MB)",
                destination,
                destination.stat().st_size / (
                    1024 * 1024
                ),
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
                time.sleep(attempt * 5)

    logger.error(
        "Failed to download: %s",
        safe_name,
    )

    return False


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download Sentinel-5P TROPOMI "
            "Level-2 methane products."
        )
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
        help=(
            "west,south,east,north. "
            "Default is India region."
        ),
    )

    parser.add_argument(
        "--max-products",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Search and save metadata without downloading.",
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download matching NetCDF products.",
    )

    parser.add_argument(
        "--output-dir",
        default=str(RAW_DIR),
    )

    args = parser.parse_args()

    if args.start_date > args.end_date:

        parser.error(
            "Start date must be before or equal to end date."
        )

    if args.max_products < 1:

        parser.error(
            "--max-products must be at least 1."
        )

    try:

        bbox = parse_bbox(args.bbox)

    except ValueError as error:

        parser.error(str(error))

    logger.info("=" * 65)
    logger.info("TROPOMI CH4 DOWNLOADER")
    logger.info("=" * 65)

    logger.info("Start date: %s", args.start_date)
    logger.info("End date: %s", args.end_date)
    logger.info("Bounding box: %s", bbox)
    logger.info("Maximum products: %s", args.max_products)

    client = TROPOMICH4Client()

    products = client.search_products(
        start_date=args.start_date,
        end_date=args.end_date,
        bbox=bbox,
        max_products=args.max_products,
    )

    save_metadata(products)

    if not products:

        logger.warning(
            "No matching TROPOMI CH4 products found."
        )

        return

    logger.info("Matching products:")

    for index, product in enumerate(
        products,
        start=1,
    ):

        logger.info(
            "%s. %s",
            index,
            product.get("Name"),
        )

    if args.search_only:

        logger.info(
            "Search-only mode. No files downloaded."
        )

        return

    if not args.download:

        logger.info(
            "Search completed. "
            "Use --download to download the products."
        )

        return

    # Authenticate only when actual downloads are requested.
    client.auth.authenticate()

    output_dir = Path(args.output_dir)

    successful = 0

    for product in products:

        if download_product(
            client,
            product,
            output_dir,
        ):

            successful += 1

    logger.info("=" * 65)
    logger.info(
        "Download finished: %s/%s successful",
        successful,
        len(products),
    )
    logger.info("Output: %s", output_dir)
    logger.info("=" * 65)


if __name__ == "__main__":
    main()

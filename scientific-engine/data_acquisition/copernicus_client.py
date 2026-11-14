
"""
Copernicus Data Space Client
Project: Earth Systems Trend Detective

Features:
    1. Search Sentinel-5P products.
    2. Filter by product type and date.
    3. Optionally filter by bounding box.
    4. Retrieve product metadata.
    5. Download products using OAuth2 authentication.
    6. Save search results as JSON.
    7. Support pagination.

Dependencies:
    requests
    python-dotenv

Authentication:
    Uses CopernicusAuth from copernicus_auth.py
"""

import os
import re
import sys
import json
import logging
import argparse

from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import requests

# Import authentication module
try:
    from copernicus_auth import CopernicusAuth
except ImportError:
    from scientific_engine_placeholder import CopernicusAuth


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

CATALOGUE_URL = (
    "https://catalogue.dataspace.copernicus.eu/odata/v1"
)

DOWNLOAD_URL = (
    "https://download.dataspace.copernicus.eu/odata/v1"
)

DEFAULT_COLLECTION = "SENTINEL-5P"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DOWNLOAD_DIR = (
    PROJECT_ROOT / "data" / "raw" / "copernicus"
)

DEFAULT_METADATA_DIR = (
    PROJECT_ROOT / "data" / "raw" / "copernicus_metadata"
)

TIMEOUT = 120
CHUNK_SIZE = 1024 * 1024

# Sentinel-5P product types relevant to this project
SUPPORTED_PRODUCT_TYPES = {
    "CH4": "L2__CH4___",
    "NO2": "L2__NO2___",
    "CO": "L2__CO____",
    "SO2": "L2__SO2___",
    "O3": "L2__O3____",
}


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("CopernicusClient")


# ---------------------------------------------------------
# CLIENT CLASS
# ---------------------------------------------------------

class CopernicusClient:
    """
    Client for searching and downloading Copernicus products.
    """

    def __init__(
        self,
        download_dir: Optional[str] = None,
        metadata_dir: Optional[str] = None
    ):

        self.download_dir = Path(
            download_dir or DEFAULT_DOWNLOAD_DIR
        )

        self.metadata_dir = Path(
            metadata_dir or DEFAULT_METADATA_DIR
        )

        self.download_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.metadata_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.auth = CopernicusAuth()

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Earth-Systems-Trend-Detective/1.0"
        })

        logger.info("Copernicus client initialized.")

    # -----------------------------------------------------
    # AUTHENTICATION
    # -----------------------------------------------------

    def _get_auth_headers(self):
        """
        Get an access token from CopernicusAuth.
        """

        token = self.auth.get_token()

        return {
            "Authorization": f"Bearer {token}"
        }

    def _authenticated_request(
        self,
        method,
        url,
        retry=True,
        **kwargs
    ):
        """
        Make an authenticated request.

        If the token expires, authenticate again and retry once.
        """

        headers = kwargs.pop("headers", {})

        auth_headers = self._get_auth_headers()
        auth_headers.update(headers)

        response = self.session.request(
            method=method,
            url=url,
            headers=auth_headers,
            timeout=TIMEOUT,
            **kwargs
        )

        if response.status_code == 401 and retry:

            logger.warning(
                "Access token may have expired. "
                "Authenticating again..."
            )

            self.auth.access_token = None
            self.auth.authenticate()

            return self._authenticated_request(
                method,
                url,
                retry=False,
                headers=headers,
                **kwargs
            )

        response.raise_for_status()

        return response

    # -----------------------------------------------------
    # DATE VALIDATION
    # -----------------------------------------------------

    @staticmethod
    def _validate_dates(start_date, end_date):
        """
        Validate YYYY-MM-DD date inputs.
        """

        start = datetime.strptime(
            start_date, "%Y-%m-%d"
        )

        end = datetime.strptime(
            end_date, "%Y-%m-%d"
        )

        if start > end:
            raise ValueError(
                "start_date cannot be later than end_date."
            )

        return start, end

    # -----------------------------------------------------
    # FILTER BUILDER
    # -----------------------------------------------------

    @staticmethod
    def _escape_odata_string(value):
        """
        Escape single quotes in OData string literals.
        """

        return str(value).replace("'", "''")

    def _build_filter(
        self,
        start_date,
        end_date,
        collection=DEFAULT_COLLECTION,
        product_type=None,
        bounding_box=None
    ):
        """
        Construct an OData filter.

        bounding_box format:
            west,south,east,north

        Example:
            68,6,98,38
        """

        self._validate_dates(start_date, end_date)

        start_time = (
            f"{start_date}T00:00:00.000Z"
        )

        end_time = (
            f"{end_date}T23:59:59.999Z"
        )

        collection = self._escape_odata_string(
            collection
        )

        filters = [
            f"Collection/Name eq '{collection}'",
            f"ContentDate/Start ge {start_time}",
            f"ContentDate/Start le {end_time}"
        ]

        if product_type:

            product_type = self._escape_odata_string(
                product_type
            )

            filters.append(
                "Attributes/OData.CSC.StringAttribute/"
                "any(att:att/Name eq 'productType' "
                "and att/OData.CSC.StringAttribute/Value "
                f"eq '{product_type}')"
            )

        if bounding_box:

            try:
                west, south, east, north = [
                    float(value.strip())
                    for value in bounding_box.split(",")
                ]

            except ValueError as error:
                raise ValueError(
                    "Bounding box must contain four numbers: "
                    "west,south,east,north"
                ) from error

            if not (
                -180 <= west <= 180
                and -180 <= east <= 180
                and -90 <= south <= 90
                and -90 <= north <= 90
                and south < north
                and west < east
            ):
                raise ValueError(
                    "Invalid bounding box coordinates."
                )

            polygon = (
                f"POLYGON(({west} {south},"
                f"{east} {south},"
                f"{east} {north},"
                f"{west} {north},"
                f"{west} {south}))"
            )

            filters.append(
                "OData.CSC.Intersects("
                "area=geography'SRID=4326;"
                f"{polygon}')"
            )

        return " and ".join(filters)

    # -----------------------------------------------------
    # PRODUCT SEARCH
    # -----------------------------------------------------

    def search_products(
        self,
        start_date,
        end_date,
        product_type=None,
        collection=DEFAULT_COLLECTION,
        bounding_box=None,
        max_products=100,
        page_size=100
    ):
        """
        Search the Copernicus catalogue.

        Returns:
            List of product metadata dictionaries.
        """

        logger.info("Starting Copernicus product search.")

        if max_products < 1 or page_size < 1:
            raise ValueError(
                "max_products and page_size must be positive."
            )

        if product_type and product_type not in (
            SUPPORTED_PRODUCT_TYPES.values()
        ):
            logger.warning(
                "Product type %s is not in the predefined "
                "Sentinel-5P product list.",
                product_type
            )

        odata_filter = self._build_filter(
            start_date=start_date,
            end_date=end_date,
            collection=collection,
            product_type=product_type,
            bounding_box=bounding_box
        )

        params = {
            "$filter": odata_filter,
            "$select": (
                "Id,Name,ContentType,ContentLength,"
                "ContentDate,PublicationDate,"
                "Online,S3Path,GeoFootprint"
            ),
            "$orderby": "ContentDate/Start asc",
            "$top": min(page_size, max_products)
        }

        products = []
        next_url = f"{CATALOGUE_URL}/Products"

        while next_url and len(products) < max_products:

            logger.info(
                "Fetching catalogue page. Products collected: %s",
                len(products)
            )

            if next_url == f"{CATALOGUE_URL}/Products":
                response = self.session.get(
                    next_url,
                    params=params,
                    timeout=TIMEOUT
                )
            else:
                # OData nextLink already includes its query parameters.
                response = self.session.get(
                    next_url,
                    timeout=TIMEOUT
                )

            response.raise_for_status()

            data = response.json()

            page_products = data.get("value", [])

            remaining = max_products - len(products)

            products.extend(page_products[:remaining])

            next_url = data.get("@odata.nextLink")

        logger.info(
            "Search completed. Found %s products.",
            len(products)
        )

        return products

    # -----------------------------------------------------
    # SEARCH BY ENVIRONMENTAL VARIABLE
    # -----------------------------------------------------

    def search_by_variable(
        self,
        variable,
        start_date,
        end_date,
        bounding_box=None,
        max_products=100
    ):
        """
        Search using a project variable name.

        Supported variables:
            CH4, NO2, CO, SO2, O3
        """

        variable = variable.upper()

        if variable not in SUPPORTED_PRODUCT_TYPES:
            raise ValueError(
                f"Unsupported variable: {variable}. "
                f"Choose from {list(SUPPORTED_PRODUCT_TYPES)}"
            )

        product_type = SUPPORTED_PRODUCT_TYPES[variable]

        logger.info(
            "Searching for %s products: %s",
            variable,
            product_type
        )

        return self.search_products(
            start_date=start_date,
            end_date=end_date,
            product_type=product_type,
            bounding_box=bounding_box,
            max_products=max_products
        )

    # -----------------------------------------------------
    # SAVE SEARCH METADATA
    # -----------------------------------------------------

    def save_metadata(
        self,
        products,
        filename="copernicus_search_results.json"
    ):
        """
        Save product search results as JSON.
        """

        output_path = self.metadata_dir / filename

        metadata = {
            "source": "Copernicus Data Space Ecosystem",
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "total_products": len(products),
            "products": products
        }

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False
            )

        logger.info(
            "Metadata saved: %s",
            output_path
        )

        return output_path

    # -----------------------------------------------------
    # GET PRODUCT DETAILS
    # -----------------------------------------------------

    def get_product_details(self, product_id):
        """
        Retrieve metadata for one product.
        """

        url = (
            f"{CATALOGUE_URL}/Products"
            f"({product_id})"
        )

        response = self.session.get(
            url,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        return response.json()

    # -----------------------------------------------------
    # SAFE FILENAME
    # -----------------------------------------------------

    @staticmethod
    def _safe_filename(filename):
        """
        Remove characters that are unsafe in Windows filenames.
        """

        filename = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            filename
        )

        return filename.strip(" .")

    # -----------------------------------------------------
    # DOWNLOAD PRODUCT
    # -----------------------------------------------------

    def download_product(
        self,
        product_id,
        product_name=None,
        output_dir=None,
        overwrite=False
    ):
        """
        Download a Copernicus product using its UUID.

        Sentinel-5P products are generally served as .nc files.
        The catalogue product name is used as the filename.
        """

        output_dir = Path(
            output_dir or self.download_dir
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        if not product_name:
            details = self.get_product_details(product_id)
            product_name = details.get("Name")

        if not product_name:
            product_name = f"{product_id}.nc"

        filename = self._safe_filename(product_name)

        if not Path(filename).suffix:
            filename += ".nc"

        output_path = output_dir / filename

        if output_path.exists() and not overwrite:
            logger.info(
                "File already exists. Skipping: %s",
                output_path
            )

            return output_path

        download_url = (
            f"{DOWNLOAD_URL}/Products"
            f"({product_id})/$value"
        )

        logger.info(
            "Downloading product: %s",
            filename
        )

        response = self._authenticated_request(
            "GET",
            download_url,
            stream=True,
            allow_redirects=True
        )

        temporary_path = output_path.with_name(
            output_path.name + ".part"
        )

        try:
            with open(temporary_path, "wb") as file:

                for chunk in response.iter_content(
                    chunk_size=CHUNK_SIZE
                ):

                    if chunk:
                        file.write(chunk)

            if temporary_path.stat().st_size == 0:
                raise RuntimeError(
                    "Downloaded file is empty."
                )

            os.replace(
                temporary_path,
                output_path
            )

        except Exception:
            if temporary_path.exists():
                temporary_path.unlink()
            raise

        finally:
            response.close()

        logger.info(
            "Download completed: %s",
            output_path
        )

        return output_path

    # -----------------------------------------------------
    # DOWNLOAD MULTIPLE PRODUCTS
    # -----------------------------------------------------

    def download_products(
        self,
        products,
        output_dir=None,
        limit=None
    ):
        """
        Download multiple products returned by search_products().
        """

        if limit is not None:
            products = products[:limit]

        downloaded_files = []
        failed_downloads = []

        for index, product in enumerate(products, start=1):

            product_id = product.get("Id")
            product_name = product.get("Name")

            if not product_id:
                logger.warning(
                    "Skipping product without an ID."
                )
                continue

            logger.info(
                "Processing product %s/%s",
                index,
                len(products)
            )

            try:
                path = self.download_product(
                    product_id=product_id,
                    product_name=product_name,
                    output_dir=output_dir
                )

                downloaded_files.append(str(path))

            except requests.exceptions.RequestException as error:
                logger.error(
                    "Download failed for %s: %s",
                    product_name,
                    error
                )

                failed_downloads.append({
                    "id": product_id,
                    "name": product_name,
                    "error": str(error)
                })

            except Exception as error:
                logger.error(
                    "Unexpected error for %s: %s",
                    product_name,
                    error
                )

                failed_downloads.append({
                    "id": product_id,
                    "name": product_name,
                    "error": str(error)
                })

        logger.info(
            "Downloads completed. Successful: %s | Failed: %s",
            len(downloaded_files),
            len(failed_downloads)
        )

        return {
            "downloaded": downloaded_files,
            "failed": failed_downloads
        }


# ---------------------------------------------------------
# COMMAND LINE INTERFACE
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Copernicus Data Space client for "
            "Earth Systems Trend Detective."
        )
    )

    parser.add_argument(
        "--variable",
        choices=list(SUPPORTED_PRODUCT_TYPES.keys()),
        help="Environmental variable: CH4, NO2, CO, SO2 or O3."
    )

    parser.add_argument(
        "--product-type",
        help="Explicit Sentinel-5P product type."
    )

    parser.add_argument(
        "--start-date",
        default="2019-01-01",
        help="Start date in YYYY-MM-DD format."
    )

    parser.add_argument(
        "--end-date",
        default="2024-12-31",
        help="End date in YYYY-MM-DD format."
    )

    parser.add_argument(
        "--bbox",
        help="Bounding box: west,south,east,north."
    )

    parser.add_argument(
        "--max-products",
        type=int,
        default=10,
        help="Maximum catalogue products to retrieve."
    )

    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the products returned by the search."
    )

    args = parser.parse_args()

    if not args.variable and not args.product_type:
        parser.error(
            "Provide either --variable or --product-type."
        )

    try:

        client = CopernicusClient()

        if args.variable:

            products = client.search_by_variable(
                variable=args.variable,
                start_date=args.start_date,
                end_date=args.end_date,
                bounding_box=args.bbox,
                max_products=args.max_products
            )

        else:

            products = client.search_products(
                start_date=args.start_date,
                end_date=args.end_date,
                product_type=args.product_type,
                bounding_box=args.bbox,
                max_products=args.max_products
            )

        if not products:
            logger.warning(
                "No products found for the given filters."
            )
            return

        metadata_path = client.save_metadata(
            products,
            filename="copernicus_search_results.json"
        )

        print("\nSearch Results")
        print("-" * 60)

        for product in products:

            print("Name:", product.get("Name"))
            print("ID:", product.get("Id"))
            print("Online:", product.get("Online"))
            print("-" * 60)

        print("Metadata file:", metadata_path)

        if args.download:

            result = client.download_products(
                products
            )

            print("\nDownload Summary")
            print("Successful:", len(result["downloaded"]))
            print("Failed:", len(result["failed"]))

    except (
        ValueError,
        RuntimeError,
        requests.exceptions.RequestException
    ) as error:

        logger.error("Client operation failed: %s", error)
        sys.exit(1)


if __name__ == "__main__":
    main()

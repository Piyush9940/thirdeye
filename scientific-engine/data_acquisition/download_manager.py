
"""
Central Download Manager
Project: Earth Systems Trend Detective

Responsibilities:
    1. Coordinate NASA CMR and Copernicus downloads.
    2. Search environmental datasets by date.
    3. Apply optional geographic bounding boxes.
    4. Download raw satellite and environmental data.
    5. Save metadata manifests.
    6. Track successful and failed downloads.

Dependencies:
    requests
    python-dotenv

Related modules:
    cmr_search.py
    copernicus_auth.py
    copernicus_client.py
"""

import os
import re
import sys
import json
import logging
import argparse
import time

from pathlib import Path
from datetime import datetime, timezone

import requests

from copernicus_client import CopernicusClient


# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

NASA_DATA_DIR = RAW_DATA_DIR / "nasa"

COPERNICUS_DATA_DIR = RAW_DATA_DIR / "copernicus"

MANIFEST_DIR = RAW_DATA_DIR / "manifests"

CMR_GRANULES_URL = (
    "https://cmr.earthdata.nasa.gov/search/granules.json"
)

TIMEOUT = 120
CHUNK_SIZE = 1024 * 1024

# NASA Earthdata token.
EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN")


# =========================================================
# NASA DATASET CATALOGUE
# =========================================================

NASA_DATASETS = {

    "LST": {
        "short_name": "MOD11A2",
        "description": "MODIS Land Surface Temperature",
        "version": "061"
    },

    "NDVI": {
        "short_name": "MOD13A2",
        "description": "MODIS Vegetation Index",
        "version": "061"
    },

    "ET": {
        "short_name": "MOD16A2GF",
        "description": "MODIS Evapotranspiration",
        "version": "061"
    },

    "GLDAS": {
        "short_name": "GLDAS_NOAH025_M",
        "description": "GLDAS Land Surface Model",
        "version": "2.1"
    },

    "GPM": {
        "short_name": "GPM_3IMERGM",
        "description": "GPM Monthly Precipitation",
        "version": "07"
    },

    "AIRS": {
        "short_name": "AIRX3STM",
        "description": "AIRS Monthly Atmospheric Data",
        "version": "006"
    },

    "CO2": {
        "short_name": "OCO2_L2_Lite_FP",
        "description": "OCO-2 Atmospheric CO2",
        "version": None
    }
}


# =========================================================
# COPERNICUS VARIABLES
# =========================================================

COPERNICUS_VARIABLES = [
    "CH4",
    "NO2",
    "CO",
    "SO2",
    "O3"
]


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("DownloadManager")


# =========================================================
# DOWNLOAD MANAGER
# =========================================================

class DownloadManager:
    """
    Central controller for NASA and Copernicus data acquisition.
    """

    def __init__(self):

        self.nasa_dir = NASA_DATA_DIR
        self.copernicus_dir = COPERNICUS_DATA_DIR
        self.manifest_dir = MANIFEST_DIR

        for directory in [
            self.nasa_dir,
            self.copernicus_dir,
            self.manifest_dir
        ]:
            directory.mkdir(
                parents=True,
                exist_ok=True
            )

        self.copernicus_client = None

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Earth-Systems-Trend-Detective/1.0"
        })

        logger.info("Download Manager initialized.")

    # =====================================================
    # COMMON UTILITIES
    # =====================================================

    @staticmethod
    def validate_dates(start_date, end_date):

        start = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        )

        end = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        )

        if start > end:
            raise ValueError(
                "Start date cannot be later than end date."
            )

    @staticmethod
    def safe_filename(filename):

        filename = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            str(filename)
        )

        return filename.strip(" .")

    def get_bounding_box(self, bbox):

        if not bbox:
            return None

        try:
            values = [
                float(value.strip())
                for value in bbox.split(",")
            ]

        except ValueError as error:
            raise ValueError(
                "Bounding box must be west,south,east,north."
            ) from error

        if len(values) != 4:
            raise ValueError(
                "Bounding box must contain four coordinates."
            )

        west, south, east, north = values

        if not (
            -180 <= west <= 180
            and -180 <= east <= 180
            and -90 <= south <= 90
            and -90 <= north <= 90
            and west < east
            and south < north
        ):
            raise ValueError(
                "Invalid bounding box coordinates."
            )

        return ",".join(map(str, values))

    # =====================================================
    # NASA CMR SEARCH
    # =====================================================

    def search_nasa(
        self,
        short_name,
        start_date,
        end_date,
        bbox=None,
        version=None,
        max_items=10,
        page_size=100
    ):
        """
        Search NASA CMR for granules.

        Returns:
            List of NASA granule metadata.
        """

        self.validate_dates(
            start_date,
            end_date
        )

        if max_items < 1 or page_size < 1:
            raise ValueError(
                "max_items and page_size must be positive."
            )

        params = {
            "short_name": short_name,
            "temporal": (
                f"{start_date}T00:00:00Z,"
                f"{end_date}T23:59:59Z"
            ),
            "page_size": min(page_size, 2000),
            "page_num": 1
        }

        if version:
            params["version"] = version

        if bbox:
            params["bounding_box"] = bbox

        if EARTHDATA_TOKEN:
            headers = {
                "Authorization": f"Bearer {EARTHDATA_TOKEN}"
            }
        else:
            headers = {}

        granules = []

        logger.info(
            "Searching NASA CMR: %s",
            short_name
        )

        while len(granules) < max_items:

            params["page_num"] = (
                (len(granules) // params["page_size"]) + 1
            )

            response = self.session.get(
                CMR_GRANULES_URL,
                params=params,
                headers=headers,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            entries = data.get(
                "feed", {}
            ).get("entry", [])

            if not entries:
                break

            remaining = max_items - len(granules)

            granules.extend(
                entries[:remaining]
            )

            logger.info(
                "NASA granules found: %s",
                len(granules)
            )

            if len(entries) < params["page_size"]:
                break

        logger.info(
            "NASA search completed. Total: %s",
            len(granules)
        )

        return granules

    # =====================================================
    # NASA DOWNLOAD LINK EXTRACTION
    # =====================================================

    @staticmethod
    def extract_nasa_download_links(granule):
        """
        Extract direct data links from a CMR granule.
        """

        links = granule.get("links", [])

        download_links = []

        for link in links:

            href = link.get("href", "")
            rel = link.get("rel", "").lower()

            if not href:
                continue

            # Exclude browse images, metadata and inherited links.
            if "browse" in rel or "metadata" in rel:
                continue

            if "inherited" in rel:
                continue

            if (
                "data#" in rel
                or "download" in rel
                or rel.endswith("/data")
            ):
                download_links.append(href)

        # Fallback: use data-looking URLs if rel metadata
        # is not sufficiently descriptive.
        if not download_links:

            for link in links:

                href = link.get("href", "")

                if not href:
                    continue

                if (
                    href.startswith("http")
                    and not any(
                        term in href.lower()
                        for term in [
                            "browse",
                            "metadata",
                            "opendap"
                        ]
                    )
                ):
                    download_links.append(href)

        return list(dict.fromkeys(download_links))

    # =====================================================
    # NASA GRANULE DOWNLOAD
    # =====================================================

    def download_nasa_granule(
        self,
        granule,
        output_dir=None,
        overwrite=False
    ):
        """
        Download one NASA granule.

        Earthdata authentication may be required.
        """

        output_dir = Path(
            output_dir or self.nasa_dir
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        title = granule.get(
            "title",
            "nasa_granule"
        )

        links = self.extract_nasa_download_links(
            granule
        )

        if not links:
            raise RuntimeError(
                f"No downloadable link found for {title}"
            )

        downloaded_paths = []

        for index, url in enumerate(links, start=1):

            filename = url.split("/")[-1].split("?")[0]

            if not filename:
                filename = f"{self.safe_filename(title)}_{index}"

            filename = self.safe_filename(filename)

            output_path = output_dir / filename

            if output_path.exists() and not overwrite:
                logger.info(
                    "Already downloaded: %s",
                    filename
                )

                downloaded_paths.append(str(output_path))
                continue

            headers = {}

            if EARTHDATA_TOKEN:
                headers["Authorization"] = (
                    f"Bearer {EARTHDATA_TOKEN}"
                )

            logger.info(
                "Downloading NASA file: %s",
                filename
            )

            response = self.session.get(
                url,
                headers=headers,
                stream=True,
                allow_redirects=True,
                timeout=TIMEOUT
            )

            response.raise_for_status()

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
                        "Downloaded NASA file is empty."
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

            downloaded_paths.append(
                str(output_path)
            )

            logger.info(
                "NASA download completed: %s",
                output_path
            )

        return downloaded_paths

    # =====================================================
    # NASA DATASET WORKFLOW
    # =====================================================

    def download_nasa_dataset(
        self,
        dataset,
        start_date,
        end_date,
        bbox=None,
        max_items=10,
        download=True
    ):
        """
        Search and optionally download a NASA dataset.

        dataset can be:
            LST, NDVI, ET, GLDAS, GPM, AIRS, CO2
        """

        dataset = dataset.upper()

        if dataset in NASA_DATASETS:

            config = NASA_DATASETS[dataset]

        else:

            # Also allow direct CMR short names.
            config = {
                "short_name": dataset,
                "description": dataset,
                "version": None
            }

        short_name = config["short_name"]

        logger.info(
            "Starting NASA workflow for %s",
            dataset
        )

        granules = self.search_nasa(
            short_name=short_name,
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            version=config.get("version"),
            max_items=max_items
        )

        output_dir = self.nasa_dir / short_name

        downloaded = []
        failed = []

        if download:

            for granule in granules:

                try:

                    paths = self.download_nasa_granule(
                        granule,
                        output_dir=output_dir
                    )

                    downloaded.extend(paths)

                except Exception as error:

                    logger.error(
                        "NASA granule failed: %s",
                        error
                    )

                    failed.append({
                        "title": granule.get("title"),
                        "error": str(error)
                    })

        return {
            "source": "NASA",
            "dataset": dataset,
            "short_name": short_name,
            "description": config["description"],
            "total_found": len(granules),
            "downloaded": downloaded,
            "failed": failed,
            "granules": granules
        }

    # =====================================================
    # COPERNICUS SEARCH AND DOWNLOAD
    # =====================================================

    def get_copernicus_client(self):

        if self.copernicus_client is None:

            self.copernicus_client = CopernicusClient(
                download_dir=str(self.copernicus_dir)
            )

        return self.copernicus_client

    def download_copernicus_variable(
        self,
        variable,
        start_date,
        end_date,
        bbox=None,
        max_items=10,
        download=True
    ):
        """
        Search and optionally download Sentinel-5P products.

        Variables:
            CH4, NO2, CO, SO2, O3
        """

        variable = variable.upper()

        if variable not in COPERNICUS_VARIABLES:
            raise ValueError(
                f"Unsupported Copernicus variable: {variable}"
            )

        self.validate_dates(
            start_date,
            end_date
        )

        client = self.get_copernicus_client()

        logger.info(
            "Starting Copernicus workflow for %s",
            variable
        )

        products = client.search_by_variable(
            variable=variable,
            start_date=start_date,
            end_date=end_date,
            bounding_box=bbox,
            max_products=max_items
        )

        output_dir = self.copernicus_dir / variable

        downloaded = []
        failed = []

        if download:

            result = client.download_products(
                products,
                output_dir=output_dir
            )

            downloaded = result["downloaded"]
            failed = result["failed"]

        return {
            "source": "Copernicus",
            "variable": variable,
            "total_found": len(products),
            "downloaded": downloaded,
            "failed": failed,
            "products": products
        }

    # =====================================================
    # SAVE MANIFEST
    # =====================================================

    def save_manifest(
        self,
        results,
        filename=None
    ):
        """
        Save combined acquisition metadata.
        """

        if filename is None:

            filename = (
                "download_manifest_"
                + datetime.now(
                    timezone.utc
                ).strftime("%Y%m%d_%H%M%S")
                + ".json"
            )

        manifest_path = self.manifest_dir / filename

        manifest = {
            "project": "Earth Systems Trend Detective",
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "results": results
        }

        with open(
            manifest_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                manifest,
                file,
                indent=4,
                ensure_ascii=False
            )

        logger.info(
            "Manifest saved: %s",
            manifest_path
        )

        return manifest_path

    # =====================================================
    # RUN MULTIPLE DATA SOURCES
    # =====================================================

    def run(
        self,
        source,
        start_date,
        end_date,
        datasets=None,
        variables=None,
        bbox=None,
        max_items=10,
        download=True
    ):
        """
        Execute one or both data acquisition workflows.
        """

        self.validate_dates(
            start_date,
            end_date
        )

        results = []

        if source in ("nasa", "all"):

            if not datasets:
                raise ValueError(
                    "Provide at least one NASA dataset."
                )

            for dataset in datasets:

                try:

                    result = self.download_nasa_dataset(
                        dataset=dataset,
                        start_date=start_date,
                        end_date=end_date,
                        bbox=bbox,
                        max_items=max_items,
                        download=download
                    )

                    results.append(result)

                except Exception as error:

                    logger.exception(
                        "NASA workflow failed for %s",
                        dataset
                    )

                    results.append({
                        "source": "NASA",
                        "dataset": dataset,
                        "error": str(error)
                    })

        if source in ("copernicus", "all"):

            if not variables:
                raise ValueError(
                    "Provide at least one Copernicus variable."
                )

            for variable in variables:

                try:

                    result = self.download_copernicus_variable(
                        variable=variable,
                        start_date=start_date,
                        end_date=end_date,
                        bbox=bbox,
                        max_items=max_items,
                        download=download
                    )

                    results.append(result)

                except Exception as error:

                    logger.exception(
                        "Copernicus workflow failed for %s",
                        variable
                    )

                    results.append({
                        "source": "Copernicus",
                        "variable": variable,
                        "error": str(error)
                    })

        manifest_path = self.save_manifest(results)

        print("\n" + "=" * 60)
        print("DATA ACQUISITION SUMMARY")
        print("=" * 60)

        for result in results:

            print("\nSource:", result.get("source"))
            print(
                "Dataset:",
                result.get(
                    "dataset",
                    result.get("variable", "Unknown")
                )
            )
            print("Found:", result.get("total_found", 0))
            print(
                "Downloaded:",
                len(result.get("downloaded", []))
            )
            print("Failed:", len(result.get("failed", [])))

            if result.get("error"):
                print("Error:", result["error"])

        print("\nManifest:", manifest_path)

        return results


# =========================================================
# COMMAND LINE INTERFACE
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Central data acquisition manager for "
            "Earth Systems Trend Detective."
        )
    )

    parser.add_argument(
        "--source",
        choices=["nasa", "copernicus", "all"],
        required=True
    )

    parser.add_argument(
        "--datasets",
        nargs="+",
        help=(
            "NASA datasets: LST NDVI ET GLDAS GPM AIRS CO2 "
            "or direct CMR short names."
        )
    )

    parser.add_argument(
        "--variables",
        nargs="+",
        choices=COPERNICUS_VARIABLES,
        help="Copernicus variables: CH4 NO2 CO SO2 O3."
    )

    parser.add_argument(
        "--start-date",
        default="2019-01-01"
    )

    parser.add_argument(
        "--end-date",
        default="2024-12-31"
    )

    parser.add_argument(
        "--bbox",
        help="west,south,east,north"
    )

    parser.add_argument(
        "--max-items",
        type=int,
        default=5,
        help="Maximum products/granules per dataset."
    )

    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Search and save metadata without downloading."
    )

    args = parser.parse_args()

    try:

        manager = DownloadManager()

        manager.run(
            source=args.source,
            start_date=args.start_date,
            end_date=args.end_date,
            datasets=args.datasets,
            variables=args.variables,
            bbox=args.bbox,
            max_items=args.max_items,
            download=not args.search_only
        )

    except Exception as error:

        logger.exception(
            "Download manager failed: %s",
            error
        )

        sys.exit(1)


if __name__ == "__main__":
    main()

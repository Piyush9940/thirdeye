
"""
NOAA Data Acquisition Client
============================

Supports:
1. NOAA NCEI ERDDAP:
   - Search datasets
   - Retrieve dataset metadata
   - Download gridded NetCDF/CSV subsets

2. NOAA Climate Data Online (CDO):
   - Retrieve dataset metadata
   - Search stations
   - Download station-based climate observations
   - Handle pagination

Project:
    Earth Systems Trend Detective

Install:
    pip install requests python-dotenv

Environment:
    NOAA_CDO_TOKEN=your_token
    NOAA_ERDDAP_BASE_URL=https://www.ncei.noaa.gov/erddap
    DATA_ROOT=./data
"""

from __future__ import annotations

import json
import logging
import os
import re
import time

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv


# ================================================================
# CONFIGURATION
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

DATA_ROOT = Path(
    os.getenv("DATA_ROOT", str(PROJECT_ROOT / "data"))
)

if not DATA_ROOT.is_absolute():
    DATA_ROOT = PROJECT_ROOT / DATA_ROOT

NOAA_RAW_DIR = DATA_ROOT / "raw" / "noaa"
ERDDAP_DIR = NOAA_RAW_DIR / "erddap"
CDO_DIR = NOAA_RAW_DIR / "cdo"
MANIFEST_DIR = NOAA_RAW_DIR / "manifests"

for directory in (
    ERDDAP_DIR,
    CDO_DIR,
    MANIFEST_DIR,
):
    directory.mkdir(parents=True, exist_ok=True)


ERDDAP_BASE_URL = os.getenv(
    "NOAA_ERDDAP_BASE_URL",
    "https://www.ncei.noaa.gov/erddap",
).rstrip("/")

CDO_BASE_URL = (
    "https://www.ncei.noaa.gov/cdo-web/api/v2"
)

CDO_TOKEN = (
    os.getenv("NOAA_CDO_TOKEN")
    or os.getenv("NOAA_API_TOKEN")
)

REQUEST_TIMEOUT = int(
    os.getenv("NOAA_REQUEST_TIMEOUT", "180")
)

MAX_RETRIES = int(
    os.getenv("NOAA_MAX_RETRIES", "3")
)

PAGE_SIZE = int(
    os.getenv("NOAA_PAGE_SIZE", "1000")
)


# ================================================================
# LOGGING
# ================================================================

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("NOAAClient")


# ================================================================
# EXCEPTIONS
# ================================================================

class NOAAClientError(Exception):
    """Base exception for NOAA acquisition errors."""


class NOAAAuthenticationError(NOAAClientError):
    """Raised when NOAA authentication fails."""


class NOAARequestError(NOAAClientError):
    """Raised when a NOAA request fails."""


class NOAADownloadError(NOAAClientError):
    """Raised when a NOAA file download fails."""


# ================================================================
# GENERAL UTILITIES
# ================================================================

def validate_date(date_string: str) -> str:
    """Validate and return a YYYY-MM-DD date."""
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"Invalid date: {date_string}. Expected YYYY-MM-DD."
        ) from exc

    return date_string


def validate_identifier(value: str, label: str) -> str:
    """Validate a dataset or station identifier."""
    if not value or not re.fullmatch(r"[A-Za-z0-9_.:-]+", value):
        raise ValueError(f"Invalid {label}: {value!r}")

    return value


def save_json(data: Any, destination: Path) -> Path:
    """Save JSON metadata or download manifests."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, default=str)

    return destination


# ================================================================
# BASE HTTP CLIENT
# ================================================================

class NOAAHTTPClient:
    """Shared HTTP session with retry handling."""

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Earth-Systems-Trend-Detective/1.0",
            "Accept": "*/*",
        })

    def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        stream: bool = False,
    ) -> requests.Response:
        """Perform a GET request with retry handling."""

        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    stream=stream,
                )

                if response.status_code in (401, 403):
                    raise NOAAAuthenticationError(
                        "NOAA rejected the request. Check your API token "
                        "or dataset access permissions."
                    )

                if response.status_code == 429:
                    wait = min(2 ** attempt * 5, 60)
                    logger.warning(
                        "Rate limit reached. Retrying in %s seconds.",
                        wait,
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response

            except NOAAAuthenticationError:
                raise

            except requests.RequestException as exc:
                last_error = exc

                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Request failed. Retrying in %s seconds: %s",
                        wait,
                        exc,
                    )
                    time.sleep(wait)

        raise NOAARequestError(
            f"NOAA request failed after {MAX_RETRIES} attempts: "
            f"{last_error}"
        )


# ================================================================
# NOAA ERDDAP CLIENT
# ================================================================

class NOAAERDDAPClient:
    """
    NOAA ERDDAP client for gridded and tabular environmental data.

    Useful for:
        - Sea surface temperature
        - Oceanographic variables
        - Satellite-derived products
        - Gridded climate data

    ERDDAP supports griddap for gridded datasets and tabledap
    for tabular datasets.
    """

    def __init__(
        self,
        base_url: str = ERDDAP_BASE_URL,
        output_dir: Path = ERDDAP_DIR,
    ):
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.http = NOAAHTTPClient()

    # ------------------------------------------------------------
    # SEARCH DATASETS
    # ------------------------------------------------------------

    def search_datasets(
        self,
        keyword: str,
        page: int = 1,
        items_per_page: int = 100,
    ) -> list[dict]:
        """
        Search ERDDAP datasets by keyword.

        Examples:
            temperature
            ocean
            sea surface temperature
            precipitation
            wind
        """

        if not keyword.strip():
            raise ValueError("Search keyword cannot be empty.")

        if page < 1 or items_per_page < 1:
            raise ValueError("Invalid pagination parameters.")

        url = f"{self.base_url}/search/index.json"

        params = {
            "page": page,
            "itemsPerPage": items_per_page,
            "searchFor": keyword,
        }

        response = self.http.get(url, params=params)
        payload = response.json()

        table = payload.get("table", {})
        raw_columns = table.get("columnNames", [])
        columns = [
            column["name"] if isinstance(column, dict) else column
            for column in raw_columns
        ]

        results = [
            dict(zip(columns, row))
            for row in table.get("rows", [])
        ]

        logger.info(
            "ERDDAP search '%s' returned %s datasets.",
            keyword,
            len(results),
        )

        return results

    # ------------------------------------------------------------
    # DATASET METADATA
    # ------------------------------------------------------------

    def get_dataset_metadata(
        self,
        dataset_id: str,
    ) -> dict:
        """Retrieve variables and metadata for an ERDDAP dataset."""

        dataset_id = validate_identifier(
            dataset_id,
            "ERDDAP dataset ID",
        )

        url = (
            f"{self.base_url}/info/"
            f"{dataset_id}/index.json"
        )

        response = self.http.get(url)
        payload = response.json()

        table = payload.get("table", {})
        raw_columns = table.get("columnNames", [])
        columns = [
            column["name"] if isinstance(column, dict) else column
            for column in raw_columns
        ]

        rows = [
            dict(zip(columns, row))
            for row in table.get("rows", [])
        ]

        metadata = {
            "dataset_id": dataset_id,
            "metadata": rows,
            "retrieved_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        save_json(
            metadata,
            self.output_dir / "metadata" / f"{dataset_id}.json",
        )

        return metadata

    # ------------------------------------------------------------
    # GRIDDAP DOWNLOAD
    # ------------------------------------------------------------

    def download_griddap(
        self,
        dataset_id: str,
        query: str,
        file_format: str = "nc",
        filename: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Download a gridded dataset subset.

        `query` must be a valid ERDDAP griddap projection constraint.

        Example shape:
            variable[(time_start):(time_end)]
                    [(latitude_start):(latitude_end)]
                    [(longitude_start):(longitude_end)]

        IMPORTANT:
            Coordinate names, ordering, and available variables
            depend on the selected dataset. Inspect its metadata first.
        """

        dataset_id = validate_identifier(
            dataset_id,
            "ERDDAP dataset ID",
        )

        allowed_formats = {
            "nc",
            "csv",
            "csvp",
            "csv0",
            "json",
        }

        if file_format not in allowed_formats:
            raise ValueError(
                f"Unsupported format: {file_format}. "
                f"Choose from {sorted(allowed_formats)}."
            )

        if not query or not query.strip():
            raise ValueError("A griddap query is required.")

        if filename is None:
            filename = f"{dataset_id}_subset.{file_format}"

        if Path(filename).name != filename:
            raise ValueError("Filename must not contain directory paths.")

        destination = self.output_dir / filename

        if destination.exists() and not overwrite:
            logger.info("File already exists: %s", destination)
            return destination

        # Preserve ERDDAP query delimiters while encoding spaces
        # and other URL-sensitive characters.
        encoded_query = quote(
            query.strip(),
            safe="[]():,",
        )

        url = (
            f"{self.base_url}/griddap/"
            f"{dataset_id}.{file_format}?{encoded_query}"
        )

        logger.info("Downloading ERDDAP dataset: %s", dataset_id)

        try:
            response = self.http.get(url, stream=True)

            temporary_path = destination.with_suffix(
                destination.suffix + ".part"
            )

            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

            if temporary_path.stat().st_size == 0:
                temporary_path.unlink(missing_ok=True)
                raise NOAADownloadError(
                    "NOAA returned an empty file."
                )

            temporary_path.replace(destination)

            logger.info("Downloaded: %s", destination)

            self._write_download_manifest(
                source="ERDDAP",
                dataset_id=dataset_id,
                destination=destination,
                request_url=url,
                file_format=file_format,
            )

            return destination

        except Exception as exc:
            raise NOAADownloadError(
                f"ERDDAP download failed for {dataset_id}: {exc}"
            ) from exc

    # ------------------------------------------------------------
    # TABLEDAP DOWNLOAD
    # ------------------------------------------------------------

    def download_tabledap(
        self,
        dataset_id: str,
        query: str,
        file_format: str = "csv",
        filename: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """Download a tabledap dataset subset."""

        dataset_id = validate_identifier(
            dataset_id,
            "ERDDAP dataset ID",
        )

        if file_format not in {"csv", "json"}:
            raise ValueError("Tabledap format must be csv or json.")

        if not query or not query.strip():
            raise ValueError("A tabledap query is required.")

        if filename is None:
            filename = f"{dataset_id}_table.{file_format}"

        if Path(filename).name != filename:
            raise ValueError("Invalid filename.")

        destination = self.output_dir / filename

        if destination.exists() and not overwrite:
            return destination

        encoded_query = quote(
            query.strip(),
            safe="[]():,",
        )

        url = (
            f"{self.base_url}/tabledap/"
            f"{dataset_id}.{file_format}?{encoded_query}"
        )

        response = self.http.get(url, stream=True)

        temporary_path = destination.with_suffix(
            destination.suffix + ".part"
        )

        try:
            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

            if temporary_path.stat().st_size == 0:
                raise NOAADownloadError("Empty tabledap response.")

            temporary_path.replace(destination)

            self._write_download_manifest(
                source="ERDDAP",
                dataset_id=dataset_id,
                destination=destination,
                request_url=url,
                file_format=file_format,
            )

            return destination

        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    # ------------------------------------------------------------
    # MANIFEST
    # ------------------------------------------------------------

    @staticmethod
    def _write_download_manifest(
        source: str,
        dataset_id: str,
        destination: Path,
        request_url: str,
        file_format: str,
    ) -> Path:
        manifest = {
            "source": f"NOAA {source}",
            "dataset_id": dataset_id,
            "file": str(destination.resolve()),
            "file_size_bytes": destination.stat().st_size,
            "format": file_format,
            "request_url": request_url,
            "downloaded_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        manifest_path = (
            MANIFEST_DIR /
            f"noaa_{source.lower()}_{dataset_id}.json"
        )

        return save_json(manifest, manifest_path)


# ================================================================
# NOAA CLIMATE DATA ONLINE CLIENT
# ================================================================

class NOAACDOClient:
    """
    NOAA Climate Data Online API v2 client.

    Supports:
        - Dataset discovery
        - Station discovery
        - Data type discovery
        - Climate observation retrieval

    Requires a NOAA CDO API token.
    """

    def __init__(
        self,
        token: Optional[str] = CDO_TOKEN,
        output_dir: Path = CDO_DIR,
    ):
        if not token:
            raise NOAAAuthenticationError(
                "NOAA CDO token is missing. Set NOAA_CDO_TOKEN in .env."
            )

        self.token = token
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.http = NOAAHTTPClient()

    # ------------------------------------------------------------
    # GENERIC API REQUEST
    # ------------------------------------------------------------

    def _request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> dict:
        url = f"{CDO_BASE_URL}/{endpoint.lstrip('/')}"

        response = self.http.get(
            url,
            params=params,
            headers={"token": self.token},
        )

        try:
            return response.json()
        except ValueError as exc:
            raise NOAARequestError(
                "NOAA CDO returned invalid JSON."
            ) from exc

    # ------------------------------------------------------------
    # DISCOVERY
    # ------------------------------------------------------------

    def get_datasets(
        self,
        limit: int = 1000,
        offset: int = 0,
        **filters,
    ) -> list[dict]:
        """Discover available NOAA climate datasets."""

        payload = self._request(
            "datasets",
            {
                "limit": min(limit, 1000),
                "offset": offset,
                **filters,
            },
        )

        return payload.get("results", [])

    def get_stations(
        self,
        dataset_id: Optional[str] = None,
        location_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict]:
        """Discover stations for a dataset or location."""

        params = {
            "limit": min(limit, 1000),
            "offset": offset,
        }

        if dataset_id:
            params["datasetid"] = dataset_id

        if location_id:
            params["locationid"] = location_id

        if start_date:
            params["startdate"] = validate_date(start_date)

        if end_date:
            params["enddate"] = validate_date(end_date)

        payload = self._request("stations", params)

        return payload.get("results", [])

    def get_data_types(
        self,
        dataset_id: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """Retrieve available climate observation data types."""

        params = {"limit": min(limit, 1000)}

        if dataset_id:
            params["datasetid"] = dataset_id

        payload = self._request("datatypes", params)

        return payload.get("results", [])

    # ------------------------------------------------------------
    # CLIMATE DATA DOWNLOAD
    # ------------------------------------------------------------

    def download_observations(
        self,
        dataset_id: str,
        start_date: str,
        end_date: str,
        station_ids: Optional[list[str]] = None,
        location_ids: Optional[list[str]] = None,
        datatype_ids: Optional[list[str]] = None,
        units: str = "metric",
        limit: int = 1000,
        max_records: Optional[int] = None,
    ) -> list[dict]:
        """
        Retrieve paginated CDO observations.

        A dataset ID is mandatory.

        Optional filters:
            station_ids
            location_ids
            datatype_ids

        The CDO API has a maximum limit of 1000 records per request.
        """

        dataset_id = validate_identifier(
            dataset_id,
            "CDO dataset ID",
        )

        start_date = validate_date(start_date)
        end_date = validate_date(end_date)

        if start_date > end_date:
            raise ValueError("Start date must not be after end date.")

        if units not in {"standard", "metric"}:
            raise ValueError("Units must be standard or metric.")

        if limit < 1:
            raise ValueError("Limit must be positive.")

        if max_records is not None and max_records < 1:
            raise ValueError("max_records must be positive.")

        results = []
        offset = 1
        page_limit = min(limit, 1000)

        while True:
            params = {
                "datasetid": dataset_id,
                "startdate": start_date,
                "enddate": end_date,
                "units": units,
                "limit": page_limit,
                "offset": offset,
            }

            if station_ids:
                params["stationid"] = station_ids

            if location_ids:
                params["locationid"] = location_ids

            if datatype_ids:
                params["datatypeid"] = datatype_ids

            payload = self._request("data", params)
            page_results = payload.get("results", [])

            if not page_results:
                break

            results.extend(page_results)

            logger.info(
                "CDO records collected: %s",
                len(results),
            )

            if max_records and len(results) >= max_records:
                results = results[:max_records]
                break

            if len(page_results) < page_limit:
                break

            offset += len(page_results)

            # Stay comfortably below the documented API rate limit.
            time.sleep(0.25)

        destination = (
            self.output_dir /
            f"{dataset_id}_{start_date}_{end_date}.json"
        )

        save_json(
            {
                "source": "NOAA Climate Data Online",
                "dataset_id": dataset_id,
                "start_date": start_date,
                "end_date": end_date,
                "units": units,
                "record_count": len(results),
                "records": results,
                "downloaded_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            },
            destination,
        )

        logger.info(
            "Saved %s observations to %s",
            len(results),
            destination,
        )

        return results


# ================================================================
# CLI
# ================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="NOAA environmental data acquisition."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ERDDAP search
    search_parser = subparsers.add_parser(
        "search",
        help="Search NOAA ERDDAP datasets.",
    )

    search_parser.add_argument(
        "--keyword",
        required=True,
    )

    # ERDDAP metadata
    metadata_parser = subparsers.add_parser(
        "metadata",
        help="Retrieve ERDDAP dataset metadata.",
    )

    metadata_parser.add_argument(
        "--dataset",
        required=True,
    )

    # ERDDAP download
    download_parser = subparsers.add_parser(
        "download",
        help="Download an ERDDAP gridded subset.",
    )

    download_parser.add_argument(
        "--dataset",
        required=True,
    )

    download_parser.add_argument(
        "--query",
        required=True,
        help="ERDDAP griddap projection constraint.",
    )

    download_parser.add_argument(
        "--format",
        default="nc",
        choices=["nc", "csv", "csvp", "csv0", "json"],
    )

    # CDO download
    cdo_parser = subparsers.add_parser(
        "cdo",
        help="Download NOAA CDO climate observations.",
    )

    cdo_parser.add_argument(
        "--dataset",
        required=True,
    )

    cdo_parser.add_argument(
        "--start",
        required=True,
    )

    cdo_parser.add_argument(
        "--end",
        required=True,
    )

    cdo_parser.add_argument(
        "--stations",
        nargs="+",
    )

    args = parser.parse_args()

    try:
        if args.command == "search":
            client = NOAAERDDAPClient()
            results = client.search_datasets(args.keyword)
            print(json.dumps(results, indent=4))

        elif args.command == "metadata":
            client = NOAAERDDAPClient()
            results = client.get_dataset_metadata(args.dataset)
            print(json.dumps(results, indent=4))

        elif args.command == "download":
            client = NOAAERDDAPClient()
            path = client.download_griddap(
                dataset_id=args.dataset,
                query=args.query,
                file_format=args.format,
            )
            print(f"\nDownloaded: {path}")

        elif args.command == "cdo":
            client = NOAACDOClient()
            results = client.download_observations(
                dataset_id=args.dataset,
                start_date=args.start,
                end_date=args.end,
                station_ids=args.stations,
            )
            print(f"\nDownloaded {len(results)} records.")

    except (NOAAClientError, ValueError) as exc:
        logger.error("%s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
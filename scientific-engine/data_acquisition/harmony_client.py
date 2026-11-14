
"""
NASA Earthdata Harmony Client
-----------------------------
Submits spatial and temporal data-subsetting requests to NASA Harmony,
downloads processed files, and writes download manifests.

Project:
    Earth Systems Trend Detective

Install:
    pip install -U harmony-py python-dotenv

Authentication:
    EDL_USERNAME / EDL_PASSWORD
    or EARTHDATA_USERNAME / EARTHDATA_PASSWORD
    or NASA_EARTHDATA_USERNAME / NASA_EARTHDATA_PASSWORD
    or ~/.netrc

Example:
    python harmony_client.py \
        --collection C1234567890-EXAMPLE \
        --start 2019-01-01 \
        --end 2024-12-31 \
        --bbox -180 -90 180 90 \
        --format application/x-netcdf
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv

try:
    from harmony import Client, Request, Collection, BBox
except ImportError as exc:
    raise ImportError(
        "NASA Harmony client is not installed. Run:\n"
        "pip install -U harmony-py"
    ) from exc


# ---------------------------------------------------------------------
# PATHS AND CONFIGURATION
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

DATA_ROOT = Path(
    os.getenv("DATA_ROOT", str(PROJECT_ROOT / "data"))
)

if not DATA_ROOT.is_absolute():
    DATA_ROOT = PROJECT_ROOT / DATA_ROOT

HARMONY_OUTPUT_DIR = (
    DATA_ROOT / "raw" / "nasa" / "harmony"
)

MANIFEST_DIR = (
    DATA_ROOT / "raw" / "manifests"
)

HARMONY_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

HARMONY_FORMAT = os.getenv(
    "HARMONY_FORMAT",
    "application/x-netcdf"
)

HARMONY_CHECK_INTERVAL = float(
    os.getenv("HARMONY_CHECK_INTERVAL", "5")
)

HARMONY_DOWNLOAD_TIMEOUT = float(
    os.getenv("HARMONY_DOWNLOAD_TIMEOUT", "3600")
)


# ---------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("HarmonyClient")


# ---------------------------------------------------------------------
# EXCEPTIONS
# ---------------------------------------------------------------------

class HarmonyClientError(Exception):
    """Base exception for Harmony client operations."""


class HarmonyAuthenticationError(HarmonyClientError):
    """Raised when Earthdata authentication fails."""


class HarmonyDownloadError(HarmonyClientError):
    """Raised when a Harmony job or download fails."""


# ---------------------------------------------------------------------
# DATE UTILITIES
# ---------------------------------------------------------------------

def parse_datetime(value: str) -> datetime:
    """
    Convert an ISO date or datetime string to a timezone-aware UTC datetime.

    Accepted examples:
        2019-01-01
        2019-01-01T00:00:00
        2019-01-01T00:00:00Z
    """
    try:
        parsed = datetime.fromisoformat(
            value.strip().replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid date/datetime: {value}"
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def validate_bbox(
    bbox: Optional[Sequence[float]],
) -> Optional[BBox]:
    """
    Validate and construct a Harmony bounding box.

    Order:
        west, south, east, north
    """
    if bbox is None:
        return None

    if len(bbox) != 4:
        raise ValueError(
            "Bounding box must contain four values: "
            "west south east north"
        )

    west, south, east, north = map(float, bbox)

    if not (-180 <= west <= 180):
        raise ValueError("West longitude must be between -180 and 180.")

    if not (-180 <= east <= 180):
        raise ValueError("East longitude must be between -180 and 180.")

    if not (-90 <= south <= 90):
        raise ValueError("South latitude must be between -90 and 90.")

    if not (-90 <= north <= 90):
        raise ValueError("North latitude must be between -90 and 90.")

    if south >= north:
        raise ValueError("South latitude must be less than north latitude.")

    if west == east:
        raise ValueError("West and east longitude cannot be identical.")

    # A west > east box can represent a dateline-crossing region.
    return BBox(west, south, east, north)


# ---------------------------------------------------------------------
# HARMONY CLIENT
# ---------------------------------------------------------------------

class NASAՀarmonyClient:
    """
    Wrapper around NASA's official harmony-py client.

    Responsibilities:
        1. Configure Earthdata authentication.
        2. Build Harmony transformation requests.
        3. Submit jobs.
        4. Wait for job completion and download results.
        5. Save job metadata and local file paths.
    """

    def __init__(
        self,
        output_dir: Optional[Path | str] = None,
        check_interval: float = HARMONY_CHECK_INTERVAL,
        download_timeout: float = HARMONY_DOWNLOAD_TIMEOUT,
    ):
        self.output_dir = Path(
            output_dir or HARMONY_OUTPUT_DIR
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.check_interval = check_interval
        self.download_timeout = download_timeout

        self.client = self._create_client()

    @staticmethod
    def _configure_credentials() -> None:
        """
        Map project credential variable names to the names
        supported by harmony-py.
        """
        username = (
            os.getenv("EDL_USERNAME")
            or os.getenv("EARTHDATA_USERNAME")
            or os.getenv("NASA_EARTHDATA_USERNAME")
        )

        password = (
            os.getenv("EDL_PASSWORD")
            or os.getenv("EARTHDATA_PASSWORD")
            or os.getenv("NASA_EARTHDATA_PASSWORD")
        )

        if username and password:
            os.environ["EDL_USERNAME"] = username
            os.environ["EDL_PASSWORD"] = password

    def _create_client(self) -> Client:
        self._configure_credentials()

        username = os.getenv("EDL_USERNAME")
        password = os.getenv("EDL_PASSWORD")

        try:
            if username and password:
                logger.info("Initializing Harmony with Earthdata credentials.")

                return Client(
                    auth=(username, password),
                    check_interval=self.check_interval,
                    download_timeout=self.download_timeout,
                )

            logger.info(
                "Initializing Harmony using environment or .netrc credentials."
            )

            return Client(
                check_interval=self.check_interval,
                download_timeout=self.download_timeout,
            )

        except Exception as exc:
            raise HarmonyAuthenticationError(
                "Could not initialize NASA Harmony. Check your "
                "Earthdata Login credentials and network connection."
            ) from exc

    # -----------------------------------------------------------------
    # REQUEST BUILDER
    # -----------------------------------------------------------------

    def build_request(
        self,
        collection_id: str,
        start_date: str,
        end_date: str,
        bbox: Optional[Sequence[float]] = None,
        variables: Optional[Sequence[str]] = None,
        output_format: str = HARMONY_FORMAT,
        max_results: Optional[int] = None,
        concatenate: bool = False,
        crs: Optional[str] = None,
    ) -> Request:
        """
        Build a NASA Harmony request.

        collection_id:
            CMR collection concept ID.

        bbox:
            [west, south, east, north]

        variables:
            List of dataset variables. Defaults to all variables.

        output_format:
            Requested output MIME type. The selected collection and
            its Harmony service must support the requested format.
        """
        if not collection_id or not collection_id.strip():
            raise ValueError("A CMR collection ID is required.")

        start = parse_datetime(start_date)
        stop = parse_datetime(end_date)

        if start >= stop:
            raise ValueError("Start date must be earlier than end date.")

        spatial = validate_bbox(bbox)

        selected_variables = (
            list(variables)
            if variables
            else ["all"]
        )

        if any(not item.strip() for item in selected_variables):
            raise ValueError("Variable names cannot be empty.")

        if max_results is not None and max_results <= 0:
            raise ValueError("max_results must be a positive integer.")

        request_arguments = {
            "collection": Collection(id=collection_id.strip()),
            "temporal": {
                "start": start,
                "stop": stop,
            },
            "variables": selected_variables,
            "format": output_format,
            "concatenate": concatenate,
        }

        if spatial is not None:
            request_arguments["spatial"] = spatial

        if max_results is not None:
            request_arguments["max_results"] = max_results

        if crs:
            request_arguments["crs"] = crs

        request = Request(**request_arguments)

        if not request.is_valid():
            raise HarmonyClientError(
                "Invalid Harmony request: "
                + "; ".join(request.error_messages())
            )

        return request

    # -----------------------------------------------------------------
    # JOB SUBMISSION
    # -----------------------------------------------------------------

    def submit_job(
        self,
        collection_id: str,
        start_date: str,
        end_date: str,
        bbox: Optional[Sequence[float]] = None,
        variables: Optional[Sequence[str]] = None,
        output_format: str = HARMONY_FORMAT,
        max_results: Optional[int] = None,
        concatenate: bool = False,
        crs: Optional[str] = None,
    ) -> str:
        """
        Submit a transformation request and return the Harmony job ID.
        """
        request = self.build_request(
            collection_id=collection_id,
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            variables=variables,
            output_format=output_format,
            max_results=max_results,
            concatenate=concatenate,
            crs=crs,
        )

        logger.info("Submitting Harmony request.")
        logger.info("Collection: %s", collection_id)
        logger.info("Period: %s to %s", start_date, end_date)

        try:
            job_id = self.client.submit(request)
        except Exception as exc:
            raise HarmonyClientError(
                f"Failed to submit Harmony request: {exc}"
            ) from exc

        if not isinstance(job_id, str):
            raise HarmonyClientError(
                f"Expected a Harmony job ID, received: {job_id!r}"
            )

        logger.info("Harmony job submitted: %s", job_id)

        return job_id

    # -----------------------------------------------------------------
    # JOB STATUS
    # -----------------------------------------------------------------

    def get_job_status(self, job_id: str) -> dict:
        """Retrieve the current Harmony job metadata."""
        try:
            return self.client.status(job_id)
        except Exception as exc:
            raise HarmonyClientError(
                f"Could not retrieve status for job {job_id}: {exc}"
            ) from exc

    def wait_for_job(self, job_id: str) -> None:
        """Wait until the Harmony job reaches a terminal state."""
        logger.info("Waiting for Harmony job: %s", job_id)

        try:
            self.client.wait_for_processing(
                job_id,
                show_progress=True,
            )
        except Exception as exc:
            raise HarmonyDownloadError(
                f"Harmony job processing failed: {job_id}"
            ) from exc

    # -----------------------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------------------

    def download_job(
        self,
        job_id: str,
        overwrite: bool = False,
    ) -> list[Path]:
        """
        Download all output files from a completed Harmony job.

        Returns:
            List of downloaded file paths.
        """
        logger.info("Downloading outputs for job %s", job_id)

        try:
            futures = self.client.download_all(
                job_id,
                directory=str(self.output_dir),
                overwrite=overwrite,
            )

            downloaded_files = []

            for future in futures:
                file_path = Path(future.result())
                downloaded_files.append(file_path)
                logger.info("Downloaded: %s", file_path)

            return downloaded_files

        except Exception as exc:
            raise HarmonyDownloadError(
                f"Failed to download Harmony job {job_id}: {exc}"
            ) from exc

    # -----------------------------------------------------------------
    # MANIFEST
    # -----------------------------------------------------------------

    @staticmethod
    def _write_manifest(
        job_id: str,
        collection_id: str,
        start_date: str,
        end_date: str,
        bbox: Optional[Sequence[float]],
        variables: Optional[Sequence[str]],
        output_format: str,
        downloaded_files: Sequence[Path],
    ) -> Path:
        """Write a JSON record describing the Harmony download."""
        manifest = {
            "source": "NASA Harmony",
            "job_id": job_id,
            "collection_id": collection_id,
            "start_date": start_date,
            "end_date": end_date,
            "bbox": list(bbox) if bbox is not None else None,
            "variables": list(variables) if variables else ["all"],
            "output_format": output_format,
            "downloaded_files": [
                str(path.resolve())
                for path in downloaded_files
            ],
            "download_count": len(downloaded_files),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        manifest_path = MANIFEST_DIR / f"harmony_{job_id}.json"

        manifest_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with manifest_path.open("w", encoding="utf-8") as file:
            json.dump(
                manifest,
                file,
                indent=4,
                ensure_ascii=False,
            )

        logger.info("Manifest saved: %s", manifest_path)

        return manifest_path

    # -----------------------------------------------------------------
    # COMPLETE WORKFLOW
    # -----------------------------------------------------------------

    def download_collection(
        self,
        collection_id: str,
        start_date: str,
        end_date: str,
        bbox: Optional[Sequence[float]] = None,
        variables: Optional[Sequence[str]] = None,
        output_format: str = HARMONY_FORMAT,
        max_results: Optional[int] = None,
        concatenate: bool = False,
        crs: Optional[str] = None,
        overwrite: bool = False,
    ) -> dict:
        """
        Complete workflow:
            Build request -> Submit -> Wait -> Download -> Manifest.
        """
        job_id = self.submit_job(
            collection_id=collection_id,
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            variables=variables,
            output_format=output_format,
            max_results=max_results,
            concatenate=concatenate,
            crs=crs,
        )

        self.wait_for_job(job_id)

        downloaded_files = self.download_job(
            job_id=job_id,
            overwrite=overwrite,
        )

        manifest_path = self._write_manifest(
            job_id=job_id,
            collection_id=collection_id,
            start_date=start_date,
            end_date=end_date,
            bbox=bbox,
            variables=variables,
            output_format=output_format,
            downloaded_files=downloaded_files,
        )

        return {
            "success": True,
            "job_id": job_id,
            "downloaded_files": [
                str(path) for path in downloaded_files
            ],
            "download_count": len(downloaded_files),
            "manifest": str(manifest_path),
        }


# ---------------------------------------------------------------------
# COMMAND LINE INTERFACE
# ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NASA Earthdata Harmony data acquisition client."
    )

    parser.add_argument(
        "--collection",
        required=True,
        help="NASA CMR collection concept ID.",
    )

    parser.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY-MM-DD).",
    )

    parser.add_argument(
        "--end",
        required=True,
        help="End date (YYYY-MM-DD).",
    )

    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        help="Spatial bounding box.",
    )

    parser.add_argument(
        "--variables",
        nargs="+",
        default=["all"],
        help="Variables to request. Defaults to all.",
    )

    parser.add_argument(
        "--format",
        default=HARMONY_FORMAT,
        help="Output MIME type supported by the collection.",
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=None,
        help="Optional maximum number of input granules.",
    )

    parser.add_argument(
        "--concatenate",
        action="store_true",
        help="Request concatenation if supported by the service.",
    )

    parser.add_argument(
        "--crs",
        default=None,
        help="Optional output coordinate reference system.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing downloaded files.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        harmony = NASAHarmonyClient()

        result = harmony.download_collection(
            collection_id=args.collection,
            start_date=args.start,
            end_date=args.end,
            bbox=args.bbox,
            variables=args.variables,
            output_format=args.format,
            max_results=args.max_results,
            concatenate=args.concatenate,
            crs=args.crs,
            overwrite=args.overwrite,
        )

        print("\n========== HARMONY DOWNLOAD RESULT ==========")
        print(json.dumps(result, indent=4))
        print("=============================================\n")

        return 0

    except (HarmonyClientError, ValueError) as exc:
        logger.error("%s", exc)
        return 1

    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

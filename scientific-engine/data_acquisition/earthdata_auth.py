
"""
NASA Earthdata Authentication Module
Project: Earth Systems Trend Detective

Purpose:
    Authenticate with NASA Earthdata Login.
    Provide authenticated sessions for NASA APIs and downloads.
    Support Earthdata token authentication and login-based access.

Dependencies:
    requests
    python-dotenv
    earthaccess

Environment variables:
    EARTHDATA_USERNAME
    EARTHDATA_PASSWORD
    EARTHDATA_TOKEN (optional)

"""

import os
import logging
import requests

from pathlib import Path
from dotenv import load_dotenv


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

EARTHDATA_USERNAME = os.getenv("EARTHDATA_USERNAME")
EARTHDATA_PASSWORD = os.getenv("EARTHDATA_PASSWORD")
EARTHDATA_TOKEN = os.getenv("EARTHDATA_TOKEN")

EARTHDATA_LOGIN_URL = (
    "https://urs.earthdata.nasa.gov"
)

CMR_URL = (
    "https://cmr.earthdata.nasa.gov"
)

TIMEOUT = 30


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("EarthdataAuth")


# ---------------------------------------------------------
# AUTHENTICATION CLASS
# ---------------------------------------------------------

class EarthdataAuth:
    """
    NASA Earthdata authentication manager.

    Supports:
        1. Earthdata bearer token.
        2. Username/password login through earthaccess.
        3. Authenticated requests using requests.Session.
    """

    def __init__(self):

        self.session = requests.Session()
        self.authenticated = False
        self.token = None

        self.username = EARTHDATA_USERNAME
        self.password = EARTHDATA_PASSWORD

        self._configure_session()

    # -----------------------------------------------------
    # SESSION CONFIGURATION
    # -----------------------------------------------------

    def _configure_session(self):

        self.session.headers.update({
            "User-Agent": (
                "Earth-Systems-Trend-Detective/1.0"
            )
        })

    # -----------------------------------------------------
    # TOKEN AUTHENTICATION
    # -----------------------------------------------------

    def authenticate_with_token(self, token=None):
        """
        Authenticate using a NASA Earthdata bearer token.

        Token can be passed directly or loaded from .env.
        """

        token = token or EARTHDATA_TOKEN

        if not token:
            raise ValueError(
                "Earthdata token not found. "
                "Set EARTHDATA_TOKEN in your .env file."
            )

        self.token = token.strip()

        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })

        self.authenticated = True

        logger.info(
            "Earthdata token configured."
        )

        return True

    # -----------------------------------------------------
    # USERNAME/PASSWORD AUTHENTICATION
    # -----------------------------------------------------

    def authenticate_with_credentials(self):
        """
        Authenticate using Earthdata username/password
        through the earthaccess library.

        earthaccess manages the NASA authentication flow.
        """

        if not self.username or not self.password:
            raise ValueError(
                "Earthdata credentials not found. "
                "Set EARTHDATA_USERNAME and "
                "EARTHDATA_PASSWORD in .env."
            )

        try:

            import earthaccess

            earthaccess.login(
                strategy="environment",
                persist=False
            )

            # Configure a requests session for NASA
            # Earthdata-hosted downloads.
            self.session.auth = (
                self.username,
                self.password
            )

            self.authenticated = True

            logger.info(
                "Earthdata authentication successful."
            )

            return True

        except Exception as error:

            self.authenticated = False

            raise RuntimeError(
                f"Earthdata authentication failed: {error}"
            ) from error

    # -----------------------------------------------------
    # AUTOMATIC AUTHENTICATION
    # -----------------------------------------------------

    def authenticate(self):
        """
        Authenticate using the best available method.

        Priority:
            1. Bearer token.
            2. Earthdata username/password.
        """

        if EARTHDATA_TOKEN:
            return self.authenticate_with_token()

        return self.authenticate_with_credentials()

    # -----------------------------------------------------
    # GET SESSION
    # -----------------------------------------------------

    def get_session(self):
        """
        Return an authenticated requests session.
        """

        if not self.authenticated:
            self.authenticate()

        return self.session

    # -----------------------------------------------------
    # AUTHENTICATED GET REQUEST
    # -----------------------------------------------------

    def get(self, url, params=None, **kwargs):
        """
        Make an authenticated GET request.
        """

        session = self.get_session()

        response = session.get(
            url,
            params=params,
            timeout=kwargs.pop("timeout", TIMEOUT),
            **kwargs
        )

        response.raise_for_status()

        return response

    # -----------------------------------------------------
    # AUTHENTICATED DOWNLOAD
    # -----------------------------------------------------

    def download_file(
        self,
        url,
        destination,
        overwrite=False
    ):
        """
        Download a NASA Earthdata file.

        Downloads are written to a temporary file first,
        then renamed after successful completion.
        """

        destination = Path(destination)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if destination.exists() and not overwrite:

            logger.info(
                "File already exists. Skipping: %s",
                destination
            )

            return destination

        temporary_path = destination.with_name(
            destination.name + ".part"
        )

        session = self.get_session()

        try:

            with session.get(
                url,
                stream=True,
                allow_redirects=True,
                timeout=TIMEOUT
            ) as response:

                response.raise_for_status()

                with open(temporary_path, "wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):

                        if chunk:
                            file.write(chunk)

            if not temporary_path.exists():
                raise RuntimeError(
                    "Download did not create a file."
                )

            if temporary_path.stat().st_size == 0:
                raise RuntimeError(
                    "Downloaded file is empty."
                )

            os.replace(
                temporary_path,
                destination
            )

            logger.info(
                "Download completed: %s",
                destination
            )

            return destination

        except Exception:

            if temporary_path.exists():
                temporary_path.unlink()

            raise

    # -----------------------------------------------------
    # CONNECTION TEST
    # -----------------------------------------------------

    def test_connection(self):
        """
        Test connectivity to NASA CMR.

        This checks that the client can reach CMR.
        It does not guarantee access to every protected dataset.
        """

        logger.info(
            "Testing NASA Earthdata connection..."
        )

        response = self.get(
            f"{CMR_URL}/search/collections.json",
            params={
                "page_size": 1
            }
        )

        data = response.json()

        collections = data.get(
            "feed", {}
        ).get("entry", [])

        logger.info(
            "NASA CMR connection successful."
        )

        logger.info(
            "Sample collections returned: %s",
            len(collections)
        )

        return True

    # -----------------------------------------------------
    # LOGOUT / CLEANUP
    # -----------------------------------------------------

    def close(self):
        """
        Close the HTTP session and clear in-memory state.
        """

        self.session.close()

        self.authenticated = False
        self.token = None

        logger.info(
            "Earthdata session closed."
        )


# ---------------------------------------------------------
# MAIN TEST
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("NASA EARTHDATA AUTHENTICATION")
    print("=" * 60)

    auth = EarthdataAuth()

    try:

        auth.authenticate()

        print("\nAuthentication successful.")

        auth.test_connection()

        print(
            "\nNASA Earthdata connection test completed."
        )

    except Exception as error:

        logger.error(
            "Authentication test failed: %s",
            error
        )

        raise SystemExit(1)

    finally:

        auth.close()


if __name__ == "__main__":
    main()

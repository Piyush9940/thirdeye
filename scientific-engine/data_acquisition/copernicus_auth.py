
"""
Copernicus Data Space Ecosystem Authentication

Purpose:
    Authenticate with CDSE using OAuth2 password grant
    and obtain an access token for Sentinel data access.

Environment variables:
    COPERNICUS_USERNAME
    COPERNICUS_PASSWORD
"""

import os
import sys
import requests

from dotenv import load_dotenv


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

load_dotenv()

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"

USERNAME = os.getenv("COPERNICUS_USERNAME")
PASSWORD = os.getenv("COPERNICUS_PASSWORD")

TIMEOUT = 30


# ---------------------------------------------------------
# AUTHENTICATION CLASS
# ---------------------------------------------------------

class CopernicusAuth:

    def __init__(self):
        self.access_token = None
        self.session = requests.Session()

    def authenticate(self):
        """
        Authenticate with Copernicus and retrieve OAuth2 token.
        """

        if not USERNAME or not PASSWORD:
            raise ValueError(
                "Copernicus credentials not found. "
                "Add COPERNICUS_USERNAME and "
                "COPERNICUS_PASSWORD to your .env file."
            )

        payload = {
            "client_id": "cdse-public",
            "username": USERNAME,
            "password": PASSWORD,
            "grant_type": "password"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(
                TOKEN_URL,
                data=payload,
                headers=headers,
                timeout=TIMEOUT
            )

            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get("access_token")

            if not self.access_token:
                raise RuntimeError(
                    "Authentication succeeded but no access token "
                    "was returned."
                )

            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}"
            })

            print("Copernicus authentication successful.")

            return self.access_token

        except requests.exceptions.HTTPError as error:
            status = error.response.status_code

            if status == 401:
                raise RuntimeError(
                    "Authentication failed. Check your username "
                    "and password."
                ) from error

            raise RuntimeError(
                f"Copernicus authentication HTTP error: {status}"
            ) from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(
                f"Unable to connect to Copernicus: {error}"
            ) from error

    # -----------------------------------------------------
    # TOKEN MANAGEMENT
    # -----------------------------------------------------

    def get_token(self):
        """
        Return the current token.
        Authenticate automatically if no token exists.
        """

        if not self.access_token:
            self.authenticate()

        return self.access_token

    # -----------------------------------------------------
    # AUTHENTICATED REQUEST
    # -----------------------------------------------------

    def get(self, url, params=None):
        """
        Make an authenticated GET request.
        """

        self.get_token()

        response = self.session.get(
            url,
            params=params,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        return response

    # -----------------------------------------------------
    # CATALOGUE CONNECTION TEST
    # -----------------------------------------------------

    def test_connection(self):
        """
        Test authenticated access to the CDSE catalogue.
        """

        print("\nTesting Copernicus catalogue connection...")

        response = self.get(
            f"{CATALOGUE_URL}/Products",
            params={"$top": 1}
        )

        data = response.json()

        print("Catalogue connection successful.")

        products = data.get("value", [])

        if products:
            print("Sample product:", products[0].get("Name"))
        else:
            print("No sample products returned.")

        return True


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 55)
    print("COPERNICUS DATA SPACE AUTHENTICATION")
    print("=" * 55)

    try:
        copernicus = CopernicusAuth()

        copernicus.authenticate()
        copernicus.test_connection()

        print("\nAuthentication test completed successfully.")

    except (ValueError, RuntimeError, requests.exceptions.RequestException) as error:
        print(f"\nERROR: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()

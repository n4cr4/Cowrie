import os, sys
import json
import time
from datetime import datetime, timedelta, timezone
from logging import INFO, getLogger, basicConfig
from pathlib import Path
from typing import Any

import requests

# Get API key from environment variable
API_KEY = str(os.getenv("API_KEY"))
if not API_KEY:
    raise ValueError("Environment variable 'API_KEY' is not set.")
HASH_LIST_PATH: Path = Path("download_hash.json")
DOWNLOAD_DIR: Path = Path("vt_reports")
DOWNLOAD_DIR.mkdir(exist_ok=True)
VT_API_URL: str = "https://www.virustotal.com/api/v3/files/"

# Initialize logger
formatter = "%(asctime)s - %(levelname)8s - %(message)s"
basicConfig(stream=sys.stdout, format=formatter, level=INFO)
logger = getLogger(__name__)


def call_vt_api(sha256: str) -> dict[str, Any] | None:
    """Call the VirusTotal API and return the response."""
    headers: dict[str, str] = {"x-apikey": API_KEY}
    logger.info(f"Requesting {sha256}")

    # Send a request to VirusTotal
    response = requests.get(VT_API_URL + sha256, headers=headers)

    # Handle successful response
    if response.status_code == 200:
        return response.json()
    # Handle QuotaExceededError
    elif response.status_code == 429:
        logger.warning("Quota exceeded... waiting until UTC midnight to request again.")
        wait_until_utc_midnight()  # Wait until next UTC midnight
        return call_vt_api(sha256)  # Retry the request
    else:
        logger.error(f"Error: {response.status_code} {response.text}")
        return None


def wait_until_utc_midnight() -> None:
    """Wait until UTC midnight."""
    now: datetime = datetime.now(timezone.utc)
    tomorrow: datetime = now + timedelta(days=1)
    midnight: datetime = datetime(
        year=tomorrow.year,
        month=tomorrow.month,
        day=tomorrow.day,
        hour=0,
        minute=0,
        second=0,
        tzinfo=timezone.utc,
    )

    # Calculate the number of seconds to wait until midnight
    wait_seconds: int = (midnight - now).seconds
    time.sleep(wait_seconds)


def main() -> None:
    with HASH_LIST_PATH.open("r") as f:
        loaded_json = json.load(f)
        for sha256, _ in loaded_json["download_files"].items():
            response: dict[str, Any] | None = call_vt_api(sha256)

            # Skip if the response is None (indicating an error or quota exceeded)
            if response is None:
                continue

            # Save the response to a file
            file_path: Path = DOWNLOAD_DIR.joinpath(sha256 + ".json")
            with file_path.open("w") as f:
                json.dump(response, f, indent=4)  # Pretty print the JSON
                logger.info(f"Saved {sha256}.json")

            # Wait for 15 seconds to avoid hitting the rate limit
            time.sleep(15)


if __name__ == "__main__":
    logger.info("Start")
    main()
    logger.info("End")

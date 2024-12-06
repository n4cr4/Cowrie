import os, sys
import json
import time
from datetime import datetime, timedelta, timezone
from logging import INFO, getLogger, basicConfig
from pathlib import Path
from typing import Any

import requests

API_KEY = str(os.getenv("API_KEY"))
if not API_KEY:
    raise ValueError("環境変数 'API_KEY' が設定されていません。")
HASH_LIST_PATH: Path = Path("download.txt")
DOWNLOAD_DIR: Path = Path("vt_reports")
DOWNLOAD_DIR.mkdir(exist_ok=True)
VT_API_URL: str = "https://www.virustotal.com/api/v3/files/"

# init logger
formatter ="%(asctime)s - %(levelname)8s - %(message)s"
basicConfig(
    stream=sys.stdout,
    format=formatter,
    level=INFO
)
logger = getLogger(__name__)


def call_vt_api(sha256: str) -> dict[str, Any] | None:
    """Call VirusTotal API and return the response."""

    headers: dict[str, str] = {"x-apikey": API_KEY}
    logger.info(f"requesting {sha256}")
    # request to VirusTotal
    response = requests.get(VT_API_URL + sha256, headers=headers)

    # handle success
    if response.status_code == 200:
        return response.json()
    # handle QuotaExceededError
    elif response.status_code == 429:
        logger.warning(
            "QuotaExceededError... waiting until UTC 00:00 to request again"
        )
        wait_until_utc_midnight()
        return call_vt_api(sha256)  # retry
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
    # calculate wait seconds
    wait_seconds: int = (midnight - now).seconds
    time.sleep(wait_seconds)


def main() -> None:
    with HASH_LIST_PATH.open("r") as f:
        for line in f:
            sha256: str = line.strip().strip('"')
            response: dict[str, Any] | None = call_vt_api(sha256)

            if response is None:
                continue

            # Save the response to a file
            file_path: Path = DOWNLOAD_DIR.joinpath(sha256 + ".json")
            with file_path.open("w") as f:
                f.write(json.dumps(response))
                logger.info(f"saved {sha256}.json")

            time.sleep(15)  # 4 requests per minute


if __name__ == "__main__":
    logger.info("start")
    main()
    logger.info("end")

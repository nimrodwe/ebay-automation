import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://www.ebay.com")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
DATA_DIR = Path(__file__).parent.parent / "data"
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
TRACES_DIR = Path(__file__).parent.parent / "traces"

with open(DATA_DIR / "search_data.json", encoding="utf-8") as file:
    SEARCH_DATA = json.load(file)


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str = field(repr=False)


def get_credentials() -> Credentials | None:
    username = os.getenv("EBAY_USER")
    password = os.getenv("EBAY_PASS")
    if username and password:
        return Credentials(username, password)
    return None

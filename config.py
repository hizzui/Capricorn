"""
Bot configuration and JSON storage helpers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "").strip()
    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Moderation settings
    WARN_LIMIT: int = 3
    MUTE_ROLE_NAME: str = "Mutado"

    # Economy settings
    STARTING_BALANCE: int = 100
    PAYDAY_AMOUNT: int = 100
    PAYDAY_COOLDOWN_HOURS: int = 24
    SLOTS_MIN_BET: int = 10
    SLOTS_MAX_BET: int = 1000

    # Local JSON state files
    MODERATION_FILE: Path = DATA_DIR / "moderation.json"
    ECONOMY_FILE: Path = DATA_DIR / "economy.json"


def load_json(path: Path, default: Any) -> Any:
    """Load JSON data from disk or return a fresh copy of `default`."""
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(default))


def save_json(path: Path, data: Any) -> None:
    """Write JSON data to disk via a temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    tmp.replace(path)

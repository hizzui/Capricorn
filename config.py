"""
Core configuration, embed builder, and atomic JSON persistence utilities for Capricorn.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import discord
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "").strip()
    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Bot identity
    BOT_NAME: str = "Capricorn"
    BOT_VERSION: str = "v2.0.0"

    # Embed color palette
    COLOR_PRIMARY: int = 0xFF2A6D   # Capricorn Crimson
    COLOR_SUCCESS: int = 0x00E676   # Emerald Green
    COLOR_WARNING: int = 0xFFB300   # Amber Warning
    COLOR_ERROR: int = 0xFF1744     # Crimson Error
    COLOR_GOLD: int = 0xFFD700      # Gold

    # Moderation settings
    WARN_LIMIT: int = 3
    MUTE_ROLE_NAME: str = "Muted"

    # Economy settings
    STARTING_BALANCE: int = 100
    PAYDAY_AMOUNT: int = 100
    PAYDAY_COOLDOWN_HOURS: int = 24
    SLOTS_MIN_BET: int = 10
    SLOTS_MAX_BET: int = 1000

    # Local JSON state files
    MODERATION_FILE: Path = DATA_DIR / "moderation.json"
    ECONOMY_FILE: Path = DATA_DIR / "economy.json"


def build_embed(
    title: str,
    description: Optional[str] = None,
    *,
    color: int = Config.COLOR_PRIMARY,
    footer: Optional[str] = None,
) -> discord.Embed:
    """Create a standardized Discord embed with consistent Capricorn styling."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color(color),
        timestamp=datetime.now(timezone.utc),
    )
    footer_text = f"{Config.BOT_NAME} • {footer}" if footer else Config.BOT_NAME
    embed.set_footer(text=footer_text)
    return embed


def load_json(path: Path, default: Any) -> Any:
    """Load JSON data from disk or return a fresh deep copy of `default`."""
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(default))


def save_json(path: Path, data: Any) -> None:
    """Atomically write JSON data to disk via a temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    tmp.replace(path)

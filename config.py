"""
Runtime configuration and file paths for NewDiscordBot.
Reads environment variables from `.env` and exposes typed constants used across cogs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv()

BASE_DIR: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = BASE_DIR / "data"


class Config:
    # Core Discord settings
    DISCORD_TOKEN: Final[str] = os.getenv("DISCORD_TOKEN", "").strip()
    COMMAND_PREFIX: Final[str] = os.getenv("COMMAND_PREFIX", "!")
    BOT_NAME: Final[str] = "NDB Bot"
    BOT_VERSION: Final[str] = "1.1.0"

    INTENTS_MESSAGE_CONTENT: Final[bool] = True
    INTENTS_VOICE_STATES: Final[bool] = True
    INTENTS_MEMBERS: Final[bool] = True

    # Optional Twitch Helix API integration (used by cogs.streams)
    TWITCH_CLIENT_ID: Final[str] = os.getenv("TWITCH_CLIENT_ID", "").strip()
    TWITCH_CLIENT_SECRET: Final[str] = os.getenv("TWITCH_CLIENT_SECRET", "").strip()
    TWITCH_TOKEN: Final[str] = os.getenv("TWITCH_TOKEN", "").strip()
    TWITCH_CHECK_INTERVAL: Final[int] = int(os.getenv("TWITCH_CHECK_INTERVAL", "15"))

    # Timeouts & cooldowns (seconds)
    HELP_MENU_TIMEOUT: Final[int] = 300
    REACTION_TIMEOUT: Final[int] = 300
    TRIVIA_QUESTION_TIMEOUT: Final[float] = 10.0
    TRIVIA_QUESTIONS_PER_ROUND: Final[int] = 5
    PAYDAY_COOLDOWN_HOURS: Final[int] = 24

    # Economy parameters
    STARTING_BALANCE: Final[int] = 100
    PAYDAY_AMOUNT: Final[int] = 100
    SLOTS_MIN_BET: Final[int] = 10
    SLOTS_MAX_BET: Final[int] = 1000
    SLOTS_JACKPOT_MULTIPLIER: Final[int] = 20
    SLOTS_PAIR_MULTIPLIER: Final[int] = 2

    # Moderation defaults
    WARN_LIMIT: Final[int] = 3
    MUTE_ROLE_NAME: Final[str] = "Mutado"

    # Logging
    LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: Final[Path] = BASE_DIR / "bot.log"
    LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Local JSON persistence files
    MODERATION_FILE: Final[Path] = DATA_DIR / "moderation.json"
    ECONOMY_FILE: Final[Path] = DATA_DIR / "economy.json"
    CUSTOMCOM_FILE: Final[Path] = DATA_DIR / "custom_commands.json"
    STREAMS_FILE: Final[Path] = DATA_DIR / "streams.json"
    TRIVIA_FILE: Final[Path] = DATA_DIR / "trivia_scores.json"

    @classmethod
    def ensure_directories(cls) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def has_twitch_credentials(cls) -> bool:
        return bool(cls.TWITCH_CLIENT_ID and cls.TWITCH_TOKEN)

    @classmethod
    def validate(cls) -> bool:
        """Check that required runtime credentials are present before connecting."""
        cls.ensure_directories()
        if not cls.DISCORD_TOKEN:
            return False
        return True

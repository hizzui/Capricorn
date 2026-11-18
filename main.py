"""
Entrypoint for NewDiscordBot.
Configures logging, initializes Discord intents, and loads the core Cogs.
"""

from __future__ import annotations

import asyncio
import logging
import sys

import discord
from discord.ext import commands

from config import BASE_DIR, Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logging.getLogger("discord").setLevel(logging.WARNING)
logger = logging.getLogger("ndb")


class NDBBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        cogs_dir = BASE_DIR / "cogs"
        for path in sorted(cogs_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            ext = f"cogs.{path.stem}"
            try:
                await self.load_extension(ext)
                logger.info("Loaded cog: %s", ext)
            except Exception as exc:
                logger.error("Failed to load %s: %s", ext, exc)

    async def on_ready(self) -> None:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Config.COMMAND_PREFIX}ajuda | {len(self.guilds)} servers",
        )
        await self.change_presence(activity=activity, status=discord.Status.idle)
        logger.info("Bot ready as %s (%d guilds)", self.user, len(self.guilds))


async def main() -> None:
    if not Config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set in environment or .env file.")
        sys.exit(1)

    bot = NDBBot()
    async with bot:
        await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")

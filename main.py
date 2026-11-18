"""
Application entrypoint for NewDiscordBot.
Initializes Discord gateway intents, dynamically loads Cog extensions from `cogs/`,
and manages guild presence updates.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import discord
from discord.ext import commands

from config import BASE_DIR, Config
from logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger("ndb.main")


class NDBBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = Config.INTENTS_MESSAGE_CONTENT
        intents.voice_states = Config.INTENTS_VOICE_STATES
        intents.members = Config.INTENTS_MEMBERS

        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,  # Replaced by custom !ajuda command in cogs.general
        )

    async def setup_hook(self) -> None:
        """Load all cog extensions before the gateway connection becomes active."""
        cogs_dir = BASE_DIR / "cogs"
        loaded, failed = 0, 0

        for path in sorted(cogs_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            ext_name = f"cogs.{path.stem}"
            try:
                await self.load_extension(ext_name)
                logger.info("Loaded extension: %s", ext_name)
                loaded += 1
            except Exception as exc:
                logger.error("Failed to load extension %s: %s", ext_name, exc)
                failed += 1

        logger.info("Extensions initialized (%d loaded, %d failed)", loaded, failed)

    async def refresh_presence(self) -> None:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Config.COMMAND_PREFIX}ajuda | {len(self.guilds)} servers",
        )
        await self.change_presence(activity=activity, status=discord.Status.idle)

    async def on_ready(self) -> None:
        await self.refresh_presence()
        total_members = sum(g.member_count or 0 for g in self.guilds)
        logger.info(
            "Connected as %s (ID: %s) across %d guilds (%d members)",
            self.user,
            self.user.id if self.user else "unknown",
            len(self.guilds),
            total_members,
        )

    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.refresh_presence()
        logger.info("Joined guild '%s' (id=%s, total=%d)", guild.name, guild.id, len(self.guilds))

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.refresh_presence()
        logger.info("Removed from guild '%s' (id=%s, total=%d)", guild.name, guild.id, len(self.guilds))


async def run_bot() -> None:
    if not Config.validate():
        logger.error("Missing DISCORD_TOKEN in environment or .env file.")
        sys.exit(1)

    if not Config.has_twitch_credentials():
        logger.info("Twitch credentials not set; background stream polling will stay idle.")

    bot = NDBBot()
    async with bot:
        try:
            await bot.start(Config.DISCORD_TOKEN)
        except discord.LoginFailure:
            logger.error("Discord authentication failed: invalid DISCORD_TOKEN.")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Shutdown requested via SIGINT.")

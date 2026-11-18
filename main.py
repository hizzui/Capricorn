"""
Entrypoint for Capricorn Discord Bot.
Configures logging, initializes Discord intents, loads Cogs, and handles command errors.
"""

from __future__ import annotations

import asyncio
import logging
import sys

import discord
from discord.ext import commands

from config import BASE_DIR, Config, build_embed

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logging.getLogger("discord").setLevel(logging.WARNING)
logger = logging.getLogger("capricorn")


class CapricornBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
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
            name=f"{Config.COMMAND_PREFIX}help | {len(self.guilds)} servers",
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
        logger.info("Capricorn ready as %s (%d guilds)", self.user, len(self.guilds))

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Centralized error handling for prefix commands."""
        if isinstance(error, commands.CommandNotFound):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = build_embed(
                title="Missing Permissions",
                description=f"You do not have the required permissions to run this command.\nRequired: {perms}",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = build_embed(
                title="Bot Missing Permissions",
                description=f"I need additional permissions to perform this action.\nMissing: {perms}",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            cmd_name = ctx.command.qualified_name if ctx.command else "command"
            usage = f"{Config.COMMAND_PREFIX}{cmd_name} {ctx.command.signature}".strip() if ctx.command else ""
            embed = build_embed(
                title="Missing Argument",
                description=f"Missing required parameter `{error.param.name}`.\nUsage: `{usage}`",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, (commands.BadArgument, commands.UserNotFound, commands.MemberNotFound)):
            embed = build_embed(
                title="Invalid Argument",
                description="Could not parse the provided arguments. Please check the member mention or number format.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        logger.error("Unhandled error in command '%s': %s", ctx.command, error, exc_info=True)


async def main() -> None:
    if not Config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set in environment or .env file.")
        sys.exit(1)

    bot = CapricornBot()
    async with bot:
        await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")

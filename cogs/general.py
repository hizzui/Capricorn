"""
General utility commands, server/member inspection, and help menu.
"""

from __future__ import annotations

import random
from typing import Optional

import discord
from discord.ext import commands

from config import Config, build_embed


class General(commands.Cog):
    """General utilities, server/member inspection, and command reference."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Check current gateway latency."""
        ms = round(self.bot.latency * 1000)
        embed = build_embed(
            title="Pong",
            description=f"Gateway latency: **{ms}ms**",
            color=Config.COLOR_PRIMARY,
        )
        await ctx.send(embed=embed)

    @commands.command(name="roll", aliases=["dice", "dado"])
    async def roll(self, ctx: commands.Context, sides: int = 6) -> None:
        """Roll an N-sided die (default: 6)."""
        if not 2 <= sides <= 1000:
            embed = build_embed(
                title="Invalid Range",
                description="Please choose between **2** and **1000** sides.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        result = random.randint(1, sides)
        embed = build_embed(
            title=f"Dice Roll (d{sides})",
            description=f"Result: **{result}**",
            color=Config.COLOR_PRIMARY,
        )
        await ctx.send(embed=embed)

    @commands.command(name="coinflip", aliases=["flip", "coin", "moeda"])
    async def coinflip(self, ctx: commands.Context) -> None:
        """Flip a coin."""
        side = "Heads" if random.random() >= 0.5 else "Tails"
        embed = build_embed(
            title="Coin Flip",
            description=f"Result: **{side}**",
            color=Config.COLOR_PRIMARY,
        )
        await ctx.send(embed=embed)

    @commands.command(name="poll", aliases=["vote"])
    async def poll(self, ctx: commands.Context, *, question: str) -> None:
        """Create a quick thumbs-up / thumbs-down poll."""
        embed = build_embed(
            title="Poll",
            description=question,
            color=Config.COLOR_PRIMARY,
            footer=f"Started by {ctx.author.display_name}",
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command(name="user", aliases=["userinfo", "whois"])
    async def user(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Show profile details and roles for a server member."""
        target = member or ctx.author
        embed = build_embed(
            title=f"User Profile — {target.display_name}",
            color=Config.COLOR_PRIMARY,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Username", value=f"`@{target.name}`", inline=True)
        embed.add_field(
            name="Account Created",
            value=target.created_at.strftime("%Y-%m-%d"),
            inline=True,
        )

        if isinstance(target, discord.Member) and target.joined_at:
            embed.add_field(
                name="Joined Server",
                value=target.joined_at.strftime("%Y-%m-%d"),
                inline=True,
            )
            roles = [r.mention for r in reversed(target.roles) if r != ctx.guild.default_role]
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=", ".join(roles[:12]) if roles else "None",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="server", aliases=["serverinfo", "servidor"])
    async def server(self, ctx: commands.Context) -> None:
        """Show summary statistics for the current Discord server."""
        guild = ctx.guild
        if guild is None:
            return

        embed = build_embed(
            title=guild.name,
            color=Config.COLOR_PRIMARY,
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Owner",
            value=guild.owner.mention if guild.owner else "N/A",
            inline=True,
        )
        embed.add_field(
            name="Created",
            value=guild.created_at.strftime("%Y-%m-%d"),
            inline=True,
        )
        embed.add_field(name="Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(
            name="Channels (Text / Voice)",
            value=f"{len(guild.text_channels)} / {len(guild.voice_channels)}",
            inline=True,
        )
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Display a member's full-size avatar."""
        target = member or ctx.author
        embed = build_embed(
            title=f"Avatar — {target.display_name}",
            color=Config.COLOR_PRIMARY,
        )
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="help", aliases=["commands", "ajuda", "comandos"])
    async def help_cmd(self, ctx: commands.Context) -> None:
        """List all available bot commands grouped by category."""
        p = Config.COMMAND_PREFIX
        embed = build_embed(
            title="Capricorn — Command Reference",
            description=f"Available commands (default prefix `{p}`):",
            color=Config.COLOR_PRIMARY,
            footer=Config.BOT_VERSION,
        )
        embed.add_field(
            name="General & Utilities",
            value=(
                f"`{p}ping` — Check gateway latency\n"
                f"`{p}user [@member]` — View member profile and roles\n"
                f"`{p}server` — View server statistics\n"
                f"`{p}avatar [@member]` — Display full-size avatar\n"
                f"`{p}roll [sides]` · `{p}coinflip` · `{p}poll <question>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Economy",
            value=(
                f"`{p}balance [@member]` — Check credit balance\n"
                f"`{p}payday` — Claim daily credits (24h cooldown)\n"
                f"`{p}pay <@member> <amount>` — Transfer credits to a member\n"
                f"`{p}slots [bet]` — Bet credits on the slot machine\n"
                f"`{p}leaderboard` — View top 10 credit holders"
            ),
            inline=False,
        )
        embed.add_field(
            name="Moderation",
            value=(
                f"`{p}kick <@member> [reason]` — Kick a member\n"
                f"`{p}ban <@member> [reason]` — Ban a member\n"
                f"`{p}unban <id|username>` — Revoke a user ban\n"
                f"`{p}mute <@member> [reason]` / `{p}unmute <@member>` — Mute or unmute a member\n"
                f"`{p}warn <@member> [reason]` — Issue a warning (auto-ban at {Config.WARN_LIMIT} warnings)\n"
                f"`{p}warnings [@member]` · `{p}unwarn <@member>` — View or remove warnings\n"
                f"`{p}clear [count]` (`{p}purge`) — Bulk-delete recent channel messages"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))

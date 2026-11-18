"""
Moderation and channel cleanup cog.
Includes kick, ban, unban, mute/unmute, 3-strike warning system, and bulk message clear.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config, build_embed, load_json, save_json


class Moderation(commands.Cog):
    """Server moderation and bulk message cleanup commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.MODERATION_FILE
        self.state: Dict[str, Any] = load_json(self.file_path, default={"users": {}})

    def _persist(self) -> None:
        save_json(self.file_path, self.state)

    @staticmethod
    def _check_hierarchy(ctx: commands.Context, target: discord.Member) -> Optional[discord.Embed]:
        if target.id == ctx.author.id:
            return build_embed(
                title="Action Denied",
                description="You cannot perform this moderation action on yourself.",
                color=Config.COLOR_ERROR,
            )
        if ctx.guild and target.id == ctx.guild.owner_id:
            return build_embed(
                title="Action Denied",
                description="You cannot moderate the server owner.",
                color=Config.COLOR_ERROR,
            )
        if (
            isinstance(ctx.author, discord.Member)
            and ctx.guild
            and ctx.author.id != ctx.guild.owner_id
            and target.top_role >= ctx.author.top_role
        ):
            return build_embed(
                title="Insufficient Role Hierarchy",
                description="That member has a role equal to or higher than yours.",
                color=Config.COLOR_ERROR,
            )
        return None

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        """Kick a member from the server."""
        err = self._check_hierarchy(ctx, member)
        if err:
            await ctx.send(embed=err)
            return

        try:
            await member.kick(reason=f"{ctx.author}: {reason}")
            embed = build_embed(
                title="Member Kicked",
                description=f"**{member}** has been removed from the server.",
                color=Config.COLOR_WARNING,
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(embed=build_embed("Kick Failed", str(exc), color=Config.COLOR_ERROR))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        """Ban a member from the server."""
        err = self._check_hierarchy(ctx, member)
        if err:
            await ctx.send(embed=err)
            return

        try:
            await member.ban(reason=f"{ctx.author}: {reason}", delete_message_seconds=86400)
            embed = build_embed(
                title="Member Banned",
                description=f"**{member}** has been banned from the server.",
                color=Config.COLOR_ERROR,
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(embed=build_embed("Ban Failed", str(exc), color=Config.COLOR_ERROR))

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, user_query: str) -> None:
        """Unban a user by username or Discord ID."""
        query = user_query.strip().lower()
        async for entry in ctx.guild.bans():
            if entry.user.name.lower() == query or str(entry.user.id) == query:
                try:
                    await ctx.guild.unban(entry.user, reason=f"Unbanned by {ctx.author}")
                    embed = build_embed(
                        title="Member Unbanned",
                        description=f"Ban removed for **{entry.user}**.",
                        color=Config.COLOR_SUCCESS,
                    )
                    await ctx.send(embed=embed)
                    return
                except discord.HTTPException as exc:
                    await ctx.send(embed=build_embed("Unban Failed", str(exc), color=Config.COLOR_ERROR))
                    return

        await ctx.send(
            embed=build_embed(
                "User Not Found",
                f"No banned user matching `{user_query}` was found.",
                color=Config.COLOR_WARNING,
            )
        )

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        """Mute a member in text channels using the configured mute role."""
        err = self._check_hierarchy(ctx, member)
        if err:
            await ctx.send(embed=err)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None:
            try:
                muted_role = await ctx.guild.create_role(
                    name=Config.MUTE_ROLE_NAME,
                    reason="Mute role created by Capricorn",
                )
                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(muted_role, send_messages=False)
            except discord.HTTPException as exc:
                await ctx.send(
                    embed=build_embed(
                        "Role Creation Failed",
                        f"Could not create `{Config.MUTE_ROLE_NAME}` role: {exc}",
                        color=Config.COLOR_ERROR,
                    )
                )
                return

        try:
            await member.add_roles(muted_role, reason=f"{ctx.author}: {reason}")
            embed = build_embed(
                title="Member Muted",
                description=f"**{member.display_name}** has been muted.",
                color=Config.COLOR_WARNING,
            )
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(embed=build_embed("Mute Failed", str(exc), color=Config.COLOR_ERROR))

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member) -> None:
        """Remove the mute role from a member."""
        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None or muted_role not in member.roles:
            await ctx.send(
                embed=build_embed(
                    "Not Muted",
                    f"**{member.display_name}** is not currently muted.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        try:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")
            embed = build_embed(
                title="Member Unmuted",
                description=f"**{member.display_name}** has been unmuted.",
                color=Config.COLOR_SUCCESS,
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(embed=build_embed("Unmute Failed", str(exc), color=Config.COLOR_ERROR))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided",
    ) -> None:
        """Warn a member; reaching `Config.WARN_LIMIT` triggers an automatic ban."""
        err = self._check_hierarchy(ctx, member)
        if err:
            await ctx.send(embed=err)
            return

        users = self.state.setdefault("users", {})
        record = users.setdefault(str(member.id), {"warns": 0, "motivos": []})
        record["warns"] += 1
        record["motivos"].append(
            {
                "razao": reason,
                "moderador": str(ctx.author),
                "data": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            }
        )
        self._persist()

        count = int(record["warns"])
        embed = build_embed(
            title="Warning Issued",
            description=f"**{member.display_name}** received a warning (`{count}/{Config.WARN_LIMIT}`).",
            color=Config.COLOR_WARNING,
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await ctx.send(embed=embed)

        if count >= Config.WARN_LIMIT:
            try:
                await member.ban(reason=f"Reached {Config.WARN_LIMIT} warnings.")
                ban_embed = build_embed(
                    title="Automatic Ban Triggered",
                    description=f"**{member}** reached **{Config.WARN_LIMIT}** warnings and was banned.",
                    color=Config.COLOR_ERROR,
                )
                await ctx.send(embed=ban_embed)
            except discord.HTTPException:
                pass

    @commands.command()
    async def warnings(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """View warnings recorded for a member."""
        target = member or ctx.author
        record = self.state.get("users", {}).get(str(target.id))
        if not record or not record.get("warns"):
            embed = build_embed(
                title="Warnings",
                description=f"**{target.display_name}** has no recorded warnings.",
                color=Config.COLOR_SUCCESS,
            )
            await ctx.send(embed=embed)
            return

        embed = build_embed(
            title=f"Warnings — {target.display_name} ({record['warns']}/{Config.WARN_LIMIT})",
            color=Config.COLOR_WARNING,
        )
        for idx, item in enumerate(record.get("motivos", []), start=1):
            reason_text = item.get("razao") or item.get("reason", "N/A")
            mod_text = item.get("moderador") or item.get("moderator", "Unknown")
            embed.add_field(
                name=f"#{idx}",
                value=f"{reason_text} *(by {mod_text})*",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx: commands.Context, member: discord.Member) -> None:
        """Remove the latest warning from a member."""
        record = self.state.get("users", {}).get(str(member.id))
        if not record or record.get("warns", 0) <= 0:
            await ctx.send(
                embed=build_embed(
                    "No Warnings",
                    f"**{member.display_name}** has no warnings to remove.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        record["warns"] -= 1
        if record.get("motivos"):
            record["motivos"].pop()
        self._persist()

        embed = build_embed(
            title="Warning Removed",
            description=f"Removed the latest warning from **{member.display_name}** (`{record['warns']}/{Config.WARN_LIMIT}`).",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)

    @commands.command(name="clear", aliases=["purge", "clean"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, count: int = 20) -> None:
        """Bulk-delete up to `count` recent messages in the channel."""
        if not 1 <= count <= 200:
            await ctx.send(
                embed=build_embed(
                    "Invalid Amount",
                    "Please specify a number of messages between **1** and **200**.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        deleted = await ctx.channel.purge(limit=count + 1)
        removed_count = max(0, len(deleted) - 1)
        embed = build_embed(
            title="Channel Purged",
            description=f"Deleted **{removed_count}** messages.",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed, delete_after=4.0)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

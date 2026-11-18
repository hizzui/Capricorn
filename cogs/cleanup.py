"""
Channel message cleanup commands (`!purge`, `!clean`, `!cleanup`, `!clear`).
Handles both single-message iteration and chunked bulk deletion.
"""

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands


class Cleanup(commands.Cog):
    """Bulk message removal utilities for moderators."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(
        self,
        ctx: commands.Context,
        quantidade: int = 10,
        usuario: Optional[discord.User] = None,
    ) -> None:
        """Delete up to `quantidade` messages in the current channel, optionally filtered by user."""
        if not 1 <= quantidade <= 1000:
            await ctx.send("❌ Quantidade deve estar entre 1 e 1000.")
            return

        deleted = 0
        async for message in ctx.channel.history(limit=quantidade + 1):
            if usuario and message.author != usuario:
                continue
            try:
                await message.delete()
                deleted += 1
            except discord.HTTPException:
                continue

        embed = discord.Embed(
            title="✅ Limpeza concluída",
            description=f"**{deleted}** mensagens foram removidas.",
            color=discord.Color.green(),
        )
        if usuario:
            embed.add_field(name="Usuário filtrado", value=usuario.mention, inline=False)

        await ctx.send(embed=embed, delete_after=5.0)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx: commands.Context, quantidade: int = 10) -> None:
        """Remove messages authored by bots within the last `quantidade` messages."""
        if not 1 <= quantidade <= 1000:
            await ctx.send("❌ Quantidade deve estar entre 1 e 1000.")
            return

        deleted = 0
        async for message in ctx.channel.history(limit=quantidade + 1):
            if message.author.bot:
                try:
                    await message.delete()
                    deleted += 1
                except discord.HTTPException:
                    continue

        embed = discord.Embed(
            title="✅ Mensagens de bots removidas",
            description=f"**{deleted}** mensagens de bot foram deletadas.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed, delete_after=5.0)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx: commands.Context) -> None:
        """Scan the last 50 messages in the channel and remove messages sent by this bot."""
        deleted = 0
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user:
                try:
                    await message.delete()
                    deleted += 1
                except discord.HTTPException:
                    continue

        embed = discord.Embed(
            title="✅ Limpeza do bot",
            description=f"**{deleted}** mensagens do bot foram removidas.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed, delete_after=5.0)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def clear(self, ctx: commands.Context, quantidade: int = 100) -> None:
        """Bulk-delete up to `quantidade` messages in chunks of 100 (Discord API limit)."""
        if not 1 <= quantidade <= 1000:
            await ctx.send("❌ Quantidade deve estar entre 1 e 1000.")
            return

        targets = [
            msg
            async for msg in ctx.channel.history(limit=quantidade + 1)
            if msg.id != ctx.message.id
        ]

        # Discord bulk-delete endpoint accepts at most 100 messages per call
        # and rejects messages older than 14 days, falling back to single delete.
        for idx in range(0, len(targets), 100):
            batch = targets[idx : idx + 100]
            try:
                await ctx.channel.delete_messages(batch)
            except discord.HTTPException:
                for msg in batch:
                    try:
                        await msg.delete()
                    except discord.HTTPException:
                        continue

        embed = discord.Embed(
            title="✅ Canal limpo",
            description=f"**{len(targets)}** mensagens foram deletadas.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed, delete_after=5.0)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Cleanup(bot))

"""
Guild and member inspection commands (`!user`, `!servidor`, `!avatar`).
Safely handles users without custom avatars by falling back to `display_avatar`.
"""

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands


class Info(commands.Cog):
    """Server and member profile inspection embeds."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def user(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Display account age, join date, roles, and permissions for a guild member."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"Perfil de {target.display_name}",
            color=target.color if target.color != discord.Color.default() else discord.Color.green(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Usuário", value=f"`@{target.name}`", inline=True)
        embed.add_field(name="Bot", value="Sim" if target.bot else "Não", inline=True)
        embed.add_field(
            name="Conta criada em",
            value=target.created_at.strftime("%d/%m/%Y às %H:%M"),
            inline=True,
        )

        if isinstance(target, discord.Member) and target.joined_at:
            embed.add_field(
                name="Entrou no servidor",
                value=target.joined_at.strftime("%d/%m/%Y às %H:%M"),
                inline=True,
            )
            roles = [r.mention for r in target.roles if r != ctx.guild.default_role]
            embed.add_field(
                name=f"Cargos ({len(roles)})",
                value=", ".join(roles[:15]) if roles else "Nenhum cargo atribuído",
                inline=False,
            )
            embed.add_field(
                name="Administrador",
                value="Sim" if target.guild_permissions.administrator else "Não",
                inline=True,
            )

        embed.set_footer(
            text=f"Solicitado por {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def servidor(self, ctx: commands.Context) -> None:
        """Show structural statistics and boost status for the current guild."""
        guild = ctx.guild
        if guild is None:
            return

        embed = discord.Embed(
            title=f"Informações de {guild.name}",
            color=discord.Color.purple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        human_count = sum(1 for m in guild.members if not m.bot)
        bot_count = sum(1 for m in guild.members if m.bot)

        embed.add_field(name="ID do Servidor", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Proprietário",
            value=guild.owner.mention if guild.owner else "Desconhecido",
            inline=True,
        )
        embed.add_field(
            name="Criado em",
            value=guild.created_at.strftime("%d/%m/%Y"),
            inline=True,
        )
        embed.add_field(name="Membros Totais", value=str(guild.member_count), inline=True)
        embed.add_field(name="Humanos / Bots", value=f"{human_count} / {bot_count}", inline=True)
        embed.add_field(
            name="Canais (Texto / Voz)",
            value=f"{len(guild.text_channels)} / {len(guild.voice_channels)}",
            inline=True,
        )
        embed.add_field(name="Categorias", value=str(len(guild.categories)), inline=True)
        embed.add_field(name="Cargos", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Emojis", value=str(len(guild.emojis)), inline=True)
        embed.add_field(
            name="Nível de Boost",
            value=f"Nível {guild.premium_tier} ({guild.premium_subscription_count} boosts)",
            inline=True,
        )
        embed.add_field(
            name="Verificação",
            value=guild.verification_level.name.title(),
            inline=True,
        )

        embed.set_footer(
            text=f"Solicitado por {ctx.author}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Render the high-resolution avatar of a guild member."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"Avatar de {target.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info(bot))

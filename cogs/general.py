"""
General commands, server/member profile info, quick chat tools, and help menu.
"""

from __future__ import annotations

import random
from typing import Optional

import discord
from discord.ext import commands


class General(commands.Cog):
    """General utilities, server/member inspection, and help menu."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Check current gateway latency."""
        ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latência: **{ms}ms**")

    @commands.command()
    async def dado(self, ctx: commands.Context, lados: int = 6) -> None:
        """Roll an N-sided die (default: 6)."""
        if not 2 <= lados <= 1000:
            await ctx.send("❌ Escolha entre 2 e 1000 lados.")
            return
        await ctx.send(f"🎲 Resultado (d{lados}): **{random.randint(1, lados)}**")

    @commands.command()
    async def moeda(self, ctx: commands.Context) -> None:
        """Flip a coin."""
        lado = "Cara" if random.random() >= 0.5 else "Coroa"
        await ctx.send(f"🪙 **{lado}!**")

    @commands.command()
    async def vote(self, ctx: commands.Context, *, pergunta: str) -> None:
        """Create a quick thumbs-up / thumbs-down poll."""
        embed = discord.Embed(
            title="📊 Votação",
            description=pergunta,
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Criada por {ctx.author.display_name}")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command()
    async def user(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Show profile details and roles for a server member."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"Perfil de {target.display_name}",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="ID", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Usuário", value=f"`@{target.name}`", inline=True)
        embed.add_field(
            name="Conta criada",
            value=target.created_at.strftime("%d/%m/%Y"),
            inline=True,
        )

        if isinstance(target, discord.Member) and target.joined_at:
            embed.add_field(
                name="Entrou no servidor",
                value=target.joined_at.strftime("%d/%m/%Y"),
                inline=True,
            )
            roles = [r.mention for r in target.roles if r != ctx.guild.default_role]
            embed.add_field(
                name=f"Cargos ({len(roles)})",
                value=", ".join(roles[:12]) if roles else "Nenhum cargo",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def servidor(self, ctx: commands.Context) -> None:
        """Show summary stats for the current Discord server."""
        guild = ctx.guild
        if guild is None:
            return

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.purple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Dono",
            value=guild.owner.mention if guild.owner else "N/A",
            inline=True,
        )
        embed.add_field(
            name="Criado em",
            value=guild.created_at.strftime("%d/%m/%Y"),
            inline=True,
        )
        embed.add_field(name="Membros", value=str(guild.member_count), inline=True)
        embed.add_field(
            name="Canais (Texto / Voz)",
            value=f"{len(guild.text_channels)} / {len(guild.voice_channels)}",
            inline=True,
        )
        embed.add_field(name="Cargos", value=str(len(guild.roles)), inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Display a member's full-size avatar."""
        target = member or ctx.author
        embed = discord.Embed(
            title=f"Avatar de {target.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="ajuda", aliases=["help", "comandos"])
    async def ajuda(self, ctx: commands.Context) -> None:
        """List all available bot commands grouped by category."""
        embed = discord.Embed(
            title="📚 Comandos — NDB Bot",
            description="Lista de comandos disponíveis (prefixo padrão `!`):",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="🔧 Geral & Servidor",
            value=(
                "`!ping` — Latência do bot\n"
                "`!user [@membro]` — Informações de perfil\n"
                "`!servidor` — Estatísticas do servidor\n"
                "`!avatar [@membro]` — Avatar ampliado\n"
                "`!dado [lados]` · `!moeda` · `!vote <pergunta>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="💰 Economia",
            value=(
                "`!balance [@membro]` — Consulta saldo\n"
                "`!payday` — Resgata créditos diários (24h)\n"
                "`!pay <@membro> <valor>` — Transfere créditos\n"
                "`!slots [aposta]` — Joga no caça-níqueis\n"
                "`!leaderboard` — Ranking dos maiores saldos"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔨 Moderação",
            value=(
                "`!kick <@membro> [razão]` — Expulsa membro\n"
                "`!ban <@membro> [razão]` — Bane membro\n"
                "`!unban <id|nome>` — Remove banimento\n"
                "`!mute <@membro>` / `!unmute <@membro>` — Silencia membro\n"
                "`!warn <@membro> [razão]` · `!warnings [@membro]` · `!unwarn <@membro>`\n"
                "`!clear [quantidade]` (`!purge`) — Limpa mensagens do canal"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))

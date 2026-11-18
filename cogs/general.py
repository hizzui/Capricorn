"""
General utility commands (`!ping`, `!oi`, `!echo`) and the custom `!ajuda` (`!help`) embed.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

logger = logging.getLogger("ndb.general")


class General(commands.Cog):
    """Core bot diagnostics and command reference menu."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="ping", brief="Display gateway latency")
    async def ping(self, ctx: commands.Context) -> None:
        """Return current WebSocket gateway latency in milliseconds."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latência: **{latency_ms}ms**")

    @commands.command(name="oi", brief="Greet the user")
    async def oi(self, ctx: commands.Context) -> None:
        """Send a quick greeting mentioning the caller."""
        await ctx.send(f"Olá, {ctx.author.mention}! 👋")

    @commands.command(name="echo", brief="Repeat a text message")
    async def echo(self, ctx: commands.Context, *, texto: str) -> None:
        """Echo back the provided message string with mass mentions escaped."""
        safe_text = discord.utils.escape_mentions(texto)
        await ctx.send(safe_text)

    @commands.command(
        name="ajuda",
        aliases=["help", "comandos"],
        brief="Display the categorized command overview",
    )
    async def ajuda(self, ctx: commands.Context) -> None:
        """Render the categorized embed of all bot commands."""
        embed = discord.Embed(
            title="📚 Central de Comandos — NDB Bot",
            description="Lista de comandos agrupados por módulo. O prefixo padrão é `!`.",
            color=discord.Color.blue(),
        )

        sections = [
            (
                "🔧 Gerais",
                "`!ping` · `!oi` · `!echo <texto>` · `!ajuda`",
            ),
            (
                "🎲 Diversão & Utilidades",
                "`!dado [lados]` · `!moeda` · `!vote <pergunta>` · `!calc <expressão>`",
            ),
            (
                "💰 Economia",
                "`!balance [@user]` · `!pay <@user> <valor>` · `!slots [aposta]` · `!payday` · `!leaderboard`",
            ),
            (
                "ℹ️ Informações",
                "`!user [@user]` · `!servidor` · `!avatar [@user]`",
            ),
            (
                "🔨 Moderação",
                "`!kick <@user> [razão]` · `!ban <@user> [razão]` · `!unban <id|nome>`\n"
                "`!mute <@user>` · `!unmute <@user>` · `!warn <@user> [razão]` · `!warnings [@user]` · `!unwarn <@user>`",
            ),
            (
                "🧹 Limpeza de Canal",
                "`!purge [qtd] [@user]` · `!clean [qtd]` · `!cleanup` · `!clear [qtd]`",
            ),
            (
                "🎯 Trivia",
                "`!trivia` · `!trivia_score [@user]` · `!trivia_top`",
            ),
            (
                "📺 Monitoramento Twitch",
                "`!streamset channel <#canal>` · `!streamset show` · `!streamset credentials`\n"
                "`!stream add twitch <canal>` · `!stream remove <canal>` · `!stream list` · `!stream check <canal>`",
            ),
            (
                "⚙️ Comandos Personalizados",
                "`!customcom create <nome> <resposta>` · `!customcom list` · `!customcom show <nome>` · `!customcom delete <nome>`",
            ),
        ]

        for title, body in sections:
            embed.add_field(name=title, value=body, inline=False)

        requester_avatar = ctx.author.display_avatar.url if ctx.author.display_avatar else None
        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=requester_avatar)

        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))

"""
Per-guild custom text commands (`!customcom create|list|delete|show`).
Supports lightweight template placeholders (`{author}`, `{guild}`, `{timestamp}`).
"""

from __future__ import annotations

from typing import Any, Dict

import discord
from discord.ext import commands

from config import Config
from utils.storage import load_json, save_json


class CustomCom(commands.Cog):
    """Guild-scoped custom text triggers managed by server staff."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.CUSTOMCOM_FILE
        self.store: Dict[str, Dict[str, Any]] = load_json(self.file_path, default={})

    def _persist(self) -> None:
        save_json(self.file_path, self.store)

    @commands.group(invoke_without_command=True)
    async def customcom(self, ctx: commands.Context) -> None:
        """Display available custom command management subcommands."""
        embed = discord.Embed(
            title="🛠️ Comandos Personalizados",
            description="Subcomandos disponíveis para este servidor:",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Uso",
            value=(
                "`!customcom create <nome> <resposta>` — Cria um comando\n"
                "`!customcom list` — Lista os comandos do servidor\n"
                "`!customcom show <nome>` — Exibe o texto bruto de um comando\n"
                "`!customcom delete <nome>` — Remove um comando"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @customcom.command()
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx: commands.Context, nome: str, *, resposta: str) -> None:
        """Register a new custom trigger for the current guild."""
        trigger = nome.lower().lstrip(Config.COMMAND_PREFIX)
        if len(trigger) < 2:
            await ctx.send("❌ O nome do comando deve ter pelo menos 2 caracteres.")
            return

        if len(resposta) > 2000:
            await ctx.send("❌ A resposta excede o limite de 2000 caracteres do Discord.")
            return

        # Prevent shadowing built-in bot commands
        if self.bot.get_command(trigger):
            await ctx.send(f"❌ `@{trigger}` já é um comando nativo do bot.")
            return

        guild_key = str(ctx.guild.id)
        guild_cmds = self.store.setdefault(guild_key, {})

        if trigger in guild_cmds:
            await ctx.send(f"❌ O comando `!{trigger}` já existe neste servidor.")
            return

        guild_cmds[trigger] = {
            "resposta": resposta,
            "criado_por": str(ctx.author),
            "criado_em": ctx.message.created_at.isoformat(),
        }
        self._persist()

        embed = discord.Embed(
            title="✅ Comando criado",
            description=f"Use `!{trigger}` para acionar a resposta.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @customcom.command(name="list")
    async def list_commands(self, ctx: commands.Context) -> None:
        """List custom commands registered in the current guild."""
        guild_cmds = self.store.get(str(ctx.guild.id), {})
        if not guild_cmds:
            await ctx.send("Nenhum comando personalizado registrado neste servidor.")
            return

        names = sorted(guild_cmds.keys())
        embed = discord.Embed(
            title="📋 Comandos Personalizados",
            description=f"Total registrado: **{len(names)}**",
            color=discord.Color.blue(),
        )

        for name in names[:20]:
            meta = guild_cmds[name]
            embed.add_field(
                name=f"!{name}",
                value=f"Criado por: {meta.get('criado_por', 'desconhecido')}",
                inline=False,
            )

        if len(names) > 20:
            embed.set_footer(text=f"Exibindo 20 de {len(names)} comandos.")

        await ctx.send(embed=embed)

    @customcom.command()
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx: commands.Context, nome: str) -> None:
        """Delete an existing custom command."""
        trigger = nome.lower().lstrip(Config.COMMAND_PREFIX)
        guild_cmds = self.store.get(str(ctx.guild.id), {})

        if trigger not in guild_cmds:
            await ctx.send(f"❌ Comando `!{trigger}` não encontrado.")
            return

        del guild_cmds[trigger]
        self._persist()

        embed = discord.Embed(
            title="✅ Comando removido",
            description=f"O comando `!{trigger}` foi excluído.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @customcom.command(name="show")
    async def show_com(self, ctx: commands.Context, nome: str) -> None:
        """Inspect the template text and author of a custom command."""
        trigger = nome.lower().lstrip(Config.COMMAND_PREFIX)
        guild_cmds = self.store.get(str(ctx.guild.id), {})

        if trigger not in guild_cmds:
            await ctx.send(f"❌ Comando `!{trigger}` não encontrado.")
            return

        info = guild_cmds[trigger]
        embed = discord.Embed(
            title=f"!{trigger}",
            description=info["resposta"],
            color=discord.Color.purple(),
        )
        embed.set_footer(text=f"Criado por {info.get('criado_por', 'desconhecido')}")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Intercept prefixed messages that match a guild's custom command table."""
        if message.author.bot or not message.guild:
            return

        if not message.content.startswith(Config.COMMAND_PREFIX):
            return

        tokens = message.content[len(Config.COMMAND_PREFIX) :].split()
        if not tokens:
            return

        trigger = tokens[0].lower()
        guild_cmds = self.store.get(str(message.guild.id), {})
        entry = guild_cmds.get(trigger)
        if not entry:
            return

        rendered = (
            entry["resposta"]
            .replace("{author}", message.author.mention)
            .replace("{guild}", message.guild.name)
            .replace("{timestamp}", message.created_at.strftime("%d/%m/%Y %H:%M"))
        )
        await message.channel.send(rendered)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CustomCom(bot))

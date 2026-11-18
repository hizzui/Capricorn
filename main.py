"""
Entrypoint para CAPRICORN // SYS-ENGRAM (Project Capricorn — Cyberpunk 2).
Configura telemetria de logs, inicializa Intents, carrega Cogs e gerencia erros globais.
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
logger = logging.getLogger("capricorn.core")


class CapricornBot(commands.Bot):
    """Instância principal do construto neural Capricorn."""

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
                logger.info("[SYS-ENGRAM] Módulo carregado: %s", ext)
            except Exception as exc:
                logger.error("[BREACH] Falha ao carregar módulo %s: %s", ext, exc)

    async def on_ready(self) -> None:
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"BLACKWALL TELEMETRY // {Config.COMMAND_PREFIX}ajuda",
        )
        await self.change_presence(activity=activity, status=discord.Status.dnd)
        logger.info(
            "[ONLINE] Construto %s ativo em %d sub-redes (servidores)",
            self.user,
            len(self.guilds),
        )

    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Tratamento centralizado e profissional de exceções de comandos."""
        if isinstance(error, commands.CommandNotFound):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = build_embed(
                title="⛔ ACESSO NEGADO // CREDENCIAL INSUFICIENTE",
                description=(
                    "Seu nível de autorização corporativa não permite executar este protocolo.\n"
                    f"**Permissões exigidas:** {perms}"
                ),
                color=Config.COLOR_ERROR,
                footer_extra="ICE SECURITY PROTOCOL",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = build_embed(
                title="⚠️ FALHA DE EXECUÇÃO // PERMISSÃO DE SISTEMA",
                description=(
                    "O construto **Capricorn** não possui privilégios suficientes nesta sub-rede.\n"
                    f"**Permissões ausentes:** {perms}"
                ),
                color=Config.COLOR_WARNING,
                footer_extra="SYSTEM DIAGNOSTICS",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            cmd_name = ctx.command.qualified_name if ctx.command else "comando"
            signature = f"{Config.COMMAND_PREFIX}{cmd_name} {ctx.command.signature}" if ctx.command else ""
            embed = build_embed(
                title="⚠️ PARÂMETRO AUSENTE // SINTAXE INVÁLIDA",
                description=(
                    f"O parâmetro obrigatório `{error.param.name}` não foi fornecido.\n"
                    f"**Uso correto:** `{signature.strip()}`"
                ),
                color=Config.COLOR_WARNING,
                footer_extra="SYNTAX VALIDATOR",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, (commands.BadArgument, commands.UserNotFound, commands.MemberNotFound)):
            embed = build_embed(
                title="❌ DADOS CORROMPIDOS // ARGUMENTO INVÁLIDO",
                description=(
                    "Não foi possível processar os parâmetros informados. "
                    "Verifique se mencionou um usuário válido ou inseriu um valor numérico correto."
                ),
                color=Config.COLOR_ERROR,
                footer_extra="INPUT PARSER",
            )
            await ctx.send(embed=embed)
            return

        logger.error("Erro não tratado no comando '%s': %s", ctx.command, error, exc_info=True)
        embed = build_embed(
            title="🩸 ANOMALIA NA BLACKWALL // ERRO INTERNO",
            description="Ocorreu uma falha inesperada durante a execução da diretriz neural.",
            color=Config.COLOR_ERROR,
        )
        await ctx.send(embed=embed)


# Alias para compatibilidade retroativa
NDBBot = CapricornBot


async def main() -> None:
    if not Config.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN não está configurado no ambiente ou arquivo .env.")
        sys.exit(1)

    bot = CapricornBot()
    async with bot:
        await bot.start(Config.DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[OFFLINE] Construto Capricorn encerrado.")

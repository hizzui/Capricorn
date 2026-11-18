"""
Módulo de Telemetria Geral, Dossiês de Cidadãos, Topologia da Sub-rede e Terminal de Operações.
Temática: Project Capricorn (Arasaka R&D // Cyberpunk 2).
"""

from __future__ import annotations

import random
from typing import Optional

import discord
from discord.ext import commands

from config import Config, build_embed


class General(commands.Cog):
    """Utilitários de telemetria, inspeção de sub-rede e terminal de ajuda da Capricorn."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        """Verifica a latência do link neural com o gateway do Discord."""
        ms = round(self.bot.latency * 1000)
        if ms < 120:
            status = "🟢 Estável (Sincronia Ideal)"
            color = Config.COLOR_SUCCESS
        elif ms < 250:
            status = "🟡 Oscilação Moderada"
            color = Config.COLOR_WARNING
        else:
            status = "🔴 Instabilidade na Blackwall"
            color = Config.COLOR_ERROR

        embed = build_embed(
            title="📡 TELEMETRIA NEURAL // PING DE REDE",
            description="Diagnóstico de conexão em tempo real do construto **Capricorn**.",
            color=color,
            footer_extra=f"NODE {Config.BOT_VERSION}",
        )
        embed.add_field(name="Latência de Gateway", value=f"`{ms} ms`", inline=True)
        embed.add_field(name="Integridade do Link", value=status, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def dado(self, ctx: commands.Context, lados: int = 6) -> None:
        """Executa uma simulação probabilística de N faces (padrão: 6)."""
        if not 2 <= lados <= 1000:
            embed = build_embed(
                title="⚠️ PARÂMETRO FORA DE ESCALA",
                description="O módulo probabilístico aceita apenas matrizes entre **2** e **1000** faces.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        resultado = random.randint(1, lados)
        embed = build_embed(
            title="🎲 SIMULADOR PROBABILÍSTICO // DADO",
            description=f"Matriz **`d{lados}`** processada pelo núcleo Capricorn.",
            color=Config.COLOR_PRIMARY,
        )
        embed.add_field(name="Resultado Obtido", value=f"**`[ {resultado} ]`**", inline=True)
        embed.add_field(name="Operador", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def moeda(self, ctx: commands.Context) -> None:
        """Realiza um sorteio binário (Cara ou Coroa)."""
        lado = "CARA (Arasaka Crest)" if random.random() >= 0.5 else "COROA (Blackwall Sigil)"
        embed = build_embed(
            title="🪙 DECISÃO BINÁRIA // MOEDA",
            description=f"Resultado do lançamento: **{lado}**",
            color=Config.COLOR_GOLD,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def vote(self, ctx: commands.Context, *, pergunta: str) -> None:
        """Inicia um protocolo de votação corporativa com reações."""
        embed = build_embed(
            title="📊 PROTOCOLO DE CONSENSO // VOTAÇÃO",
            description=f"```fix\n{pergunta}\n```\nRegistre sua diretriz utilizando as reações abaixo.",
            color=Config.COLOR_PRIMARY,
            footer_extra=f"Solicitado por {ctx.author.display_name}",
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @commands.command()
    async def user(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Exibe o dossiê biométrico e credenciais de um membro da sub-rede."""
        target = member or ctx.author
        embed = build_embed(
            title=f"🧬 DOSSIÊ BIOMÉTRICO // {target.display_name.upper()}",
            description="Registro extraído do banco de dados neural da sub-rede.",
            color=Config.COLOR_PRIMARY,
            footer_extra="KIROSHI OPTICS SCANNER",
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Identificador (ID)", value=f"`{target.id}`", inline=True)
        embed.add_field(name="Assinatura na Rede", value=f"`@{target.name}`", inline=True)
        embed.add_field(
            name="Registro Global",
            value=f"`{target.created_at.strftime('%d/%m/%Y')}`",
            inline=True,
        )

        if isinstance(target, discord.Member) and target.joined_at:
            embed.add_field(
                name="Conexão ao Domínio",
                value=f"`{target.joined_at.strftime('%d/%m/%Y')}`",
                inline=True,
            )
            roles = [r.mention for r in reversed(target.roles) if r != ctx.guild.default_role]
            embed.add_field(
                name=f"Credenciais & Implantes ({len(roles)})",
                value=", ".join(roles[:12]) if roles else "`Sem credenciais atribuídas`",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def servidor(self, ctx: commands.Context) -> None:
        """Exibe a topologia e métricas operacionais do servidor atual."""
        guild = ctx.guild
        if guild is None:
            return

        embed = build_embed(
            title=f"🏙️ TOPOLOGIA DO DOMÍNIO // {guild.name.upper()}",
            description="Relatório estrutural e populacional da sub-rede local.",
            color=Config.COLOR_PRIMARY,
            footer_extra="ARASAKA NET-TOPOLOGY",
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="ID do Nó", value=f"`{guild.id}`", inline=True)
        embed.add_field(
            name="Diretor Executivo (Owner)",
            value=guild.owner.mention if guild.owner else "`N/A`",
            inline=True,
        )
        embed.add_field(
            name="Fundação da Sub-rede",
            value=f"`{guild.created_at.strftime('%d/%m/%Y')}`",
            inline=True,
        )
        embed.add_field(
            name="Cidadãos Conectados",
            value=f"`{guild.member_count:,}`",
            inline=True,
        )
        embed.add_field(
            name="Canais (Dados / Voz)",
            value=f"`{len(guild.text_channels)} texto` / `{len(guild.voice_channels)} voz`",
            inline=True,
        )
        embed.add_field(
            name="Níveis de Credencial",
            value=f"`{len(guild.roles)} cargos`",
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(
        self,
        ctx: commands.Context,
        member: Optional[discord.Member] = None,
    ) -> None:
        """Captura a projeção visual (avatar) em alta resolução de um membro."""
        target = member or ctx.author
        embed = build_embed(
            title=f"👁️ CAPTURA ÓPTICA KIROSHI // {target.display_name.upper()}",
            description=f"[🔗 Abrir Projeção Original em Alta Resolução]({target.display_avatar.url})",
            color=Config.COLOR_PRIMARY,
        )
        embed.set_image(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="ajuda", aliases=["help", "comandos"])
    async def ajuda(self, ctx: commands.Context) -> None:
        """Exibe o terminal completo de diretrizes e comandos da Capricorn."""
        p = Config.COMMAND_PREFIX
        embed = build_embed(
            title="🩸 TERMINAL DE OPERAÇÕES // PROJECT CAPRICORN",
            description=(
                "Interface de controle do engrama **Capricorn** (*Arasaka R&D Division*).\n"
                f"Prefixo de comando ativo: **`{p}`**"
            ),
            color=Config.COLOR_PRIMARY,
            footer_extra=f"SYS-ENGRAM {Config.BOT_VERSION}",
        )
        embed.add_field(
            name="📡 01. Telemetria & Sub-rede",
            value=(
                f"`{p}ping` — Diagnóstico e latência do link neural\n"
                f"`{p}user [@membro]` — Dossiê biométrico e credenciais\n"
                f"`{p}servidor` — Topologia e estatísticas da sub-rede\n"
                f"`{p}avatar [@membro]` — Captura óptica Kiroshi (Avatar HD)\n"
                f"`{p}dado [lados]` · `{p}moeda` · `{p}vote <pauta>`"
            ),
            inline=False,
        )
        embed.add_field(
            name=f"💶 02. Terminal Financeiro ({Config.CURRENCY_NAME} — {Config.CURRENCY_SYMBOL})",
            value=(
                f"`{p}balance [@membro]` — Consulta saldo na conta corporativa\n"
                f"`{p}payday` — Resgata subsídio diário Arasaka (ciclo de 24h)\n"
                f"`{p}pay <@membro> <valor>` — Transferência neural de fundos\n"
                f"`{p}slots [aposta]` — Terminal de apostas de Night City\n"
                f"`{p}leaderboard` — Ranking das maiores fortunas do domínio"
            ),
            inline=False,
        )
        embed.add_field(
            name="🛡️ 03. Contramedidas ICE & Moderação",
            value=(
                f"`{p}kick <@membro> [razão]` — Desconexão forçada da sub-rede\n"
                f"`{p}ban <@membro> [razão]` — Neutralização permanente via Blackwall\n"
                f"`{p}unban <id|nome>` — Revogação de bloqueio ICE\n"
                f"`{p}mute <@membro> [razão]` / `{p}unmute <@membro>` — Corta ou restaura transmissão\n"
                f"`{p}warn <@membro> [razão]` — Registra infração (3 strikes = Auto-Ban Soulkiller)\n"
                f"`{p}warnings [@membro]` · `{p}unwarn <@membro>` — Histórico e remoção de infrações\n"
                f"`{p}clear [1-200]` (`{p}purge`) — Expurgo em massa de registros do canal"
            ),
            inline=False,
        )
        embed.set_image(url=Config.BOT_BANNER_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))

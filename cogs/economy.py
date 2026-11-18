"""
Módulo Econômico Corporativo (`!balance`, `!payday`, `!pay`, `!slots`, `!leaderboard`).
Moeda: Eurodólares (€$) — Project Capricorn // Arasaka Financial Terminal.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config, build_embed, format_currency, load_json, save_json

SLOT_SYMBOLS = ("🩸", "⚡", "💠", "🎰", "👑", "7️⃣")


class Economy(commands.Cog):
    """Gerenciamento de contas em Eurodólares (€$), transferências neurais e terminal de apostas."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.ECONOMY_FILE
        self.state: Dict[str, Dict[str, Any]] = load_json(
            self.file_path,
            default={"users": {}, "last_payday": {}},
        )

    def _persist(self) -> None:
        save_json(self.file_path, self.state)

    def get_balance(self, user_id: int) -> int:
        key = str(user_id)
        users = self.state.setdefault("users", {})
        if key not in users:
            users[key] = Config.STARTING_BALANCE
            self._persist()
        return int(users[key])

    def set_balance(self, user_id: int, amount: int) -> None:
        self.state.setdefault("users", {})[str(user_id)] = max(0, int(amount))
        self._persist()

    @commands.command()
    async def balance(
        self,
        ctx: commands.Context,
        usuario: Optional[discord.User] = None,
    ) -> None:
        """Consulta o saldo em Eurodólares (€$) de uma conta corporativa."""
        target = usuario or ctx.author
        saldo = self.get_balance(target.id)

        embed = build_embed(
            title="💶 TERMINAL FINANCEIRO // EXTRATO DE CONTA",
            description=f"Consulta de ativos registrada para **{target.display_name}**.",
            color=Config.COLOR_GOLD,
            footer_extra="ARASAKA BANKING CORP",
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(
            name=f"Saldo Disponível ({Config.CURRENCY_NAME})",
            value=f"**`{format_currency(saldo)}`**",
            inline=True,
        )
        embed.add_field(name="Status da Conta", value="`🟢 Verificada`", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def payday(self, ctx: commands.Context) -> None:
        """Resgata o subsídio diário corporativo em Eurodólares (ciclo de 24h)."""
        user_key = str(ctx.author.id)
        claims = self.state.setdefault("last_payday", {})
        now = datetime.now()
        cooldown = timedelta(hours=Config.PAYDAY_COOLDOWN_HOURS)

        if user_key in claims:
            try:
                last_dt = datetime.fromisoformat(claims[user_key])
                if now - last_dt < cooldown:
                    rem = cooldown - (now - last_dt)
                    h = int(rem.total_seconds() // 3600)
                    m = int((rem.total_seconds() % 3600) // 60)
                    embed = build_embed(
                        title="⏳ SUBSÍDIO EM BLOQUEIO TEMPORÁRIO",
                        description=(
                            "Sua cota diária de Eurodólares já foi processada neste ciclo.\n"
                            f"Próxima liberação autorizada em: **`{h}h {m}m`**."
                        ),
                        color=Config.COLOR_WARNING,
                        footer_extra="ARASAKA PAYROLL SYSTEM",
                    )
                    await ctx.send(embed=embed)
                    return
            except ValueError:
                pass

        novo_saldo = self.get_balance(ctx.author.id) + Config.PAYDAY_AMOUNT
        self.state["users"][user_key] = novo_saldo
        claims[user_key] = now.isoformat()
        self._persist()

        embed = build_embed(
            title="💶 SUBSÍDIO CORPORATIVO LIBERADO",
            description=f"Transferência diária creditada na conta de **{ctx.author.display_name}**.",
            color=Config.COLOR_SUCCESS,
            footer_extra="ARASAKA PAYROLL SYSTEM",
        )
        embed.add_field(
            name="Valor Creditado",
            value=f"**`+{format_currency(Config.PAYDAY_AMOUNT)}`**",
            inline=True,
        )
        embed.add_field(
            name="Saldo Atualizado",
            value=f"**`{format_currency(novo_saldo)}`**",
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def pay(self, ctx: commands.Context, usuario: discord.User, amount: int) -> None:
        """Realiza uma transferência neural de Eurodólares para outro cidadão."""
        if usuario.id == ctx.author.id or usuario.bot:
            embed = build_embed(
                title="❌ TRANSAÇÃO RECUSADA // DESTINATÁRIO INVÁLIDO",
                description="Não é possível transferir fundos para si mesmo ou para construtos automatizados.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        if amount <= 0:
            embed = build_embed(
                title="❌ TRANSAÇÃO RECUSADA // VALOR INVÁLIDO",
                description="O montante da transferência deve ser estritamente maior que zero.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        saldo = self.get_balance(ctx.author.id)
        if saldo < amount:
            embed = build_embed(
                title="❌ FUNDOS INSUFICIENTES",
                description=(
                    f"Seu saldo disponível (**`{format_currency(saldo)}`**) é inferior "
                    f"ao valor solicitado (**`{format_currency(amount)}`**)."
                ),
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        novo_saldo_remetente = saldo - amount
        novo_saldo_destinatario = self.get_balance(usuario.id) + amount
        self.set_balance(ctx.author.id, novo_saldo_remetente)
        self.set_balance(usuario.id, novo_saldo_destinatario)

        embed = build_embed(
            title="⚡ TRANSFERÊNCIA NEURAL CONCLUÍDA",
            description="Operação P2P autenticada pela rede financeira de Night City.",
            color=Config.COLOR_SUCCESS,
            footer_extra="P2P ENCRYPTED LEDGER",
        )
        embed.add_field(name="Remetente", value=ctx.author.mention, inline=True)
        embed.add_field(name="Destinatário", value=usuario.mention, inline=True)
        embed.add_field(
            name="Valor Transferido",
            value=f"**`{format_currency(amount)}`**",
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def slots(self, ctx: commands.Context, aposta: int = Config.SLOTS_MIN_BET) -> None:
        """Aposta Eurodólares no terminal de caça-níqueis de Night City."""
        if not Config.SLOTS_MIN_BET <= aposta <= Config.SLOTS_MAX_BET:
            embed = build_embed(
                title="⚠️ LIMITE DE APOSTA VIOLADO",
                description=(
                    f"O terminal aceita apostas entre **`{format_currency(Config.SLOTS_MIN_BET)}`** "
                    f"e **`{format_currency(Config.SLOTS_MAX_BET)}`**."
                ),
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        saldo = self.get_balance(ctx.author.id)
        if saldo < aposta:
            embed = build_embed(
                title="❌ FUNDOS INSUFICIENTES",
                description=f"Saldo atual (**`{format_currency(saldo)}`**) insuficiente para cobrir a aposta.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        r1, r2, r3 = random.choices(SLOT_SYMBOLS, k=3)
        if r1 == r2 == r3:
            delta = aposta * 15
            status = "🔥 OVERCLOCK JACKPOT (15x)"
            color = Config.COLOR_GOLD
        elif r1 == r2 or r2 == r3 or r1 == r3:
            delta = aposta * 2
            status = "⚡ SINCRONIA PARCIAL (2x)"
            color = Config.COLOR_SUCCESS
        else:
            delta = -aposta
            status = "💀 FALHA DE SINCRONIA (Perda)"
            color = Config.COLOR_ERROR

        novo_saldo = saldo + delta
        self.set_balance(ctx.author.id, novo_saldo)
        sinal = "+" if delta >= 0 else "-"

        embed = build_embed(
            title="🎰 NIGHT CITY CASINO // TERMINAL CAPRICORN",
            description=f"### `[  {r1}  |  {r2}  |  {r3}  ]`\n**Resultado:** {status}",
            color=color,
            footer_extra=f"Operador: {ctx.author.display_name}",
        )
        embed.add_field(
            name="Balanço da Rodada",
            value=f"**`{sinal}{format_currency(abs(delta))}`**",
            inline=True,
        )
        embed.add_field(
            name="Saldo Final",
            value=f"**`{format_currency(novo_saldo)}`**",
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Exibe a elite corporativa (Top 10 maiores saldos em Eurodólares)."""
        users = self.state.get("users", {})
        if not users:
            embed = build_embed(
                title="📊 RANKING CORPORATIVO // VAZIO",
                description="Nenhum registro financeiro encontrado no banco de dados da sub-rede.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        ranked = sorted(users.items(), key=lambda x: int(x[1]), reverse=True)[:10]
        badges = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for idx, (uid, val) in enumerate(ranked, start=1):
            user_obj = self.bot.get_user(int(uid))
            name = user_obj.display_name if user_obj else f"Cidadão #{uid}"
            prefix = badges.get(idx, f"`#{idx:02d}`")
            lines.append(f"{prefix} **{name}** — `{format_currency(int(val))}`")

        embed = build_embed(
            title="🏆 ELITE CORPORATIVA // TOP 10 NIGHT CITY",
            description="\n".join(lines),
            color=Config.COLOR_GOLD,
            footer_extra="ARASAKA WEALTH INDEX",
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))

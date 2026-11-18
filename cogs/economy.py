"""
Virtual economy cog (`!balance`, `!payday`, `!pay`, `!slots`, `!leaderboard`).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config, load_json, save_json

SLOT_SYMBOLS = ("🍒", "🍀", "💎", "🎰", "👑", "7️⃣")


class Economy(commands.Cog):
    """Virtual currency balances, transfers, daily rewards, and slot machine."""

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
        """Check your credit balance or another user's balance."""
        target = usuario or ctx.author
        saldo = self.get_balance(target.id)
        await ctx.send(f"💰 **{target.display_name}** possui **{saldo:,}** créditos.")

    @commands.command()
    async def payday(self, ctx: commands.Context) -> None:
        """Claim daily credits (24h cooldown)."""
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
                    await ctx.send(f"⏰ Você já resgatou hoje. Tente novamente em **{h}h {m}m**.")
                    return
            except ValueError:
                pass

        novo_saldo = self.get_balance(ctx.author.id) + Config.PAYDAY_AMOUNT
        self.state["users"][user_key] = novo_saldo
        claims[user_key] = now.isoformat()
        self._persist()

        await ctx.send(
            f"💰 Você recebeu **+{Config.PAYDAY_AMOUNT:,}** créditos! Saldo atual: **{novo_saldo:,}**."
        )

    @commands.command()
    async def pay(self, ctx: commands.Context, usuario: discord.User, amount: int) -> None:
        """Transfer credits to another user."""
        if usuario.id == ctx.author.id or usuario.bot:
            await ctx.send("❌ Destinatário inválido.")
            return
        if amount <= 0:
            await ctx.send("❌ O valor deve ser maior que zero.")
            return

        saldo = self.get_balance(ctx.author.id)
        if saldo < amount:
            await ctx.send(f"❌ Saldo insuficiente (**{saldo:,}** créditos).")
            return

        self.set_balance(ctx.author.id, saldo - amount)
        self.set_balance(usuario.id, self.get_balance(usuario.id) + amount)
        await ctx.send(
            f"✅ **{ctx.author.display_name}** transferiu **{amount:,}** créditos para **{usuario.display_name}**."
        )

    @commands.command()
    async def slots(self, ctx: commands.Context, aposta: int = Config.SLOTS_MIN_BET) -> None:
        """Bet credits on a 3-reel slot machine."""
        if not Config.SLOTS_MIN_BET <= aposta <= Config.SLOTS_MAX_BET:
            await ctx.send(
                f"❌ A aposta deve ficar entre {Config.SLOTS_MIN_BET} e {Config.SLOTS_MAX_BET} créditos."
            )
            return

        saldo = self.get_balance(ctx.author.id)
        if saldo < aposta:
            await ctx.send(f"❌ Saldo insuficiente (**{saldo:,}** créditos).")
            return

        r1, r2, r3 = random.choices(SLOT_SYMBOLS, k=3)
        if r1 == r2 == r3:
            delta = aposta * 15
            status = "🎉 **JACKPOT!**"
        elif r1 == r2 or r2 == r3 or r1 == r3:
            delta = aposta * 2
            status = "✨ **Par!**"
        else:
            delta = -aposta
            status = "❌ **Perdeu**"

        novo_saldo = saldo + delta
        self.set_balance(ctx.author.id, novo_saldo)

        await ctx.send(
            f"🎰 `[ {r1} | {r2} | {r3} ]` — {status} ({delta:+,} créditos) · Saldo: **{novo_saldo:,}**"
        )

    @commands.command()
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Show the top 10 users by credit balance."""
        users = self.state.get("users", {})
        if not users:
            await ctx.send("Nenhum saldo registrado ainda.")
            return

        ranked = sorted(users.items(), key=lambda x: int(x[1]), reverse=True)[:10]
        lines = []
        for idx, (uid, val) in enumerate(ranked, start=1):
            user_obj = self.bot.get_user(int(uid))
            name = user_obj.display_name if user_obj else f"User #{uid}"
            lines.append(f"**{idx}.** {name} — `{int(val):,}` créditos")

        embed = discord.Embed(
            title="🏆 Top 10 — Economia",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))

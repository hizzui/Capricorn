"""
Virtual economy cog (`!balance`, `!pay`, `!slots`, `!payday`, `!leaderboard`).
Persists balances and daily claim timestamps in `data/economy.json`.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config
from utils.storage import load_json, save_json

SLOT_REELS = ("🍒", "🍪", "🍀", "💎", "🎰", "🎲", "👑", "2️⃣", "7️⃣")


class Economy(commands.Cog):
    """Virtual currency ledger, peer transfers, daily rewards, and slot machine."""

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
        """Display the credit balance of the caller or a target user."""
        target = usuario or ctx.author
        saldo = self.get_balance(target.id)

        embed = discord.Embed(
            title=f"💰 Saldo de {target.display_name}",
            description=f"**{saldo:,}** créditos",
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def pay(self, ctx: commands.Context, usuario: discord.User, amount: int) -> None:
        """Transfer credits from the caller to another Discord user."""
        if usuario.id == ctx.author.id:
            await ctx.send("❌ Você não pode transferir créditos para si mesmo.")
            return

        if usuario.bot:
            await ctx.send("❌ Não é possível transferir créditos para bots.")
            return

        if amount <= 0:
            await ctx.send("❌ O valor da transferência deve ser maior que zero.")
            return

        sender_balance = self.get_balance(ctx.author.id)
        if sender_balance < amount:
            await ctx.send(f"❌ Saldo insuficiente. Seu saldo atual é de **{sender_balance:,}** créditos.")
            return

        self.set_balance(ctx.author.id, sender_balance - amount)
        recipient_balance = self.get_balance(usuario.id)
        self.set_balance(usuario.id, recipient_balance + amount)

        embed = discord.Embed(
            title="✅ Transferência realizada",
            description=f"**{ctx.author.display_name}** enviou **{amount:,}** créditos para **{usuario.display_name}**.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def slots(self, ctx: commands.Context, aposta: int = Config.SLOTS_MIN_BET) -> None:
        """Wager credits on a 3-reel slot machine."""
        if not Config.SLOTS_MIN_BET <= aposta <= Config.SLOTS_MAX_BET:
            await ctx.send(
                f"❌ A aposta deve estar entre **{Config.SLOTS_MIN_BET:,}** e **{Config.SLOTS_MAX_BET:,}** créditos."
            )
            return

        saldo = self.get_balance(ctx.author.id)
        if saldo < aposta:
            await ctx.send(f"❌ Saldo insuficiente. Você possui **{saldo:,}** créditos.")
            return

        r1, r2, r3 = random.choices(SLOT_REELS, k=3)

        if r1 == r2 == r3:
            delta = aposta * Config.SLOTS_JACKPOT_MULTIPLIER
            outcome = "🎉 JACKPOT!"
        elif r1 == r2 or r2 == r3 or r1 == r3:
            delta = aposta * Config.SLOTS_PAIR_MULTIPLIER
            outcome = "✨ Par combinado!"
        else:
            delta = -aposta
            outcome = "❌ Sem combinação"

        novo_saldo = saldo + delta
        self.set_balance(ctx.author.id, novo_saldo)

        embed = discord.Embed(
            title="🎰 Caça-Níqueis",
            description=f"`[ {r1} | {r2} | {r3} ]`",
            color=discord.Color.purple(),
        )
        embed.add_field(name="Resultado", value=outcome, inline=False)
        embed.add_field(name="Aposta", value=f"{aposta:,}", inline=True)
        embed.add_field(name="Balanço", value=f"{delta:+,}", inline=True)
        embed.add_field(name="Saldo atualizado", value=f"**{novo_saldo:,}** créditos", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def payday(self, ctx: commands.Context) -> None:
        """Claim the daily credit allowance (24-hour cooldown per user)."""
        user_key = str(ctx.author.id)
        last_claims = self.state.setdefault("last_payday", {})
        now = datetime.now()
        cooldown = timedelta(hours=Config.PAYDAY_COOLDOWN_HOURS)

        if user_key in last_claims:
            try:
                last_dt = datetime.fromisoformat(last_claims[user_key])
                elapsed = now - last_dt
                if elapsed < cooldown:
                    remaining = cooldown - elapsed
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    await ctx.send(f"⏰ Cooldown ativo. Próximo resgate disponível em **{hours}h {minutes}m**.")
                    return
            except ValueError:
                pass

        novo_saldo = self.get_balance(ctx.author.id) + Config.PAYDAY_AMOUNT
        self.state["users"][user_key] = novo_saldo
        last_claims[user_key] = now.isoformat()
        self._persist()

        embed = discord.Embed(
            title="💰 Payday resgatado",
            description=f"Você recebeu **+{Config.PAYDAY_AMOUNT:,}** créditos diários.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Novo saldo", value=f"**{novo_saldo:,}** créditos", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx: commands.Context, top: int = 10) -> None:
        """Rank the top credit holders recorded by the bot."""
        limit = max(1, min(top, 25))
        users = self.state.get("users", {})
        if not users:
            await ctx.send("Nenhum saldo registrado até o momento.")
            return

        ranked = sorted(users.items(), key=lambda item: int(item[1]), reverse=True)[:limit]
        embed = discord.Embed(
            title=f"🏆 Top {len(ranked)} — Economia",
            color=discord.Color.gold(),
        )

        for rank, (uid, balance_val) in enumerate(ranked, start=1):
            user_obj = self.bot.get_user(int(uid))
            if user_obj is None:
                try:
                    user_obj = await self.bot.fetch_user(int(uid))
                except discord.HTTPException:
                    user_obj = None

            label = user_obj.display_name if user_obj else f"User #{uid}"
            embed.add_field(
                name=f"{rank}. {label}",
                value=f"**{int(balance_val):,}** créditos",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))

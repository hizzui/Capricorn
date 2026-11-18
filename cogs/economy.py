"""
Virtual economy cog (`!balance`, `!payday`, `!pay`, `!slots`, `!leaderboard`).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config, build_embed, load_json, save_json

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

    @commands.command(name="balance", aliases=["bal"])
    async def balance(
        self,
        ctx: commands.Context,
        user: Optional[discord.User] = None,
    ) -> None:
        """Check your credit balance or another user's balance."""
        target = user or ctx.author
        bal = self.get_balance(target.id)
        embed = build_embed(
            title="Account Balance",
            description=f"**{target.display_name}** has **{bal:,}** credits.",
            color=Config.COLOR_PRIMARY,
        )
        await ctx.send(embed=embed)

    @commands.command(name="payday", aliases=["daily"])
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
                    embed = build_embed(
                        title="Cooldown Active",
                        description=f"You have already claimed your daily reward. Try again in **{h}h {m}m**.",
                        color=Config.COLOR_WARNING,
                    )
                    await ctx.send(embed=embed)
                    return
            except ValueError:
                pass

        new_balance = self.get_balance(ctx.author.id) + Config.PAYDAY_AMOUNT
        self.state["users"][user_key] = new_balance
        claims[user_key] = now.isoformat()
        self._persist()

        embed = build_embed(
            title="Daily Reward Claimed",
            description=f"You received **+{Config.PAYDAY_AMOUNT:,}** credits.\nNew balance: **{new_balance:,}** credits.",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def pay(self, ctx: commands.Context, user: discord.User, amount: int) -> None:
        """Transfer credits to another user."""
        if user.id == ctx.author.id or user.bot:
            embed = build_embed(
                title="Invalid Recipient",
                description="You cannot transfer credits to yourself or to a bot.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        if amount <= 0:
            embed = build_embed(
                title="Invalid Amount",
                description="Transfer amount must be greater than zero.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        bal = self.get_balance(ctx.author.id)
        if bal < amount:
            embed = build_embed(
                title="Insufficient Funds",
                description=f"Your current balance (**{bal:,}** credits) is lower than **{amount:,}**.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        self.set_balance(ctx.author.id, bal - amount)
        self.set_balance(user.id, self.get_balance(user.id) + amount)

        embed = build_embed(
            title="Transfer Complete",
            description=f"**{ctx.author.display_name}** transferred **{amount:,}** credits to **{user.display_name}**.",
            color=Config.COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def slots(self, ctx: commands.Context, bet: int = Config.SLOTS_MIN_BET) -> None:
        """Bet credits on a 3-reel slot machine."""
        if not Config.SLOTS_MIN_BET <= bet <= Config.SLOTS_MAX_BET:
            embed = build_embed(
                title="Invalid Bet",
                description=f"Bet amount must be between **{Config.SLOTS_MIN_BET:,}** and **{Config.SLOTS_MAX_BET:,}** credits.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        bal = self.get_balance(ctx.author.id)
        if bal < bet:
            embed = build_embed(
                title="Insufficient Funds",
                description=f"Your current balance (**{bal:,}** credits) cannot cover this bet.",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        r1, r2, r3 = random.choices(SLOT_SYMBOLS, k=3)
        if r1 == r2 == r3:
            delta = bet * 15
            status = "JACKPOT (15x)"
            color = Config.COLOR_GOLD
        elif r1 == r2 or r2 == r3 or r1 == r3:
            delta = bet * 2
            status = "Pair Match (2x)"
            color = Config.COLOR_SUCCESS
        else:
            delta = -bet
            status = "No Match"
            color = Config.COLOR_ERROR

        new_balance = bal + delta
        self.set_balance(ctx.author.id, new_balance)

        embed = build_embed(
            title="Slots",
            description=f"`[ {r1} | {r2} | {r3} ]` — **{status}** ({delta:+,} credits)\nBalance: **{new_balance:,}** credits",
            color=color,
        )
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["top", "rich"])
    async def leaderboard(self, ctx: commands.Context) -> None:
        """Show the top 10 users by credit balance."""
        users = self.state.get("users", {})
        if not users:
            embed = build_embed(
                title="Leaderboard",
                description="No balances recorded yet.",
                color=Config.COLOR_PRIMARY,
            )
            await ctx.send(embed=embed)
            return

        ranked = sorted(users.items(), key=lambda x: int(x[1]), reverse=True)[:10]
        lines = []
        for idx, (uid, val) in enumerate(ranked, start=1):
            user_obj = self.bot.get_user(int(uid))
            name = user_obj.display_name if user_obj else f"User #{uid}"
            lines.append(f"**{idx}.** {name} — `{int(val):,}` credits")

        embed = build_embed(
            title="Top 10 — Economy Leaderboard",
            description="\n".join(lines),
            color=Config.COLOR_GOLD,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Economy(bot))

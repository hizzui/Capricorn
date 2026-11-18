"""
Lightweight interactive commands (`!dado`, `!moeda`, `!vote`, `!calc`).
Uses an AST-based arithmetic evaluator for `!calc` instead of `eval()`.
"""

from __future__ import annotations

import ast
import operator
import random
from typing import Callable, Dict, Type, Union

import discord
from discord.ext import commands

Number = Union[int, float]

_BINARY_OPS: Dict[Type[ast.operator], Callable[[Number, Number], Number]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: Dict[Type[ast.unaryop], Callable[[Number], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval_math(expr: str) -> Number:
    """
    Evaluate a basic arithmetic expression safely using Python's AST.
    Rejects function calls, attribute access, and large exponents.
    """
    parsed = ast.parse(expr.strip(), mode="eval")

    def _eval(node: ast.AST) -> Number:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent out of allowed range.")
            return _BINARY_OPS[type(node.op)](left, right)
        raise ValueError("Unsupported syntax in arithmetic expression.")

    return _eval(parsed)


class Fun(commands.Cog):
    """Quick chat utilities: dice roll, coin flip, reaction polls, and calculator."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def dado(self, ctx: commands.Context, lados: int = 6) -> None:
        """Roll an N-sided die (defaults to d6)."""
        if not 2 <= lados <= 10000:
            await ctx.send("❌ O dado precisa ter entre 2 e 10.000 lados.")
            return
        resultado = random.randint(1, lados)
        await ctx.send(f"🎲 Resultado (d{lados}): **{resultado}**")

    @commands.command()
    async def moeda(self, ctx: commands.Context) -> None:
        """Flip a coin (Cara / Coroa)."""
        resultado = "Cara" if random.random() >= 0.5 else "Coroa"
        await ctx.send(f"🪙 **{resultado}!**")

    @commands.command()
    async def vote(self, ctx: commands.Context, *, pergunta: str) -> None:
        """Create a quick thumbs-up / thumbs-down poll embed."""
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
    async def calc(self, ctx: commands.Context, *, operacao: str) -> None:
        """Evaluate a mathematical expression safely."""
        try:
            resultado = safe_eval_math(operacao)
            formatted = round(resultado, 6) if isinstance(resultado, float) else resultado
            await ctx.send(f"`{operacao}` = **{formatted}**")
        except ZeroDivisionError:
            await ctx.send("❌ Erro: divisão por zero.")
        except Exception:
            await ctx.send("❌ Expressão inválida. Use apenas números e operadores (`+`, `-`, `*`, `/`, `%`, `**`).")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))

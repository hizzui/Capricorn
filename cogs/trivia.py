"""
Interactive reaction-based trivia game (`!trivia`, `!trivia_score`, `!trivia_top`).
Persists player scores and games played to `data/trivia_scores.json`.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

from config import Config
from utils.storage import load_json, save_json

CHOICE_EMOJIS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣")

QUESTION_BANK: List[Dict[str, Any]] = [
    # Geography
    {"pergunta": "Qual é a capital da França?", "opcoes": ["Paris", "Lyon", "Marselha", "Bordeaux"], "resposta": "Paris"},
    {"pergunta": "Qual é a capital do Brasil?", "opcoes": ["Rio de Janeiro", "Brasília", "São Paulo", "Salvador"], "resposta": "Brasília"},
    {"pergunta": "Qual é o maior oceano do mundo?", "opcoes": ["Atlântico", "Índico", "Pacífico", "Ártico"], "resposta": "Pacífico"},
    {"pergunta": "Quantos continentes existem?", "opcoes": ["5", "6", "7", "8"], "resposta": "7"},
    {"pergunta": "Qual é a capital do Japão?", "opcoes": ["Osaka", "Tóquio", "Kyoto", "Hiroshima"], "resposta": "Tóquio"},
    {"pergunta": "Qual país tem a maior população atualmente?", "opcoes": ["Índia", "China", "EUA", "Indonésia"], "resposta": "Índia"},
    {"pergunta": "Qual país produz mais ouro no mundo?", "opcoes": ["Austrália", "África do Sul", "Canadá", "China"], "resposta": "China"},
    {"pergunta": "Qual é o deserto mais quente registrado no mundo?", "opcoes": ["Deserto de Gobi", "Deserto do Saara", "Deserto da Líbia", "Deserto Arábico"], "resposta": "Deserto da Líbia"},
    # Science
    {"pergunta": "Qual planeta é conhecido como o Planeta Vermelho?", "opcoes": ["Vênus", "Marte", "Júpiter", "Saturno"], "resposta": "Marte"},
    {"pergunta": "Quantos lados tem um hexágono?", "opcoes": ["4", "5", "6", "7"], "resposta": "6"},
    {"pergunta": "Qual é o elemento químico de símbolo 'Au'?", "opcoes": ["Alumínio", "Argônio", "Ouro", "Prata"], "resposta": "Ouro"},
    {"pergunta": "Qual é a velocidade aproximada da luz no vácuo?", "opcoes": ["300.000 km/s", "200.000 km/s", "400.000 km/s", "150.000 km/s"], "resposta": "300.000 km/s"},
    {"pergunta": "Quantos ossos possui o corpo humano adulto?", "opcoes": ["186", "206", "226", "246"], "resposta": "206"},
    {"pergunta": "Qual é o maior órgão do corpo humano?", "opcoes": ["Coração", "Pele", "Fígado", "Pulmão"], "resposta": "Pele"},
    # History
    {"pergunta": "Em que ano terminou a Segunda Guerra Mundial?", "opcoes": ["1943", "1944", "1945", "1946"], "resposta": "1945"},
    {"pergunta": "Qual foi o primeiro país a lançar um satélite artificial ao espaço?", "opcoes": ["EUA", "União Soviética", "China", "França"], "resposta": "União Soviética"},
    {"pergunta": "Quem foi o primeiro presidente dos Estados Unidos?", "opcoes": ["Thomas Jefferson", "George Washington", "Abraham Lincoln", "Benjamin Franklin"], "resposta": "George Washington"},
    {"pergunta": "Em que ano teve início a Revolução Francesa?", "opcoes": ["1776", "1789", "1800", "1815"], "resposta": "1789"},
    # Nature
    {"pergunta": "Qual é o animal terrestre mais veloz?", "opcoes": ["Antílope", "Gazela", "Guepardo (Chita)", "Leão"], "resposta": "Guepardo (Chita)"},
    {"pergunta": "Qual é o animal mais pesado do planeta?", "opcoes": ["Elefante Africano", "Baleia-Azul", "Girafa", "Hipopótamo"], "resposta": "Baleia-Azul"},
    {"pergunta": "Quantos tentáculos possui um polvo?", "opcoes": ["6", "8", "10", "12"], "resposta": "8"},
    {"pergunta": "Qual destes mamíferos põe ovos?", "opcoes": ["Ornitorrinco", "Equidna", "Ambos", "Nenhum"], "resposta": "Ambos"},
    # Currencies
    {"pergunta": "Qual é a moeda oficial do Japão?", "opcoes": ["Won", "Yuan", "Iene", "Baht"], "resposta": "Iene"},
    {"pergunta": "Qual é a moeda oficial do Reino Unido?", "opcoes": ["Euro", "Libra Esterlina", "Dólar", "Franco"], "resposta": "Libra Esterlina"},
    {"pergunta": "Qual é a moeda oficial da China?", "opcoes": ["Iene", "Yuan (Renminbi)", "Rúpia", "Baht"], "resposta": "Yuan (Renminbi)"},
    {"pergunta": "Qual é a moeda oficial do Brasil?", "opcoes": ["Peso", "Real", "Bolívar", "Guarani"], "resposta": "Real"},
    # General Knowledge & Tech
    {"pergunta": "Quantas cores compõem o arco-íris tradicional?", "opcoes": ["5", "6", "7", "8"], "resposta": "7"},
    {"pergunta": "Qual é a maior biblioteca do mundo em acervo?", "opcoes": ["Biblioteca Nacional Francesa", "Biblioteca Britânica", "Biblioteca do Congresso dos EUA", "Biblioteca Vaticana"], "resposta": "Biblioteca do Congresso dos EUA"},
    {"pergunta": "Quantas cordas tem um violão/guitarra padrão?", "opcoes": ["5", "6", "7", "8"], "resposta": "6"},
    {"pergunta": "Quantos jogadores titulares um time de futebol possui em campo?", "opcoes": ["9", "10", "11", "12"], "resposta": "11"},
    {"pergunta": "Quantas Copas do Mundo masculinas a Seleção Brasileira venceu?", "opcoes": ["3", "4", "5", "6"], "resposta": "5"},
    {"pergunta": "Em que país surgiram as regras modernas da rainha no xadrez?", "opcoes": ["Irã", "Itália", "Espanha", "França"], "resposta": "Espanha"},
    {"pergunta": "A quem é atribuído o aperfeiçoamento comercial da lâmpada incandescente?", "opcoes": ["Nikola Tesla", "Thomas Edison", "George Westinghouse", "Alexander Bell"], "resposta": "Thomas Edison"},
    {"pergunta": "Em que ano a ARPANET (precursora da Internet) estabeleceu sua primeira conexão?", "opcoes": ["1969", "1975", "1989", "1995"], "resposta": "1969"},
    {"pergunta": "Qual é a menor unidade de informação em sistemas digitais?", "opcoes": ["Byte", "Kilobyte", "Bit", "Megabyte"], "resposta": "Bit"},
    {"pergunta": "Quantos dias possui um ano bissexto?", "opcoes": ["364", "365", "366", "367"], "resposta": "366"},
    {"pergunta": "Qual é o símbolo químico do Ferro?", "opcoes": ["Fe", "Fr", "F", "Fn"], "resposta": "Fe"},
    {"pergunta": "Quantas letras formam o alfabeto grego clássico?", "opcoes": ["20", "22", "24", "26"], "resposta": "24"},
    {"pergunta": "Qual é a montanha mais alta do mundo acima do nível do mar?", "opcoes": ["K2", "Kangchenjunga", "Monte Everest", "Makalu"], "resposta": "Monte Everest"},
    {"pergunta": "Qual destes metais preciosos costuma ter a maior cotação por onça?", "opcoes": ["Ouro", "Platina", "Paládio", "Ródio"], "resposta": "Ródio"},
    {"pergunta": "Quantos lados possui um pentágono?", "opcoes": ["4", "5", "6", "7"], "resposta": "5"},
]


class Trivia(commands.Cog):
    """Multi-round trivia quiz with persistent per-user score tracking."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.active_channels: Dict[int, int] = {}
        self.file_path = Config.TRIVIA_FILE
        self.leaderboard: Dict[str, Dict[str, int]] = load_json(self.file_path, default={})

    def _persist(self) -> None:
        save_json(self.file_path, self.leaderboard)

    @commands.command()
    async def trivia(self, ctx: commands.Context) -> None:
        """Start a 5-question trivia round in the current channel."""
        if ctx.channel.id in self.active_channels:
            await ctx.send("⚠️ Já existe uma partida de trivia em andamento neste canal.")
            return

        self.active_channels[ctx.channel.id] = ctx.author.id
        rounds = min(Config.TRIVIA_QUESTIONS_PER_ROUND, len(QUESTION_BANK))
        selected_questions = random.sample(QUESTION_BANK, k=rounds)

        try:
            intro = discord.Embed(
                title="🎯 Partida de Trivia Iniciada",
                description=(
                    f"{ctx.author.mention}, responda às **{rounds} perguntas** clicando nas reações "
                    f"(`1️⃣` a `4️⃣`). Tempo limite: **{int(Config.TRIVIA_QUESTION_TIMEOUT)}s** por pergunta."
                ),
                color=discord.Color.blue(),
            )
            await ctx.send(embed=intro)
            await asyncio.sleep(1.5)

            score = 0
            for idx, q_data in enumerate(selected_questions, start=1):
                correct = q_data["resposta"]
                options = list(q_data["opcoes"])
                random.shuffle(options)

                body_lines = [
                    f"{CHOICE_EMOJIS[i]}  **{opt}**" for i, opt in enumerate(options)
                ]
                q_embed = discord.Embed(
                    title=f"❓ Pergunta {idx}/{rounds}",
                    description=f"**{q_data['pergunta']}**\n\n" + "\n".join(body_lines),
                    color=discord.Color.purple(),
                )
                q_embed.set_footer(
                    text=f"Jogador: {ctx.author.display_name} • {int(Config.TRIVIA_QUESTION_TIMEOUT)}s para reagir"
                )
                msg = await ctx.send(embed=q_embed)

                for emoji in CHOICE_EMOJIS:
                    await msg.add_reaction(emoji)

                def _check(reaction: discord.Reaction, user: discord.abc.User) -> bool:
                    return (
                        user.id == ctx.author.id
                        and reaction.message.id == msg.id
                        and str(reaction.emoji) in CHOICE_EMOJIS
                    )

                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add",
                        timeout=Config.TRIVIA_QUESTION_TIMEOUT,
                        check=_check,
                    )
                    picked_idx = CHOICE_EMOJIS.index(str(reaction.emoji))
                    picked_answer = options[picked_idx]

                    if picked_answer == correct:
                        score += 1
                        await ctx.send(f"✅ Resposta correta! (**{correct}**)")
                    else:
                        await ctx.send(f"❌ Incorreto. A resposta certa era **{correct}**.")
                except asyncio.TimeoutError:
                    await ctx.send(f"⏱️ Tempo esgotado! A resposta certa era **{correct}**.")

                await asyncio.sleep(1.5)

            user_key = str(ctx.author.id)
            record = self.leaderboard.setdefault(user_key, {"pontos": 0, "jogos": 0})
            record["pontos"] += score
            record["jogos"] += 1
            self._persist()

            summary = discord.Embed(
                title="🏁 Fim da Partida",
                description=f"Você acertou **{score}/{rounds}** perguntas.",
                color=discord.Color.gold(),
            )
            summary.add_field(
                name="Acumulado Geral",
                value=f"**{record['pontos']}** pontos em **{record['jogos']}** partidas",
                inline=False,
            )
            await ctx.send(embed=summary)
        finally:
            self.active_channels.pop(ctx.channel.id, None)

    @commands.command()
    async def trivia_score(
        self,
        ctx: commands.Context,
        usuario: Optional[discord.User] = None,
    ) -> None:
        """Display lifetime trivia stats for the caller or another user."""
        target = usuario or ctx.author
        record = self.leaderboard.get(str(target.id))

        if not record:
            await ctx.send(f"**{target.display_name}** ainda não participou de nenhuma partida de trivia.")
            return

        games = max(1, int(record["jogos"]))
        pts = int(record["pontos"])
        avg = round(pts / games, 2)

        embed = discord.Embed(
            title=f"🎯 Estatísticas de Trivia — {target.display_name}",
            color=discord.Color.purple(),
        )
        embed.add_field(name="Partidas", value=str(record["jogos"]), inline=True)
        embed.add_field(name="Pontos Totais", value=str(pts), inline=True)
        embed.add_field(name="Média / Partida", value=f"{avg} pts", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def trivia_top(self, ctx: commands.Context) -> None:
        """Display the top 10 trivia players on the leaderboard."""
        if not self.leaderboard:
            await ctx.send("Nenhuma pontuação de trivia registrada até o momento.")
            return

        ranked = sorted(
            self.leaderboard.items(),
            key=lambda item: int(item[1].get("pontos", 0)),
            reverse=True,
        )[:10]

        embed = discord.Embed(
            title="🏆 Top 10 — Trivia",
            color=discord.Color.gold(),
        )

        for rank, (uid, stats) in enumerate(ranked, start=1):
            user_obj = self.bot.get_user(int(uid))
            if user_obj is None:
                try:
                    user_obj = await self.bot.fetch_user(int(uid))
                except discord.HTTPException:
                    user_obj = None

            name = user_obj.display_name if user_obj else f"User #{uid}"
            embed.add_field(
                name=f"{rank}. {name}",
                value=f"**{stats['pontos']}** pts ({stats['jogos']} partidas)",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Trivia(bot))

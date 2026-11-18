"""
Twitch Helix API livestream monitor (`!stream`, `!streamset`).
Polls tracked channels in the background and posts a notification embed when a stream goes live.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

import aiohttp
import discord
from discord.ext import commands, tasks

from config import Config
from utils.storage import load_json, save_json

logger = logging.getLogger("ndb.streams")


class Streams(commands.Cog):
    """Livestream tracker backed by the Twitch Helix API."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.STREAMS_FILE
        self.state: Dict[str, Any] = load_json(
            self.file_path,
            default={"notify_channel": None, "streamers": []},
        )
        self.active_Broadcasts: Set[str] = set()
        self.twitch_token = Config.TWITCH_TOKEN
        self.twitch_client_id = Config.TWITCH_CLIENT_ID
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.poll_streams.start()

    def _persist(self) -> None:
        save_json(self.file_path, self.state)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.http_session is None or self.http_session.closed:
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self.http_session

    async def query_twitch_stream(self, login: str) -> Optional[Dict[str, Any]]:
        """Query the Twitch Helix API for a user's current live broadcast status."""
        if not self.twitch_token or not self.twitch_client_id:
            return None

        headers = {
            "Client-ID": self.twitch_client_id,
            "Authorization": f"Bearer {self.twitch_token}",
        }

        try:
            session = await self._get_session()
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                params={"user_login": login},
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    logger.warning("Twitch API returned HTTP %d for login=%s", resp.status, login)
                    return None

                payload = await resp.json()
                entries = payload.get("data", [])
                if not entries:
                    return {"online": False}

                stream = entries[0]
                return {
                    "online": True,
                    "title": stream.get("title") or "Sem título",
                    "game": stream.get("game_name") or "Sem categoria",
                    "viewers": int(stream.get("viewer_count", 0)),
                    "url": f"https://twitch.tv/{login}",
                }
        except aiohttp.ClientError as exc:
            logger.warning("Twitch request error for %s: %s", login, exc)
            return None

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def streamset(self, ctx: commands.Context) -> None:
        """Configure livestream alert channel and inspect Twitch API credentials status."""
        embed = discord.Embed(
            title="⚙️ Configuração de Streams",
            description="Defina o canal de alertas e verifique a integração com a Twitch.",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Subcomandos",
            value=(
                "`!streamset channel <#canal>` — Define o canal de anúncios\n"
                "`!streamset show` — Exibe a configuração atual\n"
                "`!streamset credentials` — Guia de configuração da API Twitch"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @streamset.command(name="channel")
    async def set_channel(self, ctx: commands.Context, canal: discord.TextChannel) -> None:
        """Set the text channel where live alerts will be posted."""
        self.state["notify_channel"] = canal.id
        self._persist()

        embed = discord.Embed(
            title="✅ Canal de alertas atualizado",
            description=f"As notificações de live serão enviadas em {canal.mention}.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @streamset.command(name="show")
    async def show_config(self, ctx: commands.Context) -> None:
        """Display the active alert channel, tracked count, and API readiness."""
        channel_id = self.state.get("notify_channel")
        channel_label = f"<#{channel_id}>" if channel_id else "Não configurado"
        guild_streamers = [
            s for s in self.state.get("streamers", []) if s.get("guild_id") == ctx.guild.id
        ]
        api_ready = bool(self.twitch_token and self.twitch_client_id)

        embed = discord.Embed(
            title="📡 Status do Monitoramento",
            color=discord.Color.purple(),
        )
        embed.add_field(name="Canal de alertas", value=channel_label, inline=True)
        embed.add_field(name="Canais monitorados", value=str(len(guild_streamers)), inline=True)
        embed.add_field(
            name="Twitch Helix API",
            value="Configurada ✅" if api_ready else "Credenciais ausentes ⚠️",
            inline=False,
        )
        await ctx.send(embed=embed)

    @streamset.command(name="credentials")
    async def show_credentials(self, ctx: commands.Context) -> None:
        """Show setup steps for Twitch Helix OAuth credentials."""
        embed = discord.Embed(
            title="🔑 Configurando a API da Twitch",
            description="Para habilitar a checagem automática de lives:",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="1. Portal de Desenvolvedores",
            value="Acesse https://dev.twitch.tv/console/apps e registre uma aplicação.",
            inline=False,
        )
        embed.add_field(
            name="2. Variáveis de Ambiente (.env)",
            value=(
                "Preencha no arquivo `.env` na raiz do bot:\n"
                "```env\n"
                "TWITCH_CLIENT_ID=seu_client_id\n"
                "TWITCH_TOKEN=seu_app_access_token\n"
                "```"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def stream(self, ctx: commands.Context) -> None:
        """Manage the list of streamers tracked in this server."""
        embed = discord.Embed(
            title="📡 Monitoramento de Streamers",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Subcomandos",
            value=(
                "`!stream add twitch <login>` — Adiciona um canal ao monitoramento\n"
                "`!stream remove <login>` — Remove um canal da lista\n"
                "`!stream list` — Lista os canais monitorados neste servidor\n"
                "`!stream check <login>` — Consulta o status da live imediatamente"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)

    @stream.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def add_stream(self, ctx: commands.Context, plataforma: str, usuario: str) -> None:
        """Track a Twitch or YouTube creator in the current guild."""
        platform = plataforma.lower().strip()
        login = usuario.lower().strip()

        if platform not in {"twitch", "youtube"}:
            await ctx.send("❌ Plataforma inválida. Use `twitch` ou `youtube`.")
            return

        streamers = self.state.setdefault("streamers", [])
        for entry in streamers:
            if entry["nome"].lower() == login and entry.get("guild_id") == ctx.guild.id:
                await ctx.send(f"⚠️ O canal **{usuario}** já está sendo monitorado.")
                return

        streamers.append(
            {
                "tipo": platform,
                "nome": login,
                "guild_id": ctx.guild.id,
                "adicionado_por": str(ctx.author),
                "data": datetime.now().isoformat(),
            }
        )
        self._persist()

        embed = discord.Embed(
            title="✅ Canal adicionado",
            description=f"**{login}** ({platform.title()}) foi incluído no monitoramento.",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @stream.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    async def remove_stream(self, ctx: commands.Context, usuario: str) -> None:
        """Stop tracking a streamer in the current guild."""
        login = usuario.lower().strip()
        before = len(self.state.get("streamers", []))
        self.state["streamers"] = [
            s
            for s in self.state.get("streamers", [])
            if not (s["nome"].lower() == login and s.get("guild_id") == ctx.guild.id)
        ]
        self._persist()

        if len(self.state["streamers"]) < before:
            await ctx.send(f"✅ O canal **{usuario}** foi removido do monitoramento.")
        else:
            await ctx.send(f"❌ **{usuario}** não consta na lista deste servidor.")

    @stream.command(name="list")
    async def list_streams(self, ctx: commands.Context) -> None:
        """List all creators currently tracked in this guild."""
        guild_streamers = [
            s for s in self.state.get("streamers", []) if s.get("guild_id") == ctx.guild.id
        ]
        if not guild_streamers:
            await ctx.send("Nenhum canal monitorado neste servidor.")
            return

        embed = discord.Embed(
            title="📡 Canais Monitorados",
            description=f"Total: **{len(guild_streamers)}**",
            color=discord.Color.purple(),
        )

        for entry in guild_streamers:
            badge = "🟣 Twitch" if entry["tipo"] == "twitch" else "🔴 YouTube"
            embed.add_field(
                name=f"{badge} — {entry['nome']}",
                value=f"Adicionado por: {entry.get('adicionado_por', 'desconhecido')}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @stream.command(name="check")
    async def check_streamer(self, ctx: commands.Context, usuario: str) -> None:
        """Perform an on-demand live check against the Twitch Helix endpoint."""
        if not self.twitch_token or not self.twitch_client_id:
            await ctx.send("❌ Credenciais da Twitch não configuradas. Veja `!streamset credentials`.")
            return

        login = usuario.lower().strip()
        async with ctx.typing():
            status = await self.query_twitch_stream(login)
            if status is None:
                await ctx.send(f"❌ Não foi possível consultar `{login}` na API da Twitch.")
                return

            if status.get("online"):
                embed = discord.Embed(
                    title=f"🔴 {login} está AO VIVO!",
                    description=status["title"][:200],
                    url=status["url"],
                    color=discord.Color.red(),
                )
                embed.add_field(name="Categoria", value=status["game"], inline=True)
                embed.add_field(name="Espectadores", value=f"{status['viewers']:,}", inline=True)
                embed.add_field(name="Stream", value=f"[Assistir na Twitch]({status['url']})", inline=False)
            else:
                embed = discord.Embed(
                    title="⚫ Offline",
                    description=f"**{login}** não está em transmissão no momento.",
                    color=discord.Color.dark_grey(),
                )

            await ctx.send(embed=embed)

    @tasks.loop(minutes=Config.TWITCH_CHECK_INTERVAL)
    async def poll_streams(self) -> None:
        """Periodic background task that checks tracked Twitch channels for live transitions."""
        channel_id = self.state.get("notify_channel")
        if not channel_id or not self.twitch_token or not self.twitch_client_id:
            return

        notify_channel = self.bot.get_channel(int(channel_id))
        if not isinstance(notify_channel, discord.TextChannel):
            return

        for entry in self.state.get("streamers", []):
            if entry.get("tipo") != "twitch":
                continue

            login = entry["nome"].lower()
            cache_key = f"{login}:{notify_channel.guild.id}"
            status = await self.query_twitch_stream(login)

            if status and status.get("online") and cache_key not in self.active_Broadcasts:
                embed = discord.Embed(
                    title=f"🔴 {entry['nome']} entrou ao vivo na Twitch!",
                    description=status["title"][:200],
                    url=status["url"],
                    color=discord.Color.red(),
                )
                embed.add_field(name="Jogo", value=status["game"], inline=True)
                embed.add_field(name="Viewers", value=f"{status['viewers']:,}", inline=True)
                embed.add_field(name="Link", value=f"[Assistir agora]({status['url']})", inline=False)

                try:
                    await notify_channel.send(embed=embed)
                    self.active_Broadcasts.add(cache_key)
                except discord.HTTPException as exc:
                    logger.warning("Failed to send stream alert in channel %s: %s", channel_id, exc)

            elif status is not None and not status.get("online"):
                self.active_Broadcasts.discard(cache_key)

    @poll_streams.before_loop
    async def before_poll_streams(self) -> None:
        await self.bot.wait_until_ready()

    def cog_unload(self) -> None:
        self.poll_streams.cancel()
        if self.http_session and not self.http_session.closed:
            self.bot.loop.create_task(self.http_session.close())


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Streams(bot))

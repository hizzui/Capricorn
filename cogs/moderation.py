"""
Server moderation cog (`!kick`, `!ban`, `!unban`, `!mute`, `!unmute`, `!warn`, `!warnings`, `!unwarn`).
Enforces role hierarchy checks and persists warning logs to `data/moderation.json`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config
from utils.storage import load_json, save_json


class Moderation(commands.Cog):
    """Role-checked moderation actions and persistent warning escalation."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.MODERATION_FILE
        self.state: Dict[str, Any] = load_json(
            self.file_path,
            default={"users": {}, "tempbans": []},
        )

    def _persist(self) -> None:
        save_json(self.file_path, self.state)

    @staticmethod
    def _can_moderate(ctx: commands.Context, target: discord.Member) -> Optional[str]:
        """Validate that the moderator outranks the target member."""
        if target.id == ctx.author.id:
            return "❌ Você não pode executar esta ação em si mesmo."
        if ctx.guild and target.id == ctx.guild.owner_id:
            return "❌ Não é possível moderar o proprietário do servidor."
        if (
            isinstance(ctx.author, discord.Member)
            and ctx.guild
            and ctx.author.id != ctx.guild.owner_id
            and target.top_role >= ctx.author.top_role
        ):
            return "❌ O membro possui um cargo igual ou superior ao seu."
        return None

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Kick a member from the guild."""
        err = self._can_moderate(ctx, membro)
        if err:
            await ctx.send(err)
            return

        try:
            await membro.kick(reason=f"{ctx.author}: {razao}")
            embed = discord.Embed(
                title="🦶 Membro expulso",
                description=f"**{membro}** foi removido do servidor.",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Razão", value=razao, inline=False)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Falha ao expulsar membro: {exc}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Ban a member and purge their last 24 hours of messages."""
        err = self._can_moderate(ctx, membro)
        if err:
            await ctx.send(err)
            return

        try:
            await membro.ban(reason=f"{ctx.author}: {razao}", delete_message_seconds=86400)
            embed = discord.Embed(
                title="🚫 Membro banido",
                description=f"**{membro}** foi banido permanentemente.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Razão", value=razao, inline=False)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Falha ao banir membro: {exc}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, usuario: str) -> None:
        """Revoke an active ban by username or numeric Discord ID."""
        query = usuario.strip().lower()

        async for entry in ctx.guild.bans():
            if entry.user.name.lower() == query or str(entry.user.id) == query:
                try:
                    await ctx.guild.unban(entry.user, reason=f"Desbanido por {ctx.author}")
                    embed = discord.Embed(
                        title="✅ Banimento removido",
                        description=f"**{entry.user}** foi desbanido.",
                        color=discord.Color.green(),
                    )
                    await ctx.send(embed=embed)
                    return
                except discord.HTTPException as exc:
                    await ctx.send(f"❌ Falha ao remover ban: {exc}")
                    return

        await ctx.send(f"❌ Usuário `{usuario}` não encontrado na lista de banimentos.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        tempo_min: Optional[int] = None,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Assign the muted role to a member, creating channel overrides if needed."""
        err = self._can_moderate(ctx, membro)
        if err:
            await ctx.send(err)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None:
            try:
                muted_role = await ctx.guild.create_role(
                    name=Config.MUTE_ROLE_NAME,
                    reason="Cargo automático para membros silenciados",
                )
                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(muted_role, send_messages=False)
            except discord.HTTPException as exc:
                await ctx.send(f"❌ Não foi possível criar o cargo `{Config.MUTE_ROLE_NAME}`: {exc}")
                return

        try:
            await membro.add_roles(muted_role, reason=f"{ctx.author}: {razao}")
            embed = discord.Embed(
                title="🔇 Membro silenciado",
                description=f"**{membro}** recebeu o cargo `{Config.MUTE_ROLE_NAME}`.",
                color=discord.Color.orange(),
            )
            if tempo_min:
                embed.add_field(name="Duração sugerida", value=f"{tempo_min} minutos", inline=True)
            embed.add_field(name="Razão", value=razao, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Falha ao silenciar membro: {exc}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, membro: discord.Member) -> None:
        """Remove the muted role from a member."""
        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None or muted_role not in membro.roles:
            await ctx.send(f"❌ **{membro.display_name}** não está silenciado.")
            return

        try:
            await membro.remove_roles(muted_role, reason=f"Desmutado por {ctx.author}")
            embed = discord.Embed(
                title="🔊 Silenciamento removido",
                description=f"**{membro}** pode enviar mensagens novamente.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Falha ao remover silenciamento: {exc}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Issue a formal warning; automatically bans the member upon reaching `Config.WARN_LIMIT`."""
        err = self._can_moderate(ctx, membro)
        if err:
            await ctx.send(err)
            return

        users = self.state.setdefault("users", {})
        record = users.setdefault(str(membro.id), {"warns": 0, "motivos": []})

        record["warns"] += 1
        record["motivos"].append(
            {
                "razao": razao,
                "moderador": str(ctx.author),
                "data": datetime.now().isoformat(),
            }
        )
        self._persist()

        warn_count = int(record["warns"])
        embed = discord.Embed(
            title="⚠️ Aviso registrado",
            description=f"**{membro}** recebeu um aviso disciplinar.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Razão", value=razao, inline=False)
        embed.add_field(name="Acumulado", value=f"{warn_count}/{Config.WARN_LIMIT}", inline=True)
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

        if warn_count >= Config.WARN_LIMIT:
            try:
                await membro.ban(reason=f"Atingiu o limite de {Config.WARN_LIMIT} avisos.")
                await ctx.send(f"🚫 **{membro}** atingiu {Config.WARN_LIMIT} avisos e foi banido automaticamente.")
            except discord.HTTPException:
                await ctx.send(
                    f"⚠️ **{membro}** atingiu {Config.WARN_LIMIT} avisos, mas o bot não possui permissão para bani-lo."
                )

    @commands.command()
    async def warnings(
        self,
        ctx: commands.Context,
        membro: Optional[discord.Member] = None,
    ) -> None:
        """List all recorded warnings for a member."""
        target = membro or ctx.author
        record = self.state.get("users", {}).get(str(target.id))

        if not record or not record.get("warns"):
            await ctx.send(f"**{target.display_name}** não possui avisos registrados.")
            return

        embed = discord.Embed(
            title=f"⚠️ Histórico de Avisos — {target.display_name}",
            description=f"Total acumulado: **{record['warns']}/{Config.WARN_LIMIT}**",
            color=discord.Color.orange(),
        )

        for idx, item in enumerate(record.get("motivos", []), start=1):
            embed.add_field(
                name=f"Aviso #{idx}",
                value=f"Razão: {item['razao']}\nModerador: {item['moderador']}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx: commands.Context, membro: discord.Member) -> None:
        """Remove the most recent warning from a member's record."""
        record = self.state.get("users", {}).get(str(membro.id))
        if not record or record.get("warns", 0) <= 0:
            await ctx.send(f"**{membro.display_name}** não possui avisos para remover.")
            return

        record["warns"] -= 1
        if record.get("motivos"):
            record["motivos"].pop()
        self._persist()

        await ctx.send(
            f"✅ Último aviso de **{membro.display_name}** removido (restam {record['warns']}/{Config.WARN_LIMIT})."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

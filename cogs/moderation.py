"""
Moderation and channel cleanup cog.
Includes kick, ban, unban, mute/unmute, 3-strike warning system, and bulk message clear.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config, load_json, save_json


class Moderation(commands.Cog):
    """Server moderation and bulk message cleanup commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.MODERATION_FILE
        self.state: Dict[str, Any] = load_json(self.file_path, default={"users": {}})

    def _persist(self) -> None:
        save_json(self.file_path, self.state)

    @staticmethod
    def _check_hierarchy(ctx: commands.Context, target: discord.Member) -> Optional[str]:
        if target.id == ctx.author.id:
            return "❌ Você não pode aplicar esta ação em si mesmo."
        if ctx.guild and target.id == ctx.guild.owner_id:
            return "❌ Não é possível moderar o dono do servidor."
        if (
            isinstance(ctx.author, discord.Member)
            and ctx.guild
            and ctx.author.id != ctx.guild.owner_id
            and target.top_role >= ctx.author.top_role
        ):
            return "❌ Esse membro possui um cargo igual ou superior ao seu."
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
        """Kick a member from the server."""
        err = self._check_hierarchy(ctx, membro)
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
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Erro ao expulsar: {exc}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Ban a member from the server."""
        err = self._check_hierarchy(ctx, membro)
        if err:
            await ctx.send(err)
            return

        try:
            await membro.ban(reason=f"{ctx.author}: {razao}", delete_message_seconds=86400)
            embed = discord.Embed(
                title="🚫 Membro banido",
                description=f"**{membro}** foi banido do servidor.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Razão", value=razao, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Erro ao banir: {exc}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, usuario: str) -> None:
        """Unban a user by username or Discord ID."""
        query = usuario.strip().lower()
        async for entry in ctx.guild.bans():
            if entry.user.name.lower() == query or str(entry.user.id) == query:
                try:
                    await ctx.guild.unban(entry.user, reason=f"Desbanido por {ctx.author}")
                    await ctx.send(f"✅ Banimento de **{entry.user}** removido.")
                    return
                except discord.HTTPException as exc:
                    await ctx.send(f"❌ Erro ao remover ban: {exc}")
                    return

        await ctx.send(f"❌ Usuário `{usuario}` não encontrado na lista de banimentos.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Mute a member in text channels using the configured mute role."""
        err = self._check_hierarchy(ctx, membro)
        if err:
            await ctx.send(err)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None:
            try:
                muted_role = await ctx.guild.create_role(
                    name=Config.MUTE_ROLE_NAME,
                    reason="Cargo para membros silenciados",
                )
                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(muted_role, send_messages=False)
            except discord.HTTPException as exc:
                await ctx.send(f"❌ Não foi possível criar o cargo `{Config.MUTE_ROLE_NAME}`: {exc}")
                return

        try:
            await membro.add_roles(muted_role, reason=f"{ctx.author}: {razao}")
            await ctx.send(f"🔇 **{membro.display_name}** foi silenciado ({razao}).")
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Erro ao silenciar: {exc}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, membro: discord.Member) -> None:
        """Remove the mute role from a member."""
        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None or muted_role not in membro.roles:
            await ctx.send(f"❌ **{membro.display_name}** não está silenciado.")
            return

        try:
            await membro.remove_roles(muted_role, reason=f"Desmutado por {ctx.author}")
            await ctx.send(f"🔊 **{membro.display_name}** foi desmutado.")
        except discord.HTTPException as exc:
            await ctx.send(f"❌ Erro ao remover silenciamento: {exc}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem razão especificada",
    ) -> None:
        """Warn a member; reaching `Config.WARN_LIMIT` triggers an automatic ban."""
        err = self._check_hierarchy(ctx, membro)
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

        count = int(record["warns"])
        await ctx.send(
            f"⚠️ **{membro.display_name}** recebeu um aviso ({count}/{Config.WARN_LIMIT}) — Razão: *{razao}*"
        )

        if count >= Config.WARN_LIMIT:
            try:
                await membro.ban(reason=f"Atingiu {Config.WARN_LIMIT} avisos.")
                await ctx.send(f"🚫 **{membro}** atingiu {Config.WARN_LIMIT} avisos e foi banido.")
            except discord.HTTPException:
                pass

    @commands.command()
    async def warnings(
        self,
        ctx: commands.Context,
        membro: Optional[discord.Member] = None,
    ) -> None:
        """View warnings recorded for a member."""
        target = membro or ctx.author
        record = self.state.get("users", {}).get(str(target.id))
        if not record or not record.get("warns"):
            await ctx.send(f"**{target.display_name}** não possui avisos.")
            return

        embed = discord.Embed(
            title=f"⚠️ Avisos de {target.display_name} ({record['warns']}/{Config.WARN_LIMIT})",
            color=discord.Color.orange(),
        )
        for idx, item in enumerate(record.get("motivos", []), start=1):
            embed.add_field(
                name=f"#{idx}",
                value=f"{item['razao']} *(por {item['moderador']})*",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx: commands.Context, membro: discord.Member) -> None:
        """Remove the latest warning from a member."""
        record = self.state.get("users", {}).get(str(membro.id))
        if not record or record.get("warns", 0) <= 0:
            await ctx.send(f"**{membro.display_name}** não possui avisos para remover.")
            return

        record["warns"] -= 1
        if record.get("motivos"):
            record["motivos"].pop()
        self._persist()
        await ctx.send(f"✅ Aviso removido de **{membro.display_name}** ({record['warns']}/{Config.WARN_LIMIT}).")

    @commands.command(name="clear", aliases=["purge", "clean"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, quantidade: int = 20) -> None:
        """Bulk-delete up to `quantidade` recent messages in the channel."""
        if not 1 <= quantidade <= 200:
            await ctx.send("❌ Informe uma quantidade entre 1 e 200 mensagens.")
            return

        deleted = await ctx.channel.purge(limit=quantidade + 1)
        removed_count = max(0, len(deleted) - 1)
        await ctx.send(
            f"🧹 **{removed_count}** mensagens removidas.",
            delete_after=4.0,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

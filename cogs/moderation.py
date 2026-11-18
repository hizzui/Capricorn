"""
Módulo de Contramedidas ICE, Segurança da Sub-rede e Expurgo de Canal.
Inclui kick, ban, unban, mute/unmute, sistema de 3 strikes (Soulkiller Auto-Ban) e clear.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from config import Config, build_embed, load_json, save_json


class Moderation(commands.Cog):
    """Protocolos de segurança ICE, controle disciplinar e limpeza de canais."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.file_path = Config.MODERATION_FILE
        self.state: Dict[str, Any] = load_json(self.file_path, default={"users": {}})

    def _persist(self) -> None:
        save_json(self.file_path, self.state)

    @staticmethod
    def _check_hierarchy(ctx: commands.Context, target: discord.Member) -> Optional[discord.Embed]:
        if target.id == ctx.author.id:
            return build_embed(
                title="⛔ OPERAÇÃO BLOQUEADA // AUTO-ALVO",
                description="Os protocolos ICE impedem a aplicação desta diretriz em seu próprio registro.",
                color=Config.COLOR_ERROR,
            )
        if ctx.guild and target.id == ctx.guild.owner_id:
            return build_embed(
                title="⛔ OPERAÇÃO BLOQUEADA // IMUNIDADE EXECUTIVA",
                description="Não é possível aplicar contramedidas contra o Diretor Executivo (Owner) da sub-rede.",
                color=Config.COLOR_ERROR,
            )
        if (
            isinstance(ctx.author, discord.Member)
            and ctx.guild
            and ctx.author.id != ctx.guild.owner_id
            and target.top_role >= ctx.author.top_role
        ):
            return build_embed(
                title="⛔ HIERARQUIA CORPORATIVA INSUFICIENTE",
                description="O alvo possui nível de credencial igual ou superior ao seu.",
                color=Config.COLOR_ERROR,
            )
        return None

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem diretriz especificada",
    ) -> None:
        """Desconecta forçadamente (expulsa) um membro da sub-rede."""
        err_embed = self._check_hierarchy(ctx, membro)
        if err_embed:
            await ctx.send(embed=err_embed)
            return

        try:
            await membro.kick(reason=f"[CAPRICORN ICE] {ctx.author}: {razao}")
            embed = build_embed(
                title="⚡ DESCONEXÃO FORÇADA // KICK",
                description=f"O cidadão **{membro}** teve seu vínculo com a sub-rede encerrado.",
                color=Config.COLOR_WARNING,
                footer_extra="ICE COUNTERMEASURES",
            )
            embed.add_field(name="Alvo", value=f"`{membro}` (`{membro.id}`)", inline=True)
            embed.add_field(name="Agente Executor", value=ctx.author.mention, inline=True)
            embed.add_field(name="Diretriz / Razão", value=razao, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            embed = build_embed(
                title="❌ FALHA NA CONTRAMEDIDA",
                description=f"Não foi possível desconectar o alvo: `{exc}`",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem diretriz especificada",
    ) -> None:
        """Neutraliza e bane permanentemente um membro da sub-rede."""
        err_embed = self._check_hierarchy(ctx, membro)
        if err_embed:
            await ctx.send(embed=err_embed)
            return

        try:
            await membro.ban(
                reason=f"[CAPRICORN BLACKWALL] {ctx.author}: {razao}",
                delete_message_seconds=86400,
            )
            embed = build_embed(
                title="🩸 NEUTRALIZAÇÃO BLACKWALL // BANIMENTO",
                description=f"O registro de **{membro}** foi permanentemente bloqueado nesta sub-rede.",
                color=Config.COLOR_ERROR,
                footer_extra="SOULKILLER PROTOCOL",
            )
            embed.add_field(name="Alvo Neutralizado", value=f"`{membro}` (`{membro.id}`)", inline=True)
            embed.add_field(name="Agente Executor", value=ctx.author.mention, inline=True)
            embed.add_field(name="Diretriz / Razão", value=razao, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            embed = build_embed(
                title="❌ FALHA NA NEUTRALIZAÇÃO",
                description=f"Erro ao aplicar protocolo de banimento: `{exc}`",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, usuario: str) -> None:
        """Revoga o bloqueio Blackwall de um usuário pelo nome ou ID."""
        query = usuario.strip().lower()
        async for entry in ctx.guild.bans():
            if entry.user.name.lower() == query or str(entry.user.id) == query:
                try:
                    await ctx.guild.unban(
                        entry.user,
                        reason=f"[CAPRICORN ICE] Revogado por {ctx.author}",
                    )
                    embed = build_embed(
                        title="🔓 BLOQUEIO ICE REVOGADO // UNBAN",
                        description=f"O cidadão **{entry.user}** teve suas credenciais de acesso restauradas.",
                        color=Config.COLOR_SUCCESS,
                        footer_extra=f"Autorizado por {ctx.author.display_name}",
                    )
                    await ctx.send(embed=embed)
                    return
                except discord.HTTPException as exc:
                    embed = build_embed(
                        title="❌ FALHA AO REVOGAR BLOQUEIO",
                        description=f"Erro de comunicação com o gateway: `{exc}`",
                        color=Config.COLOR_ERROR,
                    )
                    await ctx.send(embed=embed)
                    return

        embed = build_embed(
            title="🔍 REGISTRO NÃO LOCALIZADO",
            description=f"O identificador `{usuario}` não consta na lista de neutralizações da Blackwall.",
            color=Config.COLOR_WARNING,
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem diretriz especificada",
    ) -> None:
        """Corta a transmissão de texto de um membro na sub-rede."""
        err_embed = self._check_hierarchy(ctx, membro)
        if err_embed:
            await ctx.send(embed=err_embed)
            return

        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None:
            try:
                muted_role = await ctx.guild.create_role(
                    name=Config.MUTE_ROLE_NAME,
                    reason="[CAPRICORN ICE] Credencial de restrição de transmissão",
                )
                for channel in ctx.guild.text_channels:
                    await channel.set_permissions(muted_role, send_messages=False)
            except discord.HTTPException as exc:
                embed = build_embed(
                    title="❌ FALHA DE PROVISIONAMENTO",
                    description=f"Não foi possível criar o cargo `{Config.MUTE_ROLE_NAME}`: `{exc}`",
                    color=Config.COLOR_ERROR,
                )
                await ctx.send(embed=embed)
                return

        try:
            await membro.add_roles(muted_role, reason=f"[CAPRICORN ICE] {ctx.author}: {razao}")
            embed = build_embed(
                title="🔇 TRANSMISSÃO NEURAL BLOQUEADA // MUTE",
                description=f"Os canais de comunicação de **{membro.display_name}** foram silenciados.",
                color=Config.COLOR_WARNING,
                footer_extra="COMM-LINK JAMMER",
            )
            embed.add_field(name="Alvo", value=membro.mention, inline=True)
            embed.add_field(name="Agente Executor", value=ctx.author.mention, inline=True)
            embed.add_field(name="Diretriz / Razão", value=razao, inline=False)
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            embed = build_embed(
                title="❌ ERRO DE BLOQUEIO",
                description=f"Falha ao silenciar transmissão: `{exc}`",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx: commands.Context, membro: discord.Member) -> None:
        """Restabelece a transmissão de texto de um membro silenciado."""
        muted_role = discord.utils.get(ctx.guild.roles, name=Config.MUTE_ROLE_NAME)
        if muted_role is None or muted_role not in membro.roles:
            embed = build_embed(
                title="⚠️ OPERAÇÃO REDUNDANTE",
                description=f"O cidadão **{membro.display_name}** não possui restrição de transmissão ativa.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        try:
            await membro.remove_roles(muted_role, reason=f"[CAPRICORN ICE] Restaurado por {ctx.author}")
            embed = build_embed(
                title="🔊 TRANSMISSÃO RESTABELECIDA // UNMUTE",
                description=f"O link de comunicação de **{membro.display_name}** foi reativado com sucesso.",
                color=Config.COLOR_SUCCESS,
                footer_extra=f"Autorizado por {ctx.author.display_name}",
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as exc:
            embed = build_embed(
                title="❌ ERRO AO RESTAURAR LINK",
                description=f"Não foi possível remover o silenciamento: `{exc}`",
                color=Config.COLOR_ERROR,
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        membro: discord.Member,
        *,
        razao: str = "Sem diretriz especificada",
    ) -> None:
        """Registra uma infração disciplinar; atingir `Config.WARN_LIMIT` aciona o Auto-Ban Soulkiller."""
        err_embed = self._check_hierarchy(ctx, membro)
        if err_embed:
            await ctx.send(embed=err_embed)
            return

        users = self.state.setdefault("users", {})
        record = users.setdefault(str(membro.id), {"warns": 0, "motivos": []})
        record["warns"] += 1
        record["motivos"].append(
            {
                "razao": razao,
                "moderador": str(ctx.author),
                "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
        )
        self._persist()

        count = int(record["warns"])
        embed = build_embed(
            title="⚠️ INFRAÇÃO CORPORATIVA REGISTRADA // WARN",
            description=f"Uma advertência disciplinar foi anexada ao dossiê de **{membro.display_name}**.",
            color=Config.COLOR_WARNING,
            footer_extra="ARASAKA COMPLIANCE DIVISION",
        )
        embed.add_field(name="Cidadão", value=membro.mention, inline=True)
        embed.add_field(name="Nível de Risco", value=f"**`{count} / {Config.WARN_LIMIT}`**", inline=True)
        embed.add_field(name="Agente Executor", value=ctx.author.mention, inline=True)
        embed.add_field(name="Diretriz Violada", value=razao, inline=False)
        await ctx.send(embed=embed)

        if count >= Config.WARN_LIMIT:
            try:
                await membro.ban(
                    reason=f"[SOULKILLER AUTO-BAN] Atingiu o limite de {Config.WARN_LIMIT} infrações."
                )
                ban_embed = build_embed(
                    title="🩸 PROTOCOLO SOULKILLER ACIONADO // AUTO-BAN",
                    description=(
                        f"**{membro}** atingiu o limite crítico de **`{Config.WARN_LIMIT}/{Config.WARN_LIMIT}`** "
                        "infrações e foi automaticamente neutralizado da sub-rede."
                    ),
                    color=Config.COLOR_ERROR,
                    footer_extra="AUTOMATED BLACKWALL DEFENSE",
                )
                await ctx.send(embed=ban_embed)
            except discord.HTTPException:
                pass

    @commands.command()
    async def warnings(
        self,
        ctx: commands.Context,
        membro: Optional[discord.Member] = None,
    ) -> None:
        """Consulta o histórico de infrações registradas para um membro."""
        target = membro or ctx.author
        record = self.state.get("users", {}).get(str(target.id))
        if not record or not record.get("warns"):
            embed = build_embed(
                title="🟢 FICHA DISCIPLINAR LIMPA",
                description=f"O cidadão **{target.display_name}** não possui infrações registradas na sub-rede.",
                color=Config.COLOR_SUCCESS,
            )
            await ctx.send(embed=embed)
            return

        embed = build_embed(
            title=f"📋 HISTÓRICO DE INFRAÇÕES // {target.display_name.upper()}",
            description=f"Nível de risco acumulado: **`{record['warns']} / {Config.WARN_LIMIT}`**",
            color=Config.COLOR_WARNING,
            footer_extra="ARASAKA COMPLIANCE RECORDS",
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        for idx, item in enumerate(record.get("motivos", []), start=1):
            data_str = item.get("data", "Registro legado")
            embed.add_field(
                name=f"Infração #{idx:02d} • {data_str}",
                value=f"**Diretriz:** {item['razao']}\n**Executor:** `{item['moderador']}`",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx: commands.Context, membro: discord.Member) -> None:
        """Remove a infração mais recente do dossiê de um membro."""
        record = self.state.get("users", {}).get(str(membro.id))
        if not record or record.get("warns", 0) <= 0:
            embed = build_embed(
                title="⚠️ NENHUMA INFRAÇÃO ATIVA",
                description=f"**{membro.display_name}** não possui registros disciplinares para remoção.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        record["warns"] -= 1
        removed = record["motivos"].pop() if record.get("motivos") else None
        self._persist()

        embed = build_embed(
            title="✅ INFRAÇÃO EXPURGADA // UNWARN",
            description=f"O registro disciplinar mais recente de **{membro.display_name}** foi removido.",
            color=Config.COLOR_SUCCESS,
            footer_extra=f"Autorizado por {ctx.author.display_name}",
        )
        embed.add_field(
            name="Nível de Risco Atual",
            value=f"**`{record['warns']} / {Config.WARN_LIMIT}`**",
            inline=True,
        )
        if removed:
            embed.add_field(name="Registro Removido", value=removed.get("razao", "N/A"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="clear", aliases=["purge", "clean"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, quantidade: int = 20) -> None:
        """Expurga em massa até `quantidade` transmissões recentes do canal (1 a 200)."""
        if not 1 <= quantidade <= 200:
            embed = build_embed(
                title="⚠️ PARÂMETRO DE EXPURGO INVÁLIDO",
                description="Especifique um volume entre **1** e **200** transmissões para limpeza.",
                color=Config.COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        deleted = await ctx.channel.purge(limit=quantidade + 1)
        removed_count = max(0, len(deleted) - 1)
        embed = build_embed(
            title="🧹 EXPURGO DE DADOS CONCLUÍDO",
            description=f"**`{removed_count}`** transmissões foram permanentemente removidas deste canal.",
            color=Config.COLOR_SUCCESS,
            footer_extra=f"Executado por {ctx.author.display_name}",
        )
        await ctx.send(embed=embed, delete_after=4.5)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))

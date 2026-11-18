"""
Configuração central, paleta visual Project Capricorn (Cyberpunk 2 / Edgerunners 2)
e utilitários de persistência JSON.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import discord
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "").strip()
    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Identidade Visual — Project Capricorn (Arasaka R&D // Engram Construct)
    BOT_NAME: str = "CAPRICORN // SYS-ENGRAM"
    BOT_TAGLINE: str = "PROJECT CAPRICORN • ARASAKA R&D TELEMETRY"
    BOT_VERSION: str = "v2.5.0-ORION"
    BOT_BANNER_URL: str = (
        "https://raw.githubusercontent.com/hizzui/NewDiscordBot/main/assets/capricorn_banner.jpg"
    )

    # Paleta de Cores Cyberpunk (Hex)
    COLOR_PRIMARY: int = 0xDC143C   # Carmesim Capricorn / Engram Core
    COLOR_SUCCESS: int = 0x00F0FF   # Ciano NetWatch / Operação Concluída
    COLOR_WARNING: int = 0xFCEE09   # Amarelo Cyberpunk / Alerta de Telemetria
    COLOR_ERROR: int = 0xFF003C     # Vermelho Blackwall / Violação de Protocolo
    COLOR_GOLD: int = 0xD4AF37      # Ouro Executivo Arasaka
    COLOR_NEUTRAL: int = 0x1A1A24   # Obsidiana Neural

    # Configurações de Moderação (Protocolos ICE)
    WARN_LIMIT: int = 3
    MUTE_ROLE_NAME: str = "Mutado"

    # Configurações Econômicas (Eurodólares — €$)
    CURRENCY_NAME: str = "Eurodólares"
    CURRENCY_SYMBOL: str = "€$"
    STARTING_BALANCE: int = 100
    PAYDAY_AMOUNT: int = 100
    PAYDAY_COOLDOWN_HOURS: int = 24
    SLOTS_MIN_BET: int = 10
    SLOTS_MAX_BET: int = 1000

    # Arquivos locais de estado JSON
    MODERATION_FILE: Path = DATA_DIR / "moderation.json"
    ECONOMY_FILE: Path = DATA_DIR / "economy.json"


def format_currency(amount: int) -> str:
    """Formata um valor inteiro no padrão de Eurodólares (€$ 1,000)."""
    return f"{Config.CURRENCY_SYMBOL} {amount:,}"


def build_embed(
    title: str,
    description: Optional[str] = None,
    *,
    color: int = Config.COLOR_PRIMARY,
    footer_extra: Optional[str] = None,
) -> discord.Embed:
    """Cria um Embed padronizado com a identidade visual corporativa da Capricorn."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color(color),
        timestamp=datetime.now(timezone.utc),
    )
    footer_text = Config.BOT_TAGLINE
    if footer_extra:
        footer_text = f"{footer_extra} • {footer_text}"
    embed.set_footer(text=footer_text)
    return embed


def load_json(path: Path, default: Any) -> Any:
    """Carrega dados JSON do disco ou retorna uma cópia limpa de `default`."""
    if not path.exists():
        return json.loads(json.dumps(default))
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(default))


def save_json(path: Path, data: Any) -> None:
    """Salva dados JSON em disco de forma atômica usando arquivo temporário."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    tmp.replace(path)

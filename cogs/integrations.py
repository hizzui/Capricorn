"""
Public API integrations cog (`!anime`, `!crypto`, `!weather`, `!github`, `!define`).
Uses free, zero-key public REST APIs via async `aiohttp` requests.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import aiohttp
from discord.ext import commands

from config import Config, build_embed

CRYPTO_ALIASES = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "dot": "polkadot",
    "ltc": "litecoin",
    "matic": "matic-network",
}

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


class Integrations(commands.Cog):
    """Live data commands powered by public REST APIs (no API keys required)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self) -> None:
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": f"{Config.BOT_NAME}/{Config.BOT_VERSION} (Discord Bot)"},
        )

    async def cog_unload(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def _get_json(self, url: str) -> Optional[dict | list]:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"User-Agent": f"{Config.BOT_NAME}/{Config.BOT_VERSION}"},
            )
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError):
            return None

    @commands.command()
    async def anime(self, ctx: commands.Context, *, query: str) -> None:
        """Search anime details via the Jikan (MyAnimeList) Public API."""
        url = f"https://api.jikan.moe/v4/anime?q={quote(query)}&limit=1&sfw=true"
        data = await self._get_json(url)
        if not isinstance(data, dict) or not data.get("data"):
            await ctx.send(
                embed=build_embed(
                    "Anime Not Found",
                    f"No results found for `{query}`.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        item = data["data"][0]
        title = item.get("title_english") or item.get("title") or "Unknown Title"
        synopsis = item.get("synopsis") or "No synopsis available."
        if len(synopsis) > 380:
            synopsis = synopsis[:377].rstrip() + "..."

        embed = build_embed(
            title=title,
            description=synopsis,
            color=Config.COLOR_PRIMARY,
            footer="Source: MyAnimeList (Jikan API)",
        )
        if item.get("url"):
            embed.url = item["url"]

        image_url = item.get("images", {}).get("jpg", {}).get("large_image_url")
        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.add_field(name="Score", value=f"`{item.get('score') or 'N/A'}`", inline=True)
        embed.add_field(name="Episodes", value=f"`{item.get('episodes') or '?'}`", inline=True)
        embed.add_field(name="Status", value=f"`{item.get('status') or 'N/A'}`", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def crypto(self, ctx: commands.Context, coin: str = "bitcoin") -> None:
        """Fetch live cryptocurrency prices (USD & BRL) via CoinGecko Public API."""
        key = coin.strip().lower()
        coin_id = CRYPTO_ALIASES.get(key, key)
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            f"?ids={quote(coin_id)}&vs_currencies=usd,brl&include_24hr_change=true"
        )
        data = await self._get_json(url)
        if not isinstance(data, dict) or coin_id not in data:
            await ctx.send(
                embed=build_embed(
                    "Asset Not Found",
                    f"Could not find market data for `{coin}`. Try `btc`, `eth`, `sol`, or a full CoinGecko ID.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        info = data[coin_id]
        usd = info.get("usd", 0)
        brl = info.get("brl", 0)
        change = info.get("usd_24h_change", 0.0) or 0.0
        color = Config.COLOR_SUCCESS if change >= 0 else Config.COLOR_ERROR

        embed = build_embed(
            title=f"Market Quote — {coin_id.capitalize()}",
            color=color,
            footer="Source: CoinGecko Public API",
        )
        embed.add_field(name="USD", value=f"**`${usd:,.2f}`**", inline=True)
        embed.add_field(name="BRL", value=f"**`R$ {brl:,.2f}`**", inline=True)
        embed.add_field(name="24h Change", value=f"`{change:+.2f}%`", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def weather(self, ctx: commands.Context, *, city: str) -> None:
        """Fetch real-time weather conditions for any city via Open-Meteo API."""
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote(city)}&count=1&language=en&format=json"
        geo_data = await self._get_json(geo_url)
        if not isinstance(geo_data, dict) or not geo_data.get("results"):
            await ctx.send(
                embed=build_embed(
                    "Location Not Found",
                    f"Could not resolve coordinates for `{city}`.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        place_name = f"{loc['name']}, {loc.get('country', '')}".strip(", ")

        wx_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code"
        )
        wx_data = await self._get_json(wx_url)
        if not isinstance(wx_data, dict) or "current" not in wx_data:
            await ctx.send(
                embed=build_embed(
                    "Service Unavailable",
                    "Weather telemetry is temporarily unreachable.",
                    color=Config.COLOR_ERROR,
                )
            )
            return

        cur = wx_data["current"]
        condition = WMO_WEATHER_CODES.get(cur.get("weather_code", -1), "Variable conditions")

        embed = build_embed(
            title=f"Weather — {place_name}",
            description=f"Condition: **{condition}**",
            color=Config.COLOR_PRIMARY,
            footer="Source: Open-Meteo API",
        )
        embed.add_field(name="Temperature", value=f"`{cur.get('temperature_2m')} °C`", inline=True)
        embed.add_field(name="Feels Like", value=f"`{cur.get('apparent_temperature')} °C`", inline=True)
        embed.add_field(name="Humidity", value=f"`{cur.get('relative_humidity_2m')}%`", inline=True)
        embed.add_field(name="Wind Speed", value=f"`{cur.get('wind_speed_10m')} km/h`", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="github", aliases=["gh"])
    async def github(self, ctx: commands.Context, username: str) -> None:
        """Inspect a public GitHub profile via the GitHub REST API."""
        url = f"https://api.github.com/users/{quote(username)}"
        data = await self._get_json(url)
        if not isinstance(data, dict) or "login" not in data:
            await ctx.send(
                embed=build_embed(
                    "GitHub User Not Found",
                    f"No public GitHub profile found for `{username}`.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        display_name = data.get("name") or data["login"]
        embed = build_embed(
            title=f"GitHub — {display_name} (@{data['login']})",
            description=data.get("bio") or "No bio provided.",
            color=Config.COLOR_PRIMARY,
            footer="Source: GitHub REST API",
        )
        if data.get("html_url"):
            embed.url = data["html_url"]
        if data.get("avatar_url"):
            embed.set_thumbnail(url=data["avatar_url"])

        embed.add_field(name="Public Repos", value=f"`{data.get('public_repos', 0)}`", inline=True)
        embed.add_field(name="Followers", value=f"`{data.get('followers', 0):,}`", inline=True)
        embed.add_field(name="Following", value=f"`{data.get('following', 0):,}`", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="define", aliases=["dict"])
    async def define(self, ctx: commands.Context, *, word: str) -> None:
        """Look up an English word definition via the Free Dictionary API."""
        clean_word = word.strip().lower()
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(clean_word)}"
        data = await self._get_json(url)
        if not isinstance(data, list) or not data:
            await ctx.send(
                embed=build_embed(
                    "Definition Not Found",
                    f"No dictionary entry found for `{word}`.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        entry = data[0]
        phonetic = entry.get("phonetic") or ""
        meanings = entry.get("meanings", [])
        if not meanings:
            await ctx.send(
                embed=build_embed(
                    "Definition Not Found",
                    f"No definitions available for `{word}`.",
                    color=Config.COLOR_WARNING,
                )
            )
            return

        first_meaning = meanings[0]
        part_of_speech = first_meaning.get("partOfSpeech", "term")
        definitions = first_meaning.get("definitions", [])
        definition_text = definitions[0].get("definition", "N/A") if definitions else "N/A"
        example_text = definitions[0].get("example") if definitions else None

        title = f"{entry.get('word', clean_word)} {phonetic}".strip()
        desc = f"*({part_of_speech})* {definition_text}"
        if example_text:
            desc += f"\n\n**Example:** *\"{example_text}\"*"

        embed = build_embed(
            title=title,
            description=desc,
            color=Config.COLOR_PRIMARY,
            footer="Source: Free Dictionary API",
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Integrations(bot))

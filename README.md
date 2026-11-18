# NewDiscordBot (NDB)

<img width="736" height="414" alt="NDB Bot Banner" src="https://github.com/user-attachments/assets/6ce3a2a0-39e4-4222-95b0-37da2225ebec" />

A multi-purpose Discord bot written in **Python 3.10+** with **`discord.py 2.3.2`**.

I built this project using `discord.py`'s `Cog` extension system so each domain (moderation, virtual economy, custom guild triggers, channel cleanup, trivia, and Twitch stream alerts) stays isolated in its own module under `cogs/` and persists state locally via atomic JSON writes in `data/`.

---

## Project Layout

```text
NewDiscordBot/
├── cogs/
│   ├── cleanup.py       # Channel history purging & bulk message deletion (!purge, !clean, !clear)
│   ├── customcom.py     # Per-guild custom text commands with placeholder variables (!customcom)
│   ├── economy.py       # Credit balances, transfers, daily !payday, and 3-reel !slots
│   ├── fun.py           # Dice roller, coin flip, reaction polls, and AST-safe math evaluator (!calc)
│   ├── general.py       # Latency check, basic utilities, and categorized !ajuda (!help) embed
│   ├── info.py          # Member and guild diagnostic embeds (!user, !servidor, !avatar)
│   ├── moderation.py    # Role-checked kick/ban/unban/mute and 3-strike warning system
│   ├── streams.py       # Background Twitch Helix API polling and live notification embeds
│   └── trivia.py        # Reaction-based trivia rounds with persistent leaderboard
├── utils/
│   ├── __init__.py
│   └── storage.py       # Atomic temp-file JSON read/write helpers for local state
├── config.py            # Environment configuration, constants, and data file paths
├── logging_config.py    # Console + 10 MB rotating file logger setup
├── main.py              # NDBBot subclass, extension loader (setup_hook), and presence handler
├── requirements.txt
└── .env.example
```

---

## Key Implementation Details

- **Async Extension Loading (`setup_hook`)**: `NDBBot` subclasses `commands.Bot` and loads all modules in `cogs/` inside `setup_hook()` before the gateway connection becomes ready.
- **Atomic Local Persistence (`utils/storage.py`)**: Stateful modules (economy balances, warning records, custom guild commands, tracked streams, and trivia scores) write to `.tmp` files first and replace the target JSON atomically so an unexpected shutdown never leaves half-written files.
- **Safe Expression Evaluator (`cogs/fun.py`)**: The `!calc` command parses arithmetic expressions through Python's `ast` module rather than calling `eval()`, blocking arbitrary code execution and capping large exponents.
- **Optional Twitch Helix Polling (`cogs/streams.py`)**: The bot boots cleanly with only `DISCORD_TOKEN` configured. If `TWITCH_CLIENT_ID` and `TWITCH_TOKEN` are present in `.env`, a background `tasks.loop` checks tracked channels every 15 minutes reusing a shared `aiohttp.ClientSession`.

---

## Command Overview (Default Prefix: `!`)

| Module | Commands | Description |
| :--- | :--- | :--- |
| **General** | `!ajuda` (`!help`), `!ping`, `!oi`, `!echo <text>` | Categorized command menu, WebSocket latency check, and basic text utilities. |
| **Moderation** | `!kick`, `!ban`, `!unban`, `!mute`, `!unmute`, `!warn`, `!warnings`, `!unwarn` | Enforces role hierarchy checks and auto-bans members who reach 3 warnings. |
| **Cleanup** | `!purge [n] [@user]`, `!clean [n]`, `!cleanup`, `!clear [n]` | Single-message filtering or chunked 100-message bulk deletion with auto-expiring confirmation embeds. |
| **Economy** | `!balance [@user]`, `!pay <@user> <amount>`, `!payday`, `!slots [bet]`, `!leaderboard` | Starting balance, 24h daily credit claims, peer transfers, and slot machine payouts. |
| **Trivia** | `!trivia`, `!trivia_score [@user]`, `!trivia_top` | 5-question multiple-choice quiz played via `1️⃣`–`4️⃣` reactions with a 10s per-question timer. |
| **Fun & Math** | `!dado [sides]`, `!moeda`, `!vote <question>`, `!calc <expr>` | N-sided dice roll, coin flip, thumbs-up/down poll, and AST arithmetic calculator. |
| **Custom Commands** | `!customcom create\|list\|show\|delete` | Per-server custom triggers supporting `{author}`, `{guild}`, and `{timestamp}` placeholders. |
| **Twitch Alerts** | `!stream add\|remove\|list\|check`, `!streamset channel\|show\|credentials` | Live status lookup and automated announcement embeds when tracked Twitch channels go live. |
| **Server Info** | `!user [@member]`, `!servidor`, `!avatar [@member]` | Member join dates, role lists, boost tier, and channel/member breakdowns. |

---

## Running Locally

1. **Clone the repository and create a virtual environment:**
   ```bash
   git clone https://github.com/hizzui/NewDiscordBot.git
   cd NewDiscordBot
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set your `DISCORD_TOKEN` (from the [Discord Developer Portal](https://discord.com/developers/applications)). Make sure **Message Content Intent** and **Server Members Intent** are enabled under the **Bot** tab.

4. **Start the bot:**
   ```bash
   python main.py
   ```

---

## License

Released under the [MIT License](LICENSE).

# NewDiscordBot (NDB)

<img width="736" height="414" alt="NDB Bot Banner" src="https://github.com/user-attachments/assets/6ce3a2a0-39e4-4222-95b0-37da2225ebec" />

A lightweight Discord bot written in **Python 3.10+** using **`discord.py 2.3.2`**.

Organized around three focused Cogs (`general`, `moderation`, and `economy`) with local JSON persistence in `data/`.

---

## Project Structure

```text
NewDiscordBot/
├── cogs/
│   ├── economy.py       # Virtual credits (!balance, !payday, !pay, !slots, !leaderboard)
│   ├── general.py       # Server/user info & utilities (!ping, !user, !servidor, !avatar, !dado, !moeda, !vote, !ajuda)
│   └── moderation.py    # Staff tools & message purge (!kick, !ban, !unban, !mute, !unmute, !warn, !warnings, !clear)
├── config.py            # Environment settings and atomic JSON read/write helpers
├── main.py              # Bot entrypoint and Cog loader
├── requirements.txt
└── .env.example
```

---

## Commands (Default Prefix: `!`)

| Category | Commands | Description |
| :--- | :--- | :--- |
| **General & Info** | `!ajuda` (`!help`), `!ping`, `!user [@member]`, `!servidor`, `!avatar [@member]` | Command reference, latency check, and member/server profile cards. |
| **Chat Utilities** | `!dado [sides]`, `!moeda`, `!vote <question>` | Dice roll, coin flip, and quick thumbs-up/down polls. |
| **Economy** | `!balance`, `!payday`, `!pay <@user> <amount>`, `!slots [bet]`, `!leaderboard` | Daily credit claims, peer transfers, slot machine, and top 10 ranking. |
| **Moderation** | `!kick`, `!ban`, `!unban`, `!mute`, `!unmute`, `!warn`, `!warnings`, `!unwarn`, `!clear [n]` | Role-checked moderation actions, 3-strike warning system, and channel message purge. |

---

## Setup

1. **Clone and create a virtual environment:**
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

3. **Configure `.env`:**
   ```bash
   cp .env.example .env
   ```
   Set your `DISCORD_TOKEN` in `.env` (make sure **Message Content Intent** and **Server Members Intent** are enabled in the Discord Developer Portal).

4. **Run:**
   ```bash
   python main.py
   ```

---

## License

[MIT](LICENSE)

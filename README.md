# NewDiscordBot

<img width="736" height="414" alt="NDB Bot Banner" src="https://github.com/user-attachments/assets/6ce3a2a0-39e4-4222-95b0-37da2225ebec" />

Discord bot written in Python (`discord.py 2.3`) split into three cogs: server moderation, a simple credit economy, and general server/member utility commands. State (balances and warning logs) is stored locally in `data/`.

## Commands

Default prefix is `!` (configurable in `.env`).

- **General:** `!ajuda` (`!help`), `!ping`, `!user [@member]`, `!servidor`, `!avatar [@member]`, `!dado [sides]`, `!moeda`, `!vote <question>`
- **Economy:** `!balance [@member]`, `!payday`, `!pay <@member> <amount>`, `!slots [bet]`, `!leaderboard`
- **Moderation:** `!kick`, `!ban`, `!unban`, `!mute`, `!unmute`, `!warn` (auto-bans at 3 warnings), `!warnings`, `!unwarn`, `!clear [count]`

## Setup

```bash
git clone https://github.com/hizzui/NewDiscordBot.git
cd NewDiscordBot
pip install -r requirements.txt
cp .env.example .env
```

Add your `DISCORD_TOKEN` to `.env` (make sure Message Content and Server Members intents are enabled in the Discord Developer Portal), then run:

```bash
python main.py
```

## License

[MIT](LICENSE)

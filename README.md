# 🩸 CAPRICORN // SYS-ENGRAM (`NewDiscordBot`)

<img width="736" height="414" alt="Capricorn Bot Banner" src="assets/capricorn_banner.jpg" />

> **"PROJECT CAPRICORN • ARASAKA R&D TELEMETRY // BLACKWALL DEFENSIVE CONSTRUCT"**

Bot profissional para Discord desenvolvido em **Python (`discord.py 2.3`)**, inspirado na identidade visual e narrativa da **Capricorn (Capri)** — o engrama experimental da divisão de P&D da Arasaka no universo de **Cyberpunk 2 / Cyberpunk: Edgerunners 2**.

Todas as respostas utilizam **Embeds padronizados de alta precisão**, paleta de cores corporativa (*Carmesim Capricorn*, *Ciano NetWatch*, *Ouro Executivo Arasaka* e *Vermelho Blackwall*), carimbos de tempo UTC e tratamento global de erros.

---

## ⚡ Arquitetura & Módulos (`cogs/`)

| Módulo | Arquivo | Descrição |
| :--- | :--- | :--- |
| **Telemetria & Sub-rede** | `cogs/general.py` | Diagnóstico de latência neural, dossiês biométricos Kiroshi, topologia do servidor, votações corporativas e terminal de ajuda. |
| **Terminal Financeiro (`€$`)** | `cogs/economy.py` | Economia baseada em **Eurodólares (`€$`)**, subsídio diário Arasaka (24h), transferências P2P criptografadas, cassino de Night City e ranking da elite corporativa. |
| **Contramedidas ICE** | `cogs/moderation.py` | Segurança de sub-rede com auditoria em Embeds: desconexão forçada (`kick`), neutralização Blackwall (`ban`/`unban`), bloqueio de transmissão (`mute`/`unmute`), sistema disciplinar de 3 strikes com **Auto-Ban Soulkiller** e expurgo de canal (`clear`). |

---

## 🛠️ Diretrizes & Comandos

O prefixo padrão é `!` (configurável via variável `COMMAND_PREFIX` no arquivo `.env`).

### 📡 01. Telemetria & Sub-rede
- `!ajuda` (`!help`, `!comandos`) — Exibe o terminal central de operações da Capricorn
- `!ping` — Diagnóstico de latência e integridade do link com o gateway
- `!user [@membro]` — Dossiê biométrico e credenciais do cidadão
- `!servidor` — Relatório de topologia e população da sub-rede local
- `!avatar [@membro]` — Captura óptica Kiroshi em alta resolução
- `!dado [lados]` · `!moeda` · `!vote <pauta>` — Ferramentas de simulação probabilística e consenso

### 💶 02. Terminal Financeiro (Eurodólares — `€$`)
- `!balance [@membro]` — Extrato da conta corporativa em Eurodólares
- `!payday` — Resgata o subsídio diário da Arasaka (`+€$ 100` a cada 24h)
- `!pay <@membro> <valor>` — Transferência neural de fundos entre cidadãos
- `!slots [aposta]` — Terminal de caça-níqueis de Night City (multiplicadores de `2x` e `15x`)
- `!leaderboard` — Ranking Top 10 da elite corporativa

### 🛡️ 03. Contramedidas ICE & Moderação
- `!kick <@membro> [diretriz]` — Desconexão forçada da sub-rede
- `!ban <@membro> [diretriz]` — Neutralização permanente via Blackwall
- `!unban <id|nome>` — Revogação de bloqueio ICE
- `!mute <@membro> [diretriz]` / `!unmute <@membro>` — Bloqueio e restauração de transmissão de texto
- `!warn <@membro> [diretriz]` — Registra infração corporativa (**3 infrações acionam o protocolo Soulkiller Auto-Ban**)
- `!warnings [@membro]` · `!unwarn <@membro>` — Consulta e expurgo de histórico disciplinar
- `!clear [1-200]` (`!purge`, `!clean`) — Expurgo em massa de transmissões do canal

---

## 🚀 Instalação & Execução

```bash
git clone https://github.com/hizzui/NewDiscordBot.git
cd NewDiscordBot
pip install -r requirements.txt
cp .env.example .env
```

Configure seu `DISCORD_TOKEN` no arquivo `.env` (certifique-se de ativar **Message Content Intent** e **Server Members Intent** no Discord Developer Portal) e inicie o construto:

```bash
python main.py
```

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).

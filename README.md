# Discord Security & Management Bot

A single-server Python 3.11+ bot using discord.py 2.x, SQLite, and python-dotenv. It includes persistent configuration, verification integration, tickets, reaction roles, moderation, logging, anti-spam, anti-raid, and conservative anti-nuke alerting.

## Install locally
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Set `DISCORD_TOKEN` and the numeric `GUILD_ID` in `.env`, then run `python bot.py`. SQLite is created automatically at `database/bot.db`; it is ignored by Git.

## Developer Portal and invite
Create an application at the Discord Developer Portal, add a bot, reset/copy its token into `.env`, and enable **Server Members Intent**, **Message Content Intent**, and **Message Content** only as used by this bot. Invite with the `bot` and `applications.commands` scopes and these least-privilege permissions: View Channels, Send Messages, Embed Links, Attach Files, Read Message History, Add Reactions, Manage Messages, Manage Channels, Manage Roles, Moderate Members, Kick Members, Ban Members, Manage Nicknames (optional), and View Audit Log. Do not grant Administrator. Put the bot role above Verified, Unverified, reaction roles, and members it must moderate; it cannot manage roles above itself or managed integrations.

## First setup
Create roles/channels, then run as administrator:
`/config verified-role`, `/config unverified-role`, `/config verification-channel`, `/config mod-log`, `/config ticket-category`, `/config ticket-log`, `/config support-role`, and `/config staff-role`. Configure `/rr add` mappings and `/ticket setup`. Set `/config raid-threshold` and `/config raid-window`. Add trusted administrators using `/config whitelist add`.

## Feature notes
- Verification assigns Unverified on join and starts the installed `discord.py-captcha` integration when a verification channel is configured. Test the installed package version in a staging server; package API changes are isolated in `cogs/verification.py`.
- Reaction roles use raw reaction events and survive restart. Staff roles, administrator roles, managed roles, and roles above the bot are rejected.
- Ticket transcripts are sent as private text files to the configured ticket log channel before the channel is deleted.
- Anti-raid only enables the persisted unverified lockdown flag and alerts staff; it does not mass-ban members. Anti-nuke alerts after four similar audit-log actions in 20 seconds and respects the whitelist.

## AWS EC2 / systemd
```bash
sudo adduser --system --group discordbot
sudo -u discordbot git clone <repository> /opt/discord-bot
sudo -u discordbot python3 -m venv /opt/discord-bot/venv
sudo -u discordbot /opt/discord-bot/venv/bin/pip install -r /opt/discord-bot/requirements.txt
sudo -u discordbot cp /opt/discord-bot/.env.example /opt/discord-bot/.env
sudo nano /opt/discord-bot/.env
```
Create `/etc/systemd/system/discordbot.service`:
```ini
[Unit]
Description=Discord security bot
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=discordbot
Group=discordbot
WorkingDirectory=/opt/discord-bot
ExecStart=/opt/discord-bot/venv/bin/python /opt/discord-bot/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
```
Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable discordbot
sudo systemctl start discordbot
sudo systemctl status discordbot
sudo journalctl -u discordbot -f
```
Back up `database/bot.db` securely; never commit `.env` or the database.

## Troubleshooting
- Commands missing: confirm `GUILD_ID`, `applications.commands`, and that the bot started successfully.
- Role errors: move the bot role above every managed role and avoid integration-managed roles.
- CAPTCHA unavailable: install the exact package from `requirements.txt`, configure a verification channel, and inspect `journalctl`; do not expose CAPTCHA answers.
- Audit/anti-nuke silent: grant View Audit Log and ensure the log channel is configured.
- Tickets fail: grant Manage Channels and configure a category/support role.
- Intents errors: enable the two privileged intents in the Developer Portal and restart.

#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-}"
APP_DIR="/opt/discord-bot"
BOT_USER="discordbot"
SERVICE_NAME="discordbot"

if [[ -z "$REPO_URL" ]]; then
    echo "Usage: sudo ./setup.sh <git-repository-url>"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "Run this script with sudo/root."
    exit 1
fi

echo "==> Updating system"
apt update
apt upgrade -y

echo "==> Installing dependencies"
apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    ca-certificates

echo "==> Creating bot user"
if ! id "$BOT_USER" &>/dev/null; then
    adduser --system --group --home "$APP_DIR" "$BOT_USER"
fi

echo "==> Preparing application directory"
mkdir -p "$APP_DIR"
chown "$BOT_USER:$BOT_USER" "$APP_DIR"

echo "==> Cloning repository"
if [[ -d "$APP_DIR/.git" ]]; then
    echo "Repository already exists; pulling latest changes."
    sudo -u "$BOT_USER" git -C "$APP_DIR" pull
else
    # Directory must be empty before cloning into it.
    rm -rf "${APP_DIR:?}/"*
    rm -rf "${APP_DIR:?}/".[!.]* "${APP_DIR:?}/"..?*
    sudo -u "$BOT_USER" git clone "$REPO_URL" "$APP_DIR"
fi

echo "==> Creating Python virtual environment"
sudo -u "$BOT_USER" python3 -m venv "$APP_DIR/venv"

echo "==> Installing Python dependencies"
sudo -u "$BOT_USER" "$APP_DIR/venv/bin/python" -m pip install --upgrade pip
sudo -u "$BOT_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Creating .env"
if [[ ! -f "$APP_DIR/.env" ]]; then
    if [[ -f "$APP_DIR/.env.example" ]]; then
        sudo -u "$BOT_USER" cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chmod 600 "$APP_DIR/.env"

        echo
        echo "IMPORTANT:"
        echo "Edit $APP_DIR/.env and set DISCORD_TOKEN and GUILD_ID."
    else
        echo "WARNING: .env.example was not found."
    fi
else
    echo ".env already exists; leaving it untouched."
fi

echo "==> Creating systemd service"

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Discord Security Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/python ${APP_DIR}/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "==> Setting permissions"
chown -R "$BOT_USER:$BOT_USER" "$APP_DIR"
chmod 600 "$APP_DIR/.env" 2>/dev/null || true

echo "==> Reloading systemd"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo
echo "=========================================="
echo " Installation complete"
echo "=========================================="
echo
echo "1. Edit your environment:"
echo "   sudo nano $APP_DIR/.env"
echo
echo "2. Start the bot:"
echo "   sudo systemctl start $SERVICE_NAME"
echo
echo "3. Check status:"
echo "   sudo systemctl status $SERVICE_NAME"
echo
echo "4. View logs:"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo


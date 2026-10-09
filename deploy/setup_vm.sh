#!/usr/bin/env bash
# Налаштування віртуальної машини під бота (Debian 12 / Ubuntu 22.04+).
# Запускати від root з папки, де лежать bot.py, problems.py, requirements.txt і цей скрипт:
#   sudo bash setup_vm.sh
set -euo pipefail

APP_DIR=/opt/mathbot
APP_USER=mathbot

echo "==> Пакети"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip

echo "==> Користувач і папка"
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR"

echo "==> Код бота"
cp -f "$(dirname "$0")/bot.py" "$(dirname "$0")/problems.py" "$(dirname "$0")/requirements.txt" "$APP_DIR/"

if [ ! -f "$APP_DIR/.env" ]; then
  echo "==> Створюю .env — встав туди токен: nano $APP_DIR/.env"
  printf 'BOT_TOKEN=PUT-YOUR-TOKEN-HERE\n' > "$APP_DIR/.env"
fi

echo "==> Python-оточення"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip -q
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

echo "==> Systemd-сервіс"
cp -f "$(dirname "$0")/mathbot.service" /etc/systemd/system/mathbot.service
systemctl daemon-reload
systemctl enable mathbot

chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "==> Старт"
systemctl restart mathbot
sleep 3
systemctl --no-pager -l status mathbot | head -n 15
echo
echo "Готово. Логи: journalctl -u mathbot -f"
echo "Якщо в .env ще стоїть placeholder — встав токен і: systemctl restart mathbot"

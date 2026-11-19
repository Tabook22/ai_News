#!/usr/bin/env bash
# Install/refresh the daily magazine job on the VPS.
# Run as root from /var/www/ainews:
#   bash deploy/install_daily_job.sh
set -euo pipefail

ROOT=/var/www/ainews
cd "$ROOT"

mkdir -p "$ROOT/logs"
chown -R www-data:www-data "$ROOT/logs"

install -m 0644 "$ROOT/deploy/ainews-daily.service" /etc/systemd/system/ainews-daily.service
install -m 0644 "$ROOT/deploy/ainews-daily.timer" /etc/systemd/system/ainews-daily.timer

systemctl daemon-reload
systemctl enable --now ainews-daily.timer

echo "Installed ainews-daily.timer"
systemctl list-timers ainews-daily.timer --no-pager

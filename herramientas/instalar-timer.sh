#!/bin/bash
# Activa la publicación automática (cada minuto) para el usuario actual. Ejecutar sin sudo.
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
DIR=~/.config/systemd/user
mkdir -p "$DIR"

cat > "$DIR/catalogo-publicar.service" <<UNIT
[Unit]
Description=Publicar catálogo en GitHub si hubo cambios

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 $RAIZ/herramientas/publicar.py
UNIT

cat > "$DIR/catalogo-publicar.timer" <<UNIT
[Unit]
Description=Revisar cambios del catálogo cada minuto

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now catalogo-publicar.timer
systemctl --user list-timers catalogo-publicar.timer --no-pager

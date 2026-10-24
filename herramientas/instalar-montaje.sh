#!/bin/bash
# Monta la carpeta compartida de la PC Windows (CENTRAL) en /mnt/catalogo-web, para que
# publicar.py lea de ahí productos.csv y las fotos.
# Ejecutar:  sudo bash herramientas/instalar-montaje.sh
set -e
USUARIO=${SUDO_USER:?Ejecutar con sudo desde tu usuario}
SERVIDOR=192.168.1.107      # IP de CENTRAL (conviene reservarla en el router)
RECURSO="//$SERVIDOR/Users/Public/Documents/CATALOGO-WEB-WSAPP"
PUNTO=/mnt/catalogo-web

apt-get install -y cifs-utils
mkdir -p "$PUNTO"

if ! grep -q " $PUNTO " /etc/fstab; then
  cat >> /etc/fstab <<FSTAB
# Catálogo web: carpeta compartida de CENTRAL (Windows)
$RECURSO $PUNTO cifs guest,uid=$(id -u "$USUARIO"),gid=$(id -g "$USUARIO"),file_mode=0664,dir_mode=0775,iocharset=utf8,nofail,_netdev,x-systemd.automount,x-systemd.mount-timeout=15 0 0
FSTAB
fi

systemctl daemon-reload
systemctl restart "$(systemd-escape -p --suffix=automount "$PUNTO")"
ls -la "$PUNTO/EDITAR"
echo
echo "Listo. productos.csv y fotos/ se editan en \\\\CENTRAL\\Users\\Public\\Documents\\CATALOGO-WEB-WSAPP\\EDITAR"

#!/bin/bash
# Comparte la carpeta editar/ en la red local para editar desde Windows.
# Ejecutar:  sudo bash herramientas/instalar-samba.sh
set -e
USUARIO=${SUDO_USER:?Ejecutar con sudo desde tu usuario}
CARPETA="$(cd "$(dirname "$0")/../editar" && pwd)"

apt-get install -y samba

if ! grep -q '^\[catalogo\]' /etc/samba/smb.conf; then
  cat >> /etc/samba/smb.conf <<CONF

[catalogo]
   comment = Catalogo Dual Time
   path = $CARPETA
   valid users = $USUARIO
   force user = $USUARIO
   read only = no
   create mask = 0664
   directory mask = 0775
   veto files = /.gitkeep/
CONF
fi

echo
echo "Elegí la contraseña para conectarse desde Windows (usuario: $USUARIO)"
smbpasswd -a "$USUARIO"
systemctl restart smbd
systemctl restart nmbd 2>/dev/null || true
if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then ufw allow samba; fi

echo
echo "Listo. En Windows: Equipo → Conectar a unidad de red → \\\\$(hostname)\\catalogo"
echo "                   (o \\\\$(hostname -I | awk '{print $1}')\\catalogo), usuario $USUARIO"

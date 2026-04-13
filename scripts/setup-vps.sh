#!/bin/bash
# Script de setup inicial para un VPS Ubuntu 24.04 (Hetzner o similar).
# Ejecutar como root: curl -sSL <url> | bash
# O copiar al servidor y ejecutar: bash setup-vps.sh

set -euo pipefail

echo "=== Actualizando sistema ==="
apt-get update && apt-get upgrade -y

echo "=== Instalando Docker ==="
curl -fsSL https://get.docker.com | sh

echo "=== Instalando Docker Compose plugin ==="
apt-get install -y docker-compose-plugin

echo "=== Creando usuario deploy ==="
if ! id "deploy" &>/dev/null; then
    useradd -m -s /bin/bash -G docker deploy
    echo "Usuario 'deploy' creado. Configura su clave SSH:"
    echo "  mkdir -p /home/deploy/.ssh"
    echo "  cp ~/.ssh/authorized_keys /home/deploy/.ssh/"
    echo "  chown -R deploy:deploy /home/deploy/.ssh"
fi

echo "=== Configurando firewall ==="
apt-get install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "=== Setup completo ==="
echo ""
echo "Siguientes pasos:"
echo "  1. Clonar el repo:  git clone <repo-url> /home/deploy/macrosnap"
echo "  2. Crear .env.prod:  cp .env.prod.example .env.prod && nano .env.prod"
echo "  3. Crear backend/.env:  cp backend/.env.example backend/.env && nano backend/.env"
echo "  4. Desplegar:  docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build"
echo "  5. Ver logs:  docker compose -f docker-compose.prod.yml logs -f"

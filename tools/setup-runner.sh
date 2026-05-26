#!/bin/bash
# GitHub Actions Self-Hosted Runner para OrangeFox NX733J
# Ejecutar en WSL Ubuntu 24.04

set -e

RUNNER_VERSION="2.322.0"
RUNNER_DIR="$HOME/actions-runner"
REPO="DrakiSama/orangeFox_device_nubia_nx733j"

if [ -z "$1" ]; then
    echo "Uso: $0 <TOKEN>"
    echo "Token disponible en: https://github.com/$REPO/settings/actions/runners"
    exit 1
fi

TOKEN="$1"

# 1. Instalar dependencias
echo "[*] Instalando dependencias..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    curl jq tar gzip libicu-dev libssl-dev liblttng-ust-dev \
    libkrb5-dev zlib1g-dev systemd

# 2. Descargar runner
echo "[*] Descargando runner v$RUNNER_VERSION..."
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

if [ ! -f "actions-runner-linux-x64-$RUNNER_VERSION.tar.gz" ]; then
    curl -sSLO "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
fi

# 3. Extraer
echo "[*] Extrayendo..."
tar xzf "actions-runner-linux-x64-$RUNNER_VERSION.tar.gz"

# 4. Configurar
echo "[*] Configurando runner para $REPO..."
./config.sh --url "https://github.com/$REPO" --token "$TOKEN" \
    --name "wsl-ubuntu-ofrp" \
    --labels "self-hosted,linux,x64,ubuntu" \
    --unattended \
    --replace

# 5. Instalar como servicio
echo "[*] Instalando servicio..."
sudo ./svc.sh install
sudo ./svc.sh start

echo ""
echo "[✔] Runner configurado e iniciado correctamente."
echo "    Ver estado: sudo ./svc.sh status"
echo "    Ver logs:   sudo journalctl -u actions.runner.* -f"

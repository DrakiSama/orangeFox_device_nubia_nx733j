#!/bin/bash
# Configuración completa: runner + dependencias para OrangeFox NX733J
# Ejecutar DENTRO de WSL Ubuntu

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_URL="https://github.com/DrakiSama/orangeFox_device_nubia_nx733j"

if [ -z "$1" ]; then
    echo "Uso: $0 <RUNNER_TOKEN>"
    echo ""
    echo "1. Ve a: https://github.com/DrakiSama/orangeFox_device_nubia_nx733j/settings/actions/runners"
    echo "2. Click 'New self-hosted runner' -> Linux -> x64"
    echo "3. Copia el token (--token XXX) y pásalo como argumento"
    exit 1
fi

TOKEN="$1"

echo "============================================"
echo " OrangeFox NX733J - Runner Setup (WSL)"
echo "============================================"
echo ""

# Paso 1: Dependencias
echo "[1/4] Instalando dependencias de build..."
bash "$SCRIPT_DIR/setup-deps.sh"

# Paso 2: Runner
echo "[2/4] Configurando GitHub Actions runner..."
bash "$SCRIPT_DIR/setup-runner.sh" "$TOKEN"

# Paso 3: Workspace
echo "[3/4] Creando workspace..."
mkdir -p ~/orangefox
echo "[*] Workspace: ~/orangefox"

# Paso 4: Verificación
echo "[4/4] Verificando..."
echo ""
echo "  Runner status:"
sudo "$HOME/actions-runner/svc.sh" status 2>/dev/null || echo "  - revisar con: sudo ~/actions-runner/svc.sh status"
echo ""
echo "  ccache:"
ccache --show-stats 2>/dev/null | head -5
echo ""
echo "============================================"
echo " Configuración completada."
echo " Ve a GitHub Actions y ejecuta el workflow."
echo "============================================"

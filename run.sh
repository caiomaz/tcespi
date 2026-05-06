#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; C='\033[0;36m'
B='\033[1m'; D='\033[2m'; X='\033[0m'

ok()   { echo -e "${G}  ✔  ${X}$*"; }
warn() { echo -e "${Y}  ⚠  ${X}$*"; }
err()  { echo -e "${R}  ✖  ${X}$*"; exit 1; }
info() { echo -e "${C}  ➜  ${X}$*"; }

PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    warn "Python 3.10+ não encontrado. Tentando instalar..."

    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y python3 python3-venv
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python
    elif command -v brew &>/dev/null; then
        brew install python@3
    else
        err "Não foi possível instalar Python automaticamente.\n  Instale Python 3.10+ e rode novamente: https://python.org/downloads"
    fi

    PYTHON=$(command -v python3 || command -v python || true)
    [[ -z "$PYTHON" ]] && err "Instalação falhou. Instale Python manualmente."
fi

ok "Python encontrado: $($PYTHON --version)"
exec "$PYTHON" "$SCRIPT_DIR/run.py" "$@"

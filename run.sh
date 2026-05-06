#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_FILE="$SCRIPT_DIR/.launcher_cache"

R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; C='\033[0;36m'
B='\033[1m'; D='\033[2m'; X='\033[0m'

ok()      { echo -e "${G}  ✔  ${X}$*"; }
warn()    { echo -e "${Y}  ⚠  ${X}$*"; }
err()     { echo -e "${R}  ✖  ${X}$*"; exit 1; }
info()    { echo -e "${C}  ➜  ${X}$*"; }
bold()    { echo -e "${B}$*${X}"; }
dim()     { echo -e "${D}$*${X}"; }
divider() { echo -e "${D}────────────────────────────────────────${X}"; }

confirm() {
    local msg="$1" default="${2:-y}"
    local prompt; [[ "$default" == "y" ]] && prompt="[Y/n]" || prompt="[y/N]"
    while true; do
        echo -ne "${B}  ?  ${X}${msg} ${D}${prompt}${X} "
        read -r answer
        answer="${answer:-$default}"
        case "${answer,,}" in
            y|yes) return 0 ;;
            n|no)  return 1 ;;
            *) warn "Responda y ou n." ;;
        esac
    done
}

cache_get() { grep -s "^$1=" "$CACHE_FILE" 2>/dev/null | cut -d= -f2- || true; }
cache_set() { grep -sv "^$1=" "$CACHE_FILE" 2>/dev/null > "$CACHE_FILE.tmp" || true; echo "$1=$2" >> "$CACHE_FILE.tmp"; mv "$CACHE_FILE.tmp" "$CACHE_FILE"; }

# ── header ────────────────────────────────────────────────────────────────────
clear
echo
bold "  🍺  Fodinha Mineira — Launcher"
divider
echo

# ── cache: já rodou com sucesso antes? ────────────────────────────────────────
CACHED_PYTHON="$(cache_get python_bin)"
if [[ -n "$CACHED_PYTHON" && -x "$CACHED_PYTHON" ]]; then
    cached_ver=$("$CACHED_PYTHON" --version 2>&1 | awk '{print $2}')
    ok "Python (cache): ${C}${CACHED_PYTHON}${X} ${D}${cached_ver}${X}"
    exec "$CACHED_PYTHON" "$SCRIPT_DIR/run.py" "$@"
fi

# ── procurar python ───────────────────────────────────────────────────────────
bold "  Python"; divider

PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
            PYTHON=$(command -v "$candidate")
            ok "Python encontrado: ${C}${PYTHON}${X} ${D}${ver}${X}"
            break
        else
            warn "Python encontrado mas versão insuficiente: ${D}${ver}${X} (precisa 3.10+)"
        fi
    fi
done

# ── instalar python se necessário ─────────────────────────────────────────────
if [[ -z "$PYTHON" ]]; then
    warn "Python 3.10+ não encontrado no sistema."
    echo

    # detectar gerenciador de pacotes
    PKG_MGR=""
    for mgr in apt-get dnf pacman brew; do
        if command -v "$mgr" &>/dev/null; then
            PKG_MGR="$mgr"
            break
        fi
    done

    if [[ -z "$PKG_MGR" ]]; then
        err "Nenhum gerenciador de pacotes reconhecido.\n\n  Instale Python 3.10+ manualmente:\n  ${D}https://python.org/downloads${X}"
    fi

    echo -e "  Gerenciador detectado: ${C}${PKG_MGR}${X}"

    # brew não precisa de sudo
    if [[ "$PKG_MGR" == "brew" ]]; then
        echo -e "  Comando: ${D}brew install python@3${X}"
        echo
        if confirm "Instalar Python via brew?"; then
            info "Instalando Python..."
            brew install python@3 || err "Falha na instalação. Tente manualmente."
        else
            err "Python é obrigatório. Abortado."
        fi
    else
        # precisa de sudo — verificar se está disponível
        if ! command -v sudo &>/dev/null; then
            err "sudo não encontrado. Instale Python 3.10+ manualmente:\n  ${D}https://python.org/downloads${X}"
        fi

        case "$PKG_MGR" in
            apt-get) pkgs="python3 python3-venv" ;;
            dnf)     pkgs="python3" ;;
            pacman)  pkgs="python" ;;
        esac

        echo -e "  Comando: ${D}sudo ${PKG_MGR} install ${pkgs}${X}"
        echo -e "  ${Y}Requer permissão de administrador (sudo).${X}"
        echo
        if confirm "Instalar Python agora? (será pedida sua senha sudo)"; then
            echo
            info "Iniciando instalação — pode ser solicitada sua senha:"
            echo

            if [[ "$PKG_MGR" == "apt-get" ]]; then
                sudo apt-get update -qq
                sudo apt-get install -y $pkgs || err "Falha na instalação."
            elif [[ "$PKG_MGR" == "dnf" ]]; then
                sudo dnf install -y $pkgs || err "Falha na instalação."
            elif [[ "$PKG_MGR" == "pacman" ]]; then
                sudo pacman -S --noconfirm $pkgs || err "Falha na instalação."
            fi
        else
            err "Python é obrigatório. Instale manualmente:\n  ${D}https://python.org/downloads${X}"
        fi
    fi

    # validar instalação
    for candidate in python3 python; do
        if command -v "$candidate" &>/dev/null; then
            ver=$("$candidate" --version 2>&1 | awk '{print $2}')
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
                PYTHON=$(command -v "$candidate")
                break
            fi
        fi
    done

    [[ -z "$PYTHON" ]] && err "Instalação concluída mas Python 3.10+ ainda não encontrado.\n  Reinicie o terminal e tente novamente."
    ok "Python instalado: ${C}${PYTHON}${X} ${D}$($PYTHON --version 2>&1 | awk '{print $2}')${X}"
fi

# ── salvar no cache e executar ────────────────────────────────────────────────
cache_set "python_bin" "$PYTHON"
echo
exec "$PYTHON" "$SCRIPT_DIR/run.py" "$@"

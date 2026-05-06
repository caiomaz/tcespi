#!/usr/bin/env python3
"""Launcher multiplataforma para Fodinha Mineira."""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
VENV_DIR = SCRIPT_DIR / ".venv"
BROWSER_SCRIPT = SCRIPT_DIR / "browser.py"
PIP_DEPS = ["pywebview"]

OS = platform.system()  # "Linux" | "Windows" | "Darwin"

# ── ANSI (desabilitado no Windows sem suporte) ────────────────────────────────
_use_color = OS != "Windows" or os.environ.get("TERM")
R = "\033[0;31m"  if _use_color else ""
G = "\033[0;32m"  if _use_color else ""
Y = "\033[1;33m"  if _use_color else ""
C = "\033[0;36m"  if _use_color else ""
B = "\033[1m"     if _use_color else ""
D = "\033[2m"     if _use_color else ""
X = "\033[0m"     if _use_color else ""

def info(msg):  print(f"{C}  ➜  {X}{msg}")
def ok(msg):    print(f"{G}  ✔  {X}{msg}")
def warn(msg):  print(f"{Y}  ⚠  {X}{msg}")
def err(msg):   print(f"{R}  ✖  {X}{msg}"); sys.exit(1)
def bold(msg):  print(f"{B}{msg}{X}")
def div():      print(f"{D}────────────────────────────────────────{X}")

def confirm(msg, default="y"):
    opts = "[Y/n]" if default == "y" else "[y/N]"
    while True:
        try:
            ans = input(f"{B}  ?  {X}{msg} {D}{opts}{X} ").strip().lower() or default
        except (EOFError, KeyboardInterrupt):
            print(); sys.exit(0)
        if ans in ("y", "yes"): return True
        if ans in ("n", "no"):  return False
        warn("Responda y ou n.")

def run(cmd, **kw):
    return subprocess.run(cmd, **kw)

def run_ok(cmd, **kw):
    r = run(cmd, **kw)
    if r.returncode != 0:
        err(f"Comando falhou: {' '.join(str(c) for c in cmd)}")

# ── PYTHON ────────────────────────────────────────────────────────────────────
def find_python():
    for candidate in ("python3", "python"):
        path = shutil.which(candidate)
        if not path:
            continue
        r = run([path, "--version"], capture_output=True, text=True)
        raw = (r.stdout or r.stderr).strip().split()[-1]
        try:
            major, minor, *_ = (int(x) for x in raw.split("."))
        except ValueError:
            continue
        if (major, minor) >= (3, 10):
            return path, f"Python {raw}"
    return None, None

# ── DEPENDÊNCIAS DE SISTEMA (Linux) ──────────────────────────────────────────
SYSTEM_DEPS = {
    "apt":    ["python3-gi", "python3-gi-cairo", "gir1.2-gtk-3.0",
               "gir1.2-webkit2-4.1"],
    "apt-get":["python3-gi", "python3-gi-cairo", "gir1.2-gtk-3.0",
               "gir1.2-webkit2-4.1"],
    "dnf":    ["python3-gobject", "webkit2gtk4.1"],
    "pacman": ["python-gobject", "webkit2gtk-4.1"],
    "zypper": ["python3-gobject", "python3-gobject-cairo", "webkit2gtk3"],
    "brew":   [],  # macOS — não precisa de system deps
}

def detect_pkg_manager():
    for mgr in SYSTEM_DEPS:
        if shutil.which(mgr):
            return mgr
    return None

def gi_importable(python_bin):
    r = run([python_bin, "-c", "import gi"], capture_output=True)
    return r.returncode == 0

def install_system_deps(mgr):
    pkgs = SYSTEM_DEPS.get(mgr, [])
    if not pkgs:
        return
    info(f"Instalando dependências de sistema via {C}{mgr}{X}...")
    if mgr == "pacman":
        cmd = ["sudo", mgr, "-S", "--noconfirm"] + pkgs
    elif mgr in ("apt", "apt-get"):
        run(["sudo", mgr, "update", "-qq"], capture_output=True)
        cmd = ["sudo", mgr, "install", "-y"] + pkgs
    elif mgr == "zypper":
        cmd = ["sudo", mgr, "install", "-y"] + pkgs
    else:
        cmd = ["sudo", mgr, "install", "-y"] + pkgs
    run_ok(cmd)

def check_linux_system_deps(python_bin):
    if gi_importable(python_bin):
        ok(f"PyGObject (gi) disponível")
        return
    warn("PyGObject (gi) não encontrado — necessário no Linux.")
    mgr = detect_pkg_manager()
    if not mgr:
        err(
            "Nenhum gerenciador de pacotes reconhecido.\n"
            "  Instale manualmente: python3-gi + webkit2gtk\n"
            "  Depois rode novamente."
        )
    pkgs = SYSTEM_DEPS[mgr or ""]
    print(f"  Pacotes: {D}{' '.join(pkgs)}{X}")
    if confirm(f"Instalar via {mgr} agora? (pode pedir senha sudo)"):
        install_system_deps(mgr)
        if not gi_importable(python_bin):
            err("Instalação falhou. Instale manualmente e tente novamente.")
        ok("PyGObject instalado.")
    else:
        err("Dependência ausente. Abortado.")

# ── VENV ──────────────────────────────────────────────────────────────────────
def venv_python():
    if OS == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"

def venv_pip():
    if OS == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"

def create_venv(python_bin):
    info(f"Criando venv em {C}{VENV_DIR}{X}...")
    cmd = [python_bin, "-m", "venv"]
    if OS == "Linux":
        cmd.append("--system-site-packages")
    cmd.append(str(VENV_DIR))
    run_ok(cmd)
    ok("Venv criado.")

def ensure_venv(python_bin):
    bold("  Ambiente virtual"); div()
    py = venv_python()

    if VENV_DIR.exists():
        if not py.exists():
            warn("Venv corrompido (executável ausente).")
            if confirm("Recriar venv?"):
                import shutil as _sh; _sh.rmtree(VENV_DIR)
                create_venv(python_bin)
            else:
                err("Venv inválido. Abortado.")
        else:
            ok(f"Venv existente: {C}{VENV_DIR}{X}")
    else:
        warn("Nenhum venv encontrado.")
        if confirm(f"Criar venv em '{VENV_DIR}'?"):
            create_venv(python_bin)
        else:
            err("Sem venv, não é possível continuar.")

    ver_r = run([str(py), "--version"], capture_output=True, text=True)
    ok(f"Venv ativado: {C}{(ver_r.stdout or ver_r.stderr).strip()}{X} em {D}{VENV_DIR}{X}")
    return py

# ── DEPENDÊNCIAS PIP ──────────────────────────────────────────────────────────
def ensure_pip_deps(pip_bin):
    bold("  Dependências"); div()
    missing = []
    for dep in PIP_DEPS:
        r = run([str(pip_bin), "show", dep], capture_output=True, text=True)
        if r.returncode == 0:
            ver = next((l.split()[-1] for l in r.stdout.splitlines() if l.startswith("Version")), "?")
            ok(f"{dep} {D}{ver}{X}")
        else:
            warn(f"{dep} {D}não instalado{X}")
            missing.append(dep)

    if missing:
        print()
        if confirm(f"Instalar: {' '.join(missing)}?"):
            info("Atualizando pip...")
            run([str(pip_bin), "install", "--upgrade", "pip", "-q"])
            for pkg in missing:
                info(f"Instalando {C}{pkg}{X}...")
                run_ok([str(pip_bin), "install", pkg])
                ok(f"{pkg} instalado.")
        else:
            err("Dependências ausentes. Abortado.")

    ok("Todas as dependências OK.")

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    os.system("cls" if OS == "Windows" else "clear")
    print()
    bold("  🍺  Fodinha Mineira — Launcher")
    div()
    print()

    # Python
    python_bin, python_label = find_python()
    if not python_bin:
        err("Python 3.10+ não encontrado. Instale e tente novamente.")
    ok(f"Python: {python_label}")

    # Dependências de sistema (só Linux precisa de gi/WebKitGTK)
    if OS == "Linux":
        print()
        bold("  Dependências de sistema"); div()
        check_linux_system_deps(python_bin)

    # Venv
    print()
    py = ensure_venv(python_bin)
    pip = venv_pip()

    # Dependências pip
    print()
    ensure_pip_deps(pip)

    # Browser script
    print()
    bold("  Browser"); div()
    if not BROWSER_SCRIPT.exists():
        err(f"{BROWSER_SCRIPT} não encontrado.")
    ok(f"{BROWSER_SCRIPT.name} encontrado.")

    # Lançar
    print()
    bold("  Pronto!"); div()
    if confirm("Abrir Fodinha Mineira agora?"):
        print()
        info("Iniciando...")
        print(f"{D}  (feche a janela para encerrar){X}")
        print()
        os.execv(str(py), [str(py), str(BROWSER_SCRIPT)])
    else:
        print()
        print(f"{D}  Ok. Rode run.py novamente quando quiser.{X}")


if __name__ == "__main__":
    main()

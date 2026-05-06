# Fodinha Mineira — Launcher

Abre [fodinhamineira.vercel.app](https://fodinhamineira.vercel.app/) em uma janela desktop nativa, sem depender de navegador instalado.

## Como rodar

**Linux / macOS**
```bash
./run.sh
```

**Windows**
```cmd
python run.py
```

O launcher cuida de tudo automaticamente: cria o ambiente virtual, instala dependências de sistema (Linux) e pip, e abre o browser.

## Estrutura

```
launcher/
├── browser.py      # abre o site via pywebview (motor nativo do OS)
├── run.py          # TUI: venv, deps de sistema e pip, launch
├── run.sh          # bootstrap bash: garante Python 3.10+, delega ao run.py
├── requirements.txt
└── .gitignore
```

## Compatibilidade

| OS | Motor web | Requisito extra |
|---|---|---|
| Linux | WebKitGTK (sistema) | `python3-gi` + `webkit2gtk` — instalado automaticamente |
| Windows | Edge WebView2 | nenhum (incluso no Win10/11) |
| macOS | WKWebView | nenhum |

## Dependências

- Python 3.10+
- [`pywebview`](https://pywebview.flowrl.com/) (instalado automaticamente na venv)
- **Linux:** `python3-gi`, `webkit2gtk` via gerenciador de pacotes do sistema

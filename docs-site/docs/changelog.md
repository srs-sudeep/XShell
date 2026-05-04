---
id: changelog
title: Changelog
sidebar_position: 9
---

# Changelog

## v1.0 — 2026-05-04

### New

- Complete rewrite as `xshell/` Python package with clean module separation
- `prompt_toolkit` integration — cross-platform readline, tab completion, Ctrl+R search
- Full pipeline support: `|` `>` `>>` `<` `&&` `||` `;` `&`
- Plugin system with `XShellPlugin` base class and runtime load/unload/reload
- Theme system — 5 built-in JSON themes, live switching, user theme directory
- Levenshtein autocorrect for unknown commands
- `calc` plugin — safe AST-based expression evaluator + 20+ unit conversions
- `sysinfo` plugin — CPU/RAM/disk/network with progress bars (`psutil`)
- `git` plugin — 11 git shortcuts with pass-through arguments
- Web terminal complete rewrite: ANSI rendering, theme panel, status bar, ghost text
- `build.py` — single-command PyInstaller packaging for all platforms
- `docs-site/` — Docusaurus documentation site (managed with bun)

### Removed

- `app.py` (replaced by `web_app.py`)
- `native_shell.py` (Tkinter shell — replaced by `prompt_toolkit` engine)
- `build_native.py`, `native_shell.spec`, `web_terminal.spec` (replaced by `build.py`)
- `shell.c` (C prototype — not used)

---

## v1.0.0 — initial

- Flask + Socket.IO web terminal (`app.py`)
- Tkinter native shell (`native_shell.py`)
- Basic command execution via `subprocess`
- Command history navigation

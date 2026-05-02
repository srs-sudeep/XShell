---
id: intro
title: Introduction
sidebar_position: 1
slug: /
---

# XShell

**XShell** is a feature-rich, cross-platform interactive shell built entirely in Python.
It runs as a native terminal application _or_ as a browser-based web terminal — same
core engine, both modes.

```
  __  __ _____  _          _ _
 \ \/ // ____|| |        | | |
  >  <| (___  | |__   ___| | |
 / /\ \\___ \ | '_ \ / _ \ | |
/ ____ \___) || | | |  __/ | |
/_/    \_\____/ |_| |_|\___|_|_|
  v2.0
```

## Why XShell?

| Problem                                    | XShell's solution                                           |
| ------------------------------------------ | ----------------------------------------------------------- |
| Terminals behave differently on every OS   | Single Python codebase, identical UX on Windows/macOS/Linux |
| Typos waste time                           | Levenshtein autocorrect suggests the right command          |
| Customisation requires dotfile archaeology | One JSON config, one `theme set` command                    |
| Shell extensions are hard to write         | Plugin base class + `register_command()` — 10 lines         |
| No web access                              | `python main.py --web` opens a browser terminal             |

## What's included

- **27 built-in commands** — navigation, file ops, env, aliases, history, themes, plugins
- **Pluggable command system** — built-in, user, and project-local plugins at runtime
- **5 bundled themes** — catppuccin, github-dark, gruvbox, onedark, tokyo-night
- **Full pipeline support** — `|`, `>`, `>>`, `<`, `&&`, `||`, `;`, `&`
- **Tab completion** — commands, files, aliases, plugin commands
- **Ctrl+R** reverse history search
- **Persistent history** — survives restarts, stored in `~/.xshell/history`
- **Standalone executables** — build with PyInstaller via `python build.py`

## Quick start

```bash
# Clone and enter
git clone https://github.com/your-org/xshell.git
cd xshell

# Install (with bun for docs; pip for the shell itself)
pip install -r requirements.txt

# Launch native shell
python main.py

# Or open in browser
python main.py --web
```

See [Getting Started](./getting-started) for a full walkthrough.

---
id: installation
title: Installation
sidebar_position: 3
---

# Installation

## Requirements

| Requirement | Version                                        |
| ----------- | ---------------------------------------------- |
| Python      | 3.9 or later                                   |
| pip         | any recent version                             |
| Git         | optional, needed for the git plugin            |
| bun         | 1.0+ (only needed to run/build this docs site) |

## Step 1 — Get the source

```bash
git clone https://github.com/your-org/xshell.git
cd xshell
```

## Step 2 — Create a virtual environment (recommended)

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs groupId="os">
  <TabItem value="win" label="Windows">

```powershell
python -m venv .venv
.venv\Scripts\activate
```

  </TabItem>
  <TabItem value="mac" label="macOS / Linux">

```bash
python -m venv .venv
source .venv/bin/activate
```

  </TabItem>
</Tabs>

## Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package                    | Purpose                           |
| -------------------------- | --------------------------------- |
| `flask` + `flask-socketio` | Web terminal server               |
| `prompt_toolkit`           | Cross-platform readline input     |
| `rich`                     | Beautiful output (tables, panels) |
| `Pygments`                 | Syntax highlighting               |
| `psutil`                   | System info plugin (optional)     |
| `pyinstaller`              | Standalone build tool             |

## Step 4 — Launch

```bash
# Native terminal
python main.py

# Browser terminal
python main.py --web
```

Source checkout note: the web app resolves `templates/` and `static/` from the
repository root, and project-local plugins and themes are loaded from the
repository `plugins/` and `themes/` folders. Running
`python /full/path/to/main.py --web` from another directory is supported.

---

## Installing the docs site

The documentation site uses [Docusaurus](https://docusaurus.io/) and is managed with **bun**.

```bash
# Move into the docs directory
cd docs-site

# Install dependencies with bun
bun install

# Start local dev server (hot-reload)
bun start

# Build static site
bun run build

# Serve the built site
bun run serve
```

The dev server runs at **http://localhost:3000** by default.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'prompt_toolkit'`

You forgot to install requirements, or your venv isn't activated.  
Run `pip install -r requirements.txt` inside the activated venv.

### Port 5000 already in use (web mode)

Pass a custom port: `python main.py --web --port 8080`

### Windows: Unicode errors in terminal

XShell automatically falls back to ASCII symbols on cp1252 terminals.  
For full Unicode support, use **Windows Terminal** or set:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

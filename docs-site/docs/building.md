---
id: building
title: Building & Packaging
sidebar_position: 8
---

# Building & Packaging

XShell can be packaged into a **single standalone executable** using PyInstaller.
The resulting binary requires no Python installation to run.

## Requirements

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install pyinstaller
```

PyInstaller is already in `requirements.txt`.

## Build the native shell

```bash
python build.py
```

Output: `dist/xshell` (Linux/macOS) or `dist/xshell.exe` (Windows)

## Build the web terminal

```bash
python build.py --web
```

Output: `dist/xshell-web` or `dist/xshell-web.exe`

The web build bundles `templates/`, `static/`, the repository `themes/` folder,
and the repository `plugins/` folder.
Start it the same way:

```bash
./dist/xshell-web          # opens browser automatically
```

## Source checkout vs packaged build

When you run XShell from source, the web app resolves `templates/`, `static/`,
`themes/`, and `plugins/` relative to the repository root.

Packaged builds copy those same top-level folders into the executable bundle, so
theme and plugin discovery behaves the same way after packaging.

## Clean build artifacts

```bash
python build.py --clean    # removes build/ dist/ *.spec
```

## Build the docs site

The documentation site is separate from the PyInstaller build:

```bash
cd docs-site
bun install
bun run build
```

Output: `docs-site/build/`

## What `build.py` does

1. Deletes `build/`, `dist/`, and any `.spec` files
2. Runs PyInstaller with:
   - `--onefile` — single executable

- `--add-data` — bundles `templates/`, `static/`, `themes/`, `plugins/`
- `--hidden-import` — includes all dynamic imports (plugins, prompt_toolkit, etc.)

3. Reports the output path and file size

## Platform-specific notes

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs groupId="os">
  <TabItem value="win" label="Windows">

```powershell
# Activate venv first
.venv\Scripts\activate
python build.py
# → dist\xshell.exe
```

The Windows build uses `--console` so output is visible in CMD/PowerShell.

  </TabItem>
  <TabItem value="mac" label="macOS">

```bash
source .venv/bin/activate
python build.py
# → dist/xshell

# Make executable (should already be set)
chmod +x dist/xshell
./dist/xshell
```

  </TabItem>
  <TabItem value="linux" label="Linux">

```bash
source .venv/bin/activate
python build.py
# → dist/xshell

./dist/xshell
```

To install system-wide:

```bash
sudo cp dist/xshell /usr/local/bin/xshell
xshell
```

  </TabItem>
</Tabs>

## Reducing build size

By default the build bundles everything. To exclude `psutil` if you do not use it:

1. Open `build.py`
2. Remove `'psutil'` from `_HIDDEN`
3. Add `--exclude-module psutil` to the `cmd` list

## Troubleshooting builds

### `RecursionError` during analysis

Add to `build.py`:

```python
import sys
sys.setrecursionlimit(5000)
```

### Missing module at runtime

Add the module to `_HIDDEN` in `build.py`:

```python
_HIDDEN = [
  ...
  'missing.module.name',
]
```

### Icon file

Place a 256×256 `.ico` file at `static/terminal.ico` and `build.py` will
pick it up automatically.

---

## Source map {#source-map}

| File                          | Purpose                                             |
| ----------------------------- | --------------------------------------------------- |
| `main.py`                     | CLI entry point, argument parsing                   |
| `web_app.py`                  | Flask + Socket.IO web server                        |
| `build.py`                    | PyInstaller build script                            |
| `requirements.txt`            | Python dependencies                                 |
| `xshell/__init__.py`          | Version string                                      |
| `xshell/core/shell.py`        | Main REPL, prompt, completions                      |
| `xshell/core/parser.py`       | Tokenizer and AST builder                           |
| `xshell/core/executor.py`     | Pipeline execution, redirects                       |
| `xshell/core/builtins.py`     | 27 built-in commands                                |
| `xshell/core/history.py`      | Persistent history                                  |
| `xshell/core/autocorrect.py`  | Levenshtein autocorrect                             |
| `xshell/config/manager.py`    | JSON config load/save                               |
| `xshell/themes/manager.py`    | Theme file scanner                                  |
| `xshell/plugins/base.py`      | XShellPlugin base class                             |
| `xshell/plugins/manager.py`   | Dynamic plugin loader                               |
| `xshell/plugins/builtin/*.py` | Bundled built-in plugins (`git`, `sysinfo`, `calc`) |
| `xshell/ui/renderer.py`       | Rich output helpers                                 |
| `xshell/ui/prompt.py`         | Prompt segment builders                             |
| `static/css/style.css`        | Web UI styles                                       |
| `static/js/terminal.js`       | Web UI logic                                        |
| `templates/index.html`        | Web terminal HTML                                   |
| `plugins/`                    | Project-local plugins loaded from the repo root     |
| `themes/`                     | Bundled/project-local theme JSON files              |
| `docs-site/`                  | This Docusaurus documentation site                  |

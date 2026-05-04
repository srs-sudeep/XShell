# XShell v1.0

A feature-rich, cross-platform shell built entirely in Python.

```
  __  __ _____  _          _ _
 \ \/ // ____|| |        | | |
  >  <| (___  | |__   ___| | |
 / /\ \\___ \ | '_ \ / _ \ | |
/ ____ \___) || | | |  __/ | |
/_/    \_\____/ |_| |_|\___|_|_|
```

> Live documentation: [x-shell.vercel.app](https://x-shell.vercel.app/)
>
> GitHub repository: [github.com/srs-sudeep/XShell](https://github.com/srs-sudeep/XShell)
>
> Download releases: [github.com/srs-sudeep/XShell/releases](https://github.com/srs-sudeep/XShell/releases/)

---

## Quick start

### Shell

```bash
# Clone repository
git clone https://github.com/srs-sudeep/XShell.git
cd XShell

# 1. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run native terminal shell
python main.py

# 4. Or open in the browser
python main.py --web
```

Source checkout note: when you run the web UI from source, XShell resolves
`templates/`, `static/`, and the project-local `plugins/` folder relative to the
repository root, not the process working directory. Running
`python /full/path/to/main.py --web` from another directory works as expected.

### Docs site

```bash
# Install bun (if you don't have it)
# Windows PowerShell:
powershell -c "irm bun.sh/install.ps1 | iex"
# macOS / Linux:
curl -fsSL https://bun.sh/install | bash

cd docs-site
bun install     # install Docusaurus + dependencies
bun start       # dev server at http://localhost:3000
bun run build   # build static site → docs-site/build/
bun run serve   # preview the built site
```

Live docs: [x-shell.vercel.app](https://x-shell.vercel.app/)

---

## CLI flags

```
python main.py                   Interactive shell
python main.py --web             Web UI (browser, default port 5000)
python main.py --web --port N    Web UI on port N
python main.py --theme <name>    Start with a theme (for example: gruvbox, onedark)
python main.py --no-plugins      Disable plugin system
python main.py --version         Print version
python main.py -c "ls -la"       Execute one command and exit
```

---

## Features at a glance

| Feature        | Details                                                                    |
| -------------- | -------------------------------------------------------------------------- |
| Cross-platform | Windows · macOS · Linux — identical experience                             |
| Smart prompt   | `user@host:cwd (branch)$` with live git info                               |
| Tab completion | Commands, files, dirs, aliases, plugin commands                            |
| History        | Persistent, deduplicated, Ctrl+R search, arrow nav                         |
| Autocorrect    | Levenshtein typo detection + suggestions                                   |
| Themes         | Bundled themes: catppuccin · github-dark · gruvbox · onedark · tokyo-night |
| Plugin system  | Built-in plugins + user + project-local plugins, loaded at runtime         |
| 27 builtins    | Full shell utilities cross-platform                                        |
| Pipelines      | `\|` `>` `>>` `<` `&&` `\|\|` `;` `&`                                      |
| Extensible     | Project-local and user plugins can add commands at runtime                 |
| Web terminal   | Browser UI with ANSI colours + theme switcher                              |
| Packaging      | Single exe/binary via `python build.py`                                    |

---

## Project structure

```
XShell/
├── main.py              ← Entry point
├── web_app.py           ← Flask/Socket.IO web server
├── requirements.txt     ← Python deps
├── build.py             ← PyInstaller packaging
│
├── xshell/              ← Core Python package
│   ├── core/            ← shell, parser, executor, builtins, history, autocorrect
│   ├── config/          ← JSON config manager
│   ├── themes/          ← Theme manager
│   ├── plugins/         ← Plugin base class, manager, bundled plugins
│   └── ui/              ← Rich renderer, prompt builder
│
├── static/              ← Web UI (CSS + JS)
├── templates/           ← Web terminal HTML
│
├── plugins/             ← Drop project-local plugins here (.py)
├── themes/              ← Drop project-local themes here (.json)
│
└── docs-site/           ← Docusaurus documentation site
    ├── package.json     ← Managed with bun
    ├── docs/            ← All documentation pages (Markdown)
    └── src/             ← Homepage + custom CSS
```

---

## Keyboard shortcuts (native shell)

| Key       | Action                 |
| --------- | ---------------------- |
| `↑` / `↓` | Navigate history       |
| `Tab`     | Autocomplete           |
| `Ctrl+R`  | Reverse history search |
| `Ctrl+L`  | Clear screen           |
| `Ctrl+C`  | Cancel current input   |
| `Ctrl+D`  | Exit shell             |

---

## Themes

```bash
theme list            # show available themes with descriptions
theme info gruvbox    # show full palette and prompt format
theme set gruvbox     # apply immediately
```

Custom theme — drop a JSON file in `themes/` or `~/.xshell/themes/`:

```json
{
  "name": "My Theme",
  "colors": {
    "prompt_user": "bright_cyan",
    "prompt_host": "bright_green",
    "prompt_cwd": "bright_yellow",
    "prompt_git": "bright_magenta"
  },
  "prompt": { "format": "{default}" }
}
```

---

## Working with plugins

```bash
plugin list             # loaded plugins + commands they add
plugin available        # everything XShell can load
plugin info git         # description, version, commands, completions
plugin load todo        # load a project-local or user plugin
plugin reload calc      # reload a plugin after editing
```

The default config auto-loads the bundled `git`, `sysinfo`, and `calc` plugins.
XShell also discovers plugins from:

- `plugins/` in the repository root
- `~/.xshell/plugins/` (or `%APPDATA%\XShell\plugins\` on Windows)

## Writing a plugin

Create `~/.xshell/plugins/myplugin.py`:

```python
from xshell.plugins.base import XShellPlugin

class MyPlugin(XShellPlugin):
    name        = 'myplugin'
    description = 'Does something cool'

    def on_load(self, shell):
        super().on_load(shell)
        self.register_command('hello', self._hello, help='Print a greeting')

    def _hello(self, shell, args):
        print(f"Hello, {args[1] if len(args) > 1 else 'World'}!")
        return 0
```

```bash
plugin load myplugin
hello World
```

---

## Build a standalone executable

```bash
python build.py            # → dist/xshell (or dist/xshell.exe)
python build.py --web      # → dist/xshell-web
python build.py --clean    # remove build artifacts
```

## Publish binaries on GitHub Releases

You do **not** need to upload executables manually each time.

Binary builds are automated by `.github/workflows/release-binaries.yml` and run on:

- Published GitHub Release
- Git tag push matching `v*` (for example `v1.0.1`)
- Manual run from Actions (`workflow_dispatch`)

Regular pushes to `main` do not trigger this release workflow.

Release downloads are available at:
[github.com/srs-sudeep/XShell/releases](https://github.com/srs-sudeep/XShell/releases/)

Typical flow:

```bash
git tag v1.0.1
git push origin v1.0.1
```

The workflow builds Linux/macOS/Windows binaries and attaches archives to the
matching GitHub Release.

Linux binaries are produced on `ubuntu-22.04` to avoid the newer `glibc` baseline
from `ubuntu-latest` while still using a Python build that works with
PyInstaller.

Packaged builds bundle `templates/`, `static/`, the repository `themes/` folder,
the repository `plugins/` folder, and the bundled Python plugin modules under
`xshell/plugins/builtin/`. The same root-relative theme and plugin discovery
works in both source mode and packaged mode.

## Build the docs site

```bash
cd docs-site
bun install
bun start       # dev server at http://localhost:3000
bun run build   # static output in docs-site/build/
bun run serve   # preview the built site
```

---

## Configuration

`~/.xshell/config.json` (Windows: `%APPDATA%\XShell\config.json`):

```json
{
  "theme": "default",
  "plugins": ["git", "sysinfo", "calc"],
  "history_size": 2000,
  "autocorrect": true,
  "aliases": { "ll": "ls -l", "..": "cd .." }
}
```

---

## License

MIT

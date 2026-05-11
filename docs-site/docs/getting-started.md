---
id: getting-started
title: Getting Started
sidebar_position: 2
---

# Getting Started

This page walks you through your first XShell session from install to your first plugin.

**Native shell demo (video):** [youtu.be/XHgtwIJJVFs](https://youtu.be/XHgtwIJJVFs) — stills and the web UI tour live on [Demos & Screenshots](./demo-media).

## 1. Launch the shell

```bash
python main.py
```

You'll see the banner and a prompt:

```
  __  __ _____  _          _ _
 ...

  XShell v1.0  |  type 'help' for commands  |  Ctrl+D to exit

sudeep@hostname:~/projects/xshell $
```

The prompt shows:

- **user** (cyan) — your username
- **host** (green) — machine hostname
- **cwd** (yellow) — current directory, shortened to last 3 parts
- **branch** (magenta) — git branch if you're inside a repo

## 2. Run your first commands

```bash
# List files
ls -la

# Navigate
cd src
pwd

# Pipe and redirect
ls | grep py > python_files.txt
cat python_files.txt
```

## 3. Explore history

- Press `↑` / `↓` to navigate previous commands
- Press `Ctrl+R` to open reverse-search — type to filter

```bash
history        # show all history
history -n 20  # show last 20 entries
history -c     # clear history
```

## 4. Use tab completion

Start typing a command and press `Tab`:

```
th[Tab]  →  theme
ls -[Tab]  →  shows -a, -l flags
cd ~/[Tab]  →  expands home directory
```

## 5. Try autocorrect

Make a typo on purpose:

```bash
gti status
# xshell: 'gti' not found. Did you mean 'git'?
```

## 6. Change the theme

```bash
theme list
theme info gruvbox
theme set gruvbox
```

## 7. Load a project-local plugin

```bash
plugin load todo
todo add write docs cleanup
todo list

plugin load notes
note new ideas
note write ideas tighten plugin defaults
```

Project-local plugins live in the repository `plugins/` directory and are
discovered from the repo root when you run from a source checkout.

## 8. Auto-load a plugin

Edit `~/.xshell/config.json`:

```json
{
  "plugins": ["git", "sysinfo", "calc", "todo", "notes"]
}
```

On the next launch, XShell loads those plugin files automatically from either
`~/.xshell/plugins/` or the repository `plugins/` folder.

## 9. Reload after an edit

```bash
plugin reload todo
```

You can also inspect what is available before loading anything:

```bash
plugin available
plugin info todo
plugin info git
```

## 10. Open the web terminal

```bash
python main.py --web
```

Your browser opens automatically at `http://127.0.0.1:5000` with a full terminal UI,
ANSI colour support, and the theme switcher panel.

If you're working from a source checkout, project-local plugins live in the
repository `plugins/` folder and are discovered from the repo root.

---

## Command-line flags

| Flag             | Description                  |
| ---------------- | ---------------------------- |
| `--web`          | Run web terminal             |
| `--web --port N` | Web terminal on port N       |
| `--theme <name>` | Start with a specific theme  |
| `--no-plugins`   | Disable plugin system        |
| `--version`      | Print version and exit       |
| `-c "cmd"`       | Execute one command and exit |

```bash
python main.py --theme gruvbox --web --port 8080
```

## Next steps

- [Demos & Screenshots](./demo-media) — video tours and screenshot gallery (native + web)
- [Commands reference](./commands) — every built-in command
- [Themes](./themes) — switch and create themes
- [Writing a plugin](./plugins/writing-plugins) — extend XShell in minutes
- Releases: [github.com/srs-sudeep/XShell/releases](https://github.com/srs-sudeep/XShell/releases/)
- Repository: [github.com/srs-sudeep/XShell](https://github.com/srs-sudeep/XShell)
- Live docs: [x-shell.vercel.app](https://x-shell.vercel.app/)

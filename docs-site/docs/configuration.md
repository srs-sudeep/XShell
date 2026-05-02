---
id: configuration
title: Configuration
sidebar_position: 7
---

# Configuration

XShell stores its configuration as JSON at:

| Platform      | Path                           |
| ------------- | ------------------------------ |
| Linux / macOS | `~/.xshell/config.json`        |
| Windows       | `%APPDATA%\XShell\config.json` |

The file is created with defaults on first launch.

## Default configuration

```json
{
  "theme": "default",
  "plugins": ["git", "sysinfo", "calc"],
  "history_size": 2000,
  "autocorrect": true,
  "complete_while_typing": true,
  "prompt_format": "{default}",
  "aliases": {
    "ll": "ls -l",
    "la": "ls -a",
    "lla": "ls -la",
    "..": "cd ..",
    "...": "cd ../..",
    "g": "git",
    "py": "python"
  },
  "show_banner": true,
  "vi_mode": false
}
```

## Keys reference

| Key                     | Type   | Default                      | Description                              |
| ----------------------- | ------ | ---------------------------- | ---------------------------------------- |
| `theme`                 | string | `"default"`                  | Active theme name                        |
| `plugins`               | array  | `['git', 'sysinfo', 'calc']` | Plugins to load at startup               |
| `history_size`          | int    | `2000`                       | Max history entries to keep              |
| `autocorrect`           | bool   | `true`                       | Suggest corrections for unknown commands |
| `complete_while_typing` | bool   | `true`                       | Show completions as you type             |
| `aliases`               | object | see above                    | Persistent alias definitions             |
| `show_banner`           | bool   | `true`                       | Show ASCII art banner on startup         |
| `vi_mode`               | bool   | `false`                      | Use vi key bindings (Esc, hjkl, …)       |

## Editing config from the shell

Config changes made with `theme set` and `alias` are auto-saved.
For other keys, edit the file directly — changes take effect on next launch:

```bash
# Show the config file path
python -c "from xshell.config.manager import _config_dir; print(_config_dir())"

# Open in default editor (Windows)
notepad %APPDATA%\XShell\config.json

# Open in default editor (Unix)
$EDITOR ~/.xshell/config.json
```

## Adding persistent aliases

```json
{
  "aliases": {
    "k": "kubectl",
    "dc": "docker-compose",
    "tf": "terraform",
    "gp": "gpush"
  }
}
```

## Loading a custom config file

```bash
# Pass an explicit path to XShell
python -c "
from xshell.core.shell import XShell
XShell(config_path='/path/to/my-config.json').run()
"
```

Or modify `main.py` to accept `--config` as a CLI flag.

## Per-project config

XShell doesn't natively support per-project config files yet.  
As a workaround, use a shell script:

```bash title="start-dev.sh"
#!/bin/bash
export XSHELL_THEME=gruvbox
python main.py --theme gruvbox --no-plugins
```

## User themes and plugins directories

| Platform    | Themes                     | Plugins                     |
| ----------- | -------------------------- | --------------------------- |
| Linux/macOS | `~/.xshell/themes/`        | `~/.xshell/plugins/`        |
| Windows     | `%APPDATA%\XShell\themes\` | `%APPDATA%\XShell\plugins\` |

Drop `.json` files into themes and `.py` files into plugins — XShell picks them up
automatically without any configuration changes.
Plugin names resolve in this order:

1. Built-in plugin modules under `xshell/plugins/builtin/`
2. User plugin directory
3. Project-local plugins in the repository `plugins/` folder

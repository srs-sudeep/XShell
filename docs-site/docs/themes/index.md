---
id: index
title: Themes
sidebar_position: 1
---

# Themes

XShell ships with **5 bundled themes** in the repository `themes/` folder and
supports unlimited custom themes. Themes control prompt colours, ANSI palette,
and background/foreground colours for the web terminal.

## Switching themes

```bash
theme list            # see all available themes with descriptions
theme info gruvbox    # inspect the palette for one theme
theme set gruvbox     # apply a theme immediately — no restart needed
```

The chosen theme is saved to `~/.xshell/config.json` and restored on next launch.

## Bundled themes

### `catppuccin`

Catppuccin Mocha. Soothing pastel palette with warm cursor and muted selection.

### `github-dark`

GitHub dark-style palette. Clean, restrained, and familiar.

### `gruvbox`

Retro groove dark palette with warm contrast.

### `onedark`

One Dark-inspired palette for Atom / VS Code style terminals.

### `tokyo-night`

Cool neon-blue night palette inspired by Tokyo Night.

### Fallback `default`

If XShell finds no theme files at all, it falls back to an internal `default`
theme so the shell still renders correctly.

## Theme file format

Every theme is a JSON file with two sections: `colors` and `prompt`.

```json title="~/.xshell/themes/mytheme.json"
{
  "name": "My Theme",
  "description": "Optional description shown in theme list",
  "colors": {
    "background": "#0d1117",
    "foreground": "#c9d1d9",
    "prompt_user": "bright_cyan",
    "prompt_host": "bright_green",
    "prompt_cwd": "bright_yellow",
    "prompt_git": "bright_magenta",
    "error": "bright_red",
    "success": "bright_green",
    "info": "bright_blue",
    "warning": "bright_yellow"
  },
  "prompt": {
    "format": "{default}"
  }
}
```

### Color values

Colours can be:

- **Named ANSI**: `black red green yellow blue magenta cyan white` (and `bright_` variants)
- **Hex** (web terminal only): `#282a36`

### Prompt format

Set `"format"` to `"{default}"` to use the built-in `user@host:cwd (branch)$` layout.

To customise the layout, use placeholders:

| Placeholder | Replaced with                                 |
| ----------- | --------------------------------------------- |
| `{user}`    | Username (coloured)                           |
| `{host}`    | Hostname (coloured)                           |
| `{cwd}`     | Current directory (coloured, shortened)       |
| `{git}`     | ` (branch)` if in a git repo, empty otherwise |
| `{$}`       | Bold `$` sign                                 |

```json
"prompt": {
  "format": "[{user}@{host}] {cwd}{git} {$}"
}
```

## Where themes are loaded from

1. Repository or bundled root: `themes/*.json`
2. User overrides: `~/.xshell/themes/*.json`
3. Internal fallback theme used only when no theme files are found

Files are scanned in this order; later files override earlier ones with the same stem name.

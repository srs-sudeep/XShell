---
id: custom-themes
title: Creating Custom Themes
sidebar_position: 2
---

# Creating Custom Themes

You can create a fully custom theme in about 2 minutes.

## Step 1 — Create the JSON file

Save this to `~/.xshell/themes/mytheme.json`  
(or drop it in the project-local `themes/` folder):

```json title="~/.xshell/themes/mytheme.json"
{
  "name": "Cyberpunk",
  "description": "Neon on dark",
  "colors": {
    "background": "#0a0a0a",
    "foreground": "#e0e0e0",
    "prompt_user": "bright_magenta",
    "prompt_host": "bright_cyan",
    "prompt_cwd": "bright_yellow",
    "prompt_git": "bright_green",
    "error": "bright_red",
    "success": "bright_green",
    "info": "bright_cyan",
    "warning": "bright_yellow"
  },
  "prompt": {
    "format": "{default}"
  }
}
```

## Step 2 — Activate it

```bash
theme list      # your new theme should appear
theme set cyberpunk
```

XShell scans the themes directory on startup and whenever `theme list` is called.
No restart is needed after a fresh launch. If you add a new theme file while
XShell is already running, restart the shell so it will be picked up.

## Step 3 — Persist it

The `theme set` command saves your choice to `~/.xshell/config.json` automatically.
It will be restored on your next launch.

---

## Named ANSI colors reference

| Name             | Appearance              |
| ---------------- | ----------------------- |
| `black`          | Dark                    |
| `red`            | Standard red            |
| `green`          | Standard green          |
| `yellow`         | Standard yellow / brown |
| `blue`           | Standard blue           |
| `magenta`        | Purple/pink             |
| `cyan`           | Teal/aqua               |
| `white`          | Light grey              |
| `bright_black`   | Dark grey               |
| `bright_red`     | Bright red              |
| `bright_green`   | Bright green            |
| `bright_yellow`  | Bright yellow           |
| `bright_blue`    | Bright blue             |
| `bright_magenta` | Bright purple/pink      |
| `bright_cyan`    | Bright teal             |
| `bright_white`   | Pure white              |

## Custom prompt layout

You can fully control the prompt structure with the `format` string:

```json
"prompt": {
  "format": "({user}) {cwd}{git} >"
}
```

This would produce:

```
(alice) ~/projects/xshell (main) >
```

Available placeholders: `{user}` `{host}` `{cwd}` `{git}` `{$}`

## Sharing themes

To share your theme with other XShell users:

1. Place it in the project-local `themes/` directory
2. Commit and push to your fork
3. Other users can drop the JSON into their `~/.xshell/themes/` without any code changes

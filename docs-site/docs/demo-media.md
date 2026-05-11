---
id: demo-media
title: Demos & Screenshots
sidebar_position: 4
description: Video walkthroughs and a screenshot gallery for the XShell native and web terminals.
---

# Demos & Screenshots

Short video tours and still captures of **XShell** in the native Python terminal and in the **browser web terminal** ([`python main.py --web`](./web-terminal)).

:::tip Keeping images in sync

Screenshots live under **`static/img/demo/`** at the repository root. The docs build serves copies from **`docs-site/static/img/demo/`**. After you add or rename files in the root folder, sync the docs tree:

```bash
cp static/img/demo/*.png docs-site/static/img/demo/
```

:::

## Video walkthroughs

| Mode | Demo |
| ---- | ---- |
| **Native shell** (terminal UI, themes, plugins, `python main.py`) | [**Watch on YouTube**](https://youtu.be/XHgtwIJJVFs) |
| **Web terminal** (Flask + Socket.IO, `python main.py --web`) | [**Watch on YouTube**](https://youtu.be/LNP0p5zTUro) |

Direct links: [Native — youtu.be/XHgtwIJJVFs](https://youtu.be/XHgtwIJJVFs) · [Web — youtu.be/LNP0p5zTUro](https://youtu.be/LNP0p5zTUro)

## Screenshot gallery

Files use descriptive names under `static/img/demo/` (mirrored at `/img/demo/` on this site). Captures were taken **11 May 2026**; order is chronological (native session first, then web UI).

### Native terminal (`python main.py`)

#### `neofetch` (Gruvbox)

![Native XShell: neofetch summary with Gruvbox theme](/img/demo/native-neofetch-gruvbox.png)

#### `help` — built-in command list

![Native XShell: help output listing builtins](/img/demo/native-help-builtins.png)

#### `banner` and `rm`

![Native XShell: ASCII banner and rm command](/img/demo/native-banner-rm.png)

#### `ls`, `ll`, and `ls -la`

![Native XShell: directory listing with ll](/img/demo/native-ls-ll.png)

#### Files: `mkdir`, `cd`, `touch`, `cat`

![Native XShell: mkdir cd touch cat workflow](/img/demo/native-files-mkdir-cd-touch.png)

#### Themes: `theme list`, `theme set`, `theme info`

![Native XShell: theme list set and theme info catppuccin](/img/demo/native-theme-list-info.png)

#### Plugins: `plugin` help, `plugin list`, `plugin available`

![Native XShell: plugin available table](/img/demo/native-plugin-available.png)

#### Todo plugin: `plugin load todo`, `todo` commands

![Native XShell: todo plugin demo](/img/demo/native-plugin-todo.png)

### Web terminal (`python main.py --web`)

#### Startup banner (Catppuccin)

![Web XShell: startup banner and theme changed message](/img/demo/web-banner-catppuccin.png)

#### Theme picker

![Web XShell: Choose Theme panel](/img/demo/web-theme-picker.png)

#### Multiple tabs

![Web XShell: three shell tabs](/img/demo/web-tabs-multi-session.png)

#### Split panes

![Web XShell: vertical split two panes](/img/demo/web-split-panes.png)

#### `dir` — project listing

![Web XShell: dir output project root](/img/demo/web-dir-listing.png)

#### `help` — built-in command list

![Web XShell: help output listing builtins](/img/demo/web-help-builtins.png)

## See also

- [Getting started](./getting-started) — first session in the native shell  
- [Web terminal](./web-terminal) — browser UI, architecture, and shortcuts  
- [GitHub releases](https://github.com/srs-sudeep/XShell/releases) — downloadable builds  

---
id: index
title: Commands Overview
sidebar_position: 1
---

# Built-in Commands

XShell ships with **27 built-in commands** that work identically on Windows, macOS, and Linux.
They are implemented in [`xshell/core/builtins.py`](../building#source-map) and are always
available — no PATH lookup needed.

## Quick reference

| Category | Commands |
|---|---|
| [Navigation](./navigation) | `cd`, `pwd`, `ls`, `dir` |
| [Files](./files) | `cat`, `touch`, `mkdir`, `rm`, `cp`, `mv` |
| [Output](./shell#echo) | `echo` |
| [Terminal](./shell#clear) | `clear`, `cls` |
| [History](./shell#history) | `history` |
| [Aliases](./shell#alias) | `alias`, `unalias` |
| [Environment](./shell#export) | `export`, `unset`, `env` |
| [Shell mgmt](./shell#source) | `source`, `exit`, `quit` |
| [Discovery](./shell#which) | `which`, `type`, `help` |
| [Theming](./shell#theme) | `theme` |
| [Plugins](./shell#plugin) | `plugin` |

## Pipeline operators

These are not commands — they're syntax handled by the parser:

| Operator | Meaning |
|---|---|
| `\|` | Pipe stdout of left into stdin of right |
| `>` | Redirect stdout to file (overwrite) |
| `>>` | Redirect stdout to file (append) |
| `<` | Redirect stdin from file |
| `&&` | Run right only if left succeeded (exit 0) |
| `\|\|` | Run right only if left failed (exit ≠ 0) |
| `;` | Run both regardless of exit code |
| `&` | Run in background |

```bash
# Examples
ls | grep .py > results.txt
make && echo "Build OK" || echo "Build failed"
long_job &
```

## Exit codes

Every command returns an integer exit code. `0` means success, anything else is an error.
`$?` is not yet a shell variable in XShell — the exit code is shown in the status bar of
the web terminal.

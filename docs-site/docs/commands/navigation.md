---
id: navigation
title: Navigation
sidebar_position: 2
---

# Navigation Commands

## `cd` — Change directory

```bash
cd [dir]
```

| Usage | Result |
|---|---|
| `cd` | Go to home directory (`$HOME`) |
| `cd /path/to/dir` | Go to absolute path |
| `cd relative/path` | Go to relative path |
| `cd -` | Go to previous directory (`$OLDPWD`) |
| `cd ..` | Go up one level |
| `cd ~/projects` | Tilde expands to home |

:::tip
`cd -` is a quick toggle between two directories — great when bouncing between source and output dirs.
:::

---

## `pwd` — Print working directory

```bash
pwd
```

Prints the absolute path of the current directory.

```bash
$ pwd
/home/user/projects/xshell
```

---

## `ls` — List directory contents

```bash
ls [-a] [-l] [path ...]
```

| Flag | Description |
|---|---|
| `-a` / `--all` | Show hidden files (starting with `.`) |
| `-l` | Long format — shows size and type indicator |

Directories are shown in **blue**, executables in **green** (Unix only).

```bash
ls               # short listing of current dir
ls -la           # long listing including hidden
ls -l ~/Desktop  # long listing of another path
ls src tests     # list multiple directories
```

:::note
`dir` is an alias for `ls` and accepts the same flags.
:::

---

## Default aliases for navigation

These aliases are pre-configured in the default config:

```bash
..    # cd ..
...   # cd ../..
ll    # ls -l
la    # ls -a
lla   # ls -la
```

---
id: files
title: File Operations
sidebar_position: 3
---

# File Operation Commands

All file commands use Python's `os`, `shutil`, and `pathlib` under the hood, making them
fully cross-platform. Glob patterns (`*`, `?`, `[...]`) are expanded before the command runs.

## `cat` — Print file contents

```bash
cat <file> [file ...]
```

Prints one or more files to stdout. Without arguments, reads from stdin.

```bash
cat README.md
cat file1.txt file2.txt
cat *.log | grep ERROR
```

---

## `touch` — Create or update file

```bash
touch <file> [file ...]
```

Creates the file if it doesn't exist, or updates its modification time.

```bash
touch newfile.py
touch a.txt b.txt c.txt
```

---

## `mkdir` — Create directory

```bash
mkdir [-p] <dir> [dir ...]
```

| Flag | Description |
|---|---|
| `-p` | Create parent directories as needed; don't error if exists |

```bash
mkdir src
mkdir -p a/b/c/d
```

---

## `rm` — Remove files and directories

```bash
rm [-r] [-f] <path> [path ...]
```

| Flag | Description |
|---|---|
| `-r` / `-R` | Recursively remove directories |
| `-f` | Force — suppress "not found" errors |
| `-rf` | Both flags combined |

```bash
rm old_file.txt
rm -r build/
rm -rf dist/ __pycache__/
rm *.pyc
```

:::warning
`rm -rf` is irreversible. XShell does **not** move files to trash.
:::

---

## `cp` — Copy

```bash
cp [-r] <src> [src ...] <dst>
```

| Flag | Description |
|---|---|
| `-r` / `-R` | Recursively copy directories |

```bash
cp config.json config.backup.json
cp -r src/ src_backup/
cp *.py scripts/
```

---

## `mv` — Move / rename

```bash
mv <src> [src ...] <dst>
```

```bash
mv old_name.py new_name.py        # rename
mv build/ dist/ archive/          # move into archive/
mv *.txt docs/                    # move all text files
```

---

## Glob expansion

All file commands support glob patterns expanded by XShell before the command runs:

```bash
rm *.pyc                  # all .pyc files
cp src/*.py dst/          # all Python files
ls **/*.json              # all JSON files recursively (Python glob)
```

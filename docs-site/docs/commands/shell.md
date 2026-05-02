---
id: shell
title: Shell Management
sidebar_position: 4
---

# Shell Management Commands

## `echo` {#echo}

```bash
echo [-n] [-e] <text>
```

| Flag | Description                                         |
| ---- | --------------------------------------------------- |
| `-n` | No trailing newline                                 |
| `-e` | Interpret escape sequences (`\n`, `\t`, `\\`, etc.) |

```bash
echo Hello, World!
echo -n "no newline"
echo -e "line1\nline2\ttabbed"
```

---

## `clear` / `cls` {#clear}

Clears the terminal screen.

```bash
clear    # Unix-style
cls      # Windows-style (also works on all platforms)
```

Keyboard shortcut: `Ctrl+L`

---

## `history` {#history}

```bash
history [-c] [-n N]
```

| Flag                | Description         |
| ------------------- | ------------------- |
| _(none)_            | Print all history   |
| `-c` / `--clear`    | Delete all history  |
| `-n N` / `--last N` | Show last N entries |

```bash
history
history -n 20
history -c
```

History is saved to `~/.xshell/history` (or `%APPDATA%\XShell\history` on Windows)
and persists across sessions. Consecutive duplicate entries are deduplicated.

---

## `alias` {#alias}

```bash
alias [name=value]
```

```bash
alias                    # show all current aliases
alias ll='ls -l'         # define an alias
alias g=git              # short form without quotes
alias ll                 # show a single alias definition
```

Aliases are expanded before the command is parsed, so they can include flags and pipes:

```bash
alias lsg='ls | grep'
lsg .py    # → ls | grep .py
```

Aliases defined in the session are not persisted automatically. To persist, add them
to `~/.xshell/config.json` in the `"aliases"` section.

---

## `unalias` {#unalias}

```bash
unalias <name> [name ...]
```

```bash
unalias ll
unalias g ll la
```

---

## `export` {#export}

```bash
export [KEY=value] [KEY ...]
```

```bash
export                       # print all environment variables
export DEBUG=1               # set a variable
export PATH="$PATH:/opt/bin" # extend PATH
export DEBUG                 # mark existing variable as exported
```

---

## `unset` {#unset}

```bash
unset <KEY> [KEY ...]
```

Removes a variable from the environment.

```bash
unset DEBUG
unset TEMP_VAR OLD_VAR
```

---

## `env` {#env}

```bash
env
```

Prints all environment variables in `KEY=value` format, sorted alphabetically.

---

## `source` {#source}

```bash
source <file>
```

Executes every non-comment line of a file as if typed at the prompt.
Useful for loading aliases, env vars, or configs.

```bash
source ~/.xshell/profile.xsh
source ./setup_env.sh
```

---

## `which` {#which}

```bash
which <command>
```

Prints the full path to an executable, using `shutil.which`.

```bash
which python
which git
which xshell
```

---

## `type` {#type}

```bash
type <name>
```

Explains how a name will be resolved — builtin, alias, or external command.

```bash
$ type cd
cd is a shell builtin

$ type ll
ll is aliased to 'ls -l'

$ type python
python is /usr/bin/python
```

---

## `help` {#help}

```bash
help [command]
```

Without arguments, lists all built-in commands.
With a command name, shows help for that specific command.

```bash
help
help cd
help history
```

---

## `theme` {#theme}

```bash
theme --help
theme list
theme info <name>
theme set <name>
```

```bash
theme --help            # built-in help output
theme list              # show all available themes with descriptions
theme info gruvbox      # show colours + prompt format
theme gruvbox           # shorthand for 'theme set gruvbox'
```

See [Themes](../themes) for details.

---

## `plugin` {#plugin}

```bash
plugin --help
plugin list
plugin available
plugin info <name>
plugin load <name>
plugin unload <name>
plugin reload <name>
```

```bash
plugin --help          # built-in help output
plugin list            # loaded plugins + commands they contribute
plugin available       # builtin / local / user plugins XShell can load
plugin info git        # description, author, version, commands, completions
plugin load myplugin   # load ~/.xshell/plugins/myplugin.py or plugins/myplugin.py
plugin reload calc     # reload the calc plugin after editing
```

See [Plugins](../plugins) for details.

---

## `exit` / `quit` {#exit}

```bash
exit [code]
quit [code]
```

Exits the shell with an optional exit code (default 0).

```bash
exit
exit 1
quit 42
```

Keyboard shortcut: `Ctrl+D`

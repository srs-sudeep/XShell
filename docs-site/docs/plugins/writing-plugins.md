---
id: writing-plugins
title: Writing Plugins
sidebar_position: 3
---

# Writing Plugins

A plugin is a single Python file containing one class that subclasses `XShellPlugin`.
XShell finds it automatically — no registration needed.

For development in a source checkout, you can keep tracked plugins in the repository
`plugins/` directory. For personal or installed usage, put them in
`~/.xshell/plugins/` (or `%APPDATA%\\XShell\\plugins\\` on Windows).

## Minimal example

```python title="~/.xshell/plugins/hello.py"
from xshell.plugins.base import XShellPlugin

class HelloPlugin(XShellPlugin):
    name        = 'hello'
    description = 'Greets people'

    def on_load(self, shell):
        super().on_load(shell)
        self.register_command('hello', self._hello, help='Print a greeting')

    def _hello(self, shell, args):
        name = args[1] if len(args) > 1 else 'World'
        print(f'Hello, {name}!')
        return 0   # exit code 0 = success
```

Load it:

```bash
plugin load hello
hello Alice
# Hello, Alice!
```

---

## Plugin lifecycle

```
plugin load   →  __init__()  →  on_load(shell)
plugin unload →  on_unload()
plugin reload →  on_unload() + on_load(shell)
```

### `on_load(shell)`

Called when the plugin is loaded. Register commands here.
`shell` is the live `XShell` instance — you can access `shell.config`,
`shell.theme_manager`, `shell.history`, etc.

### `on_unload()`

Called when the plugin is unloaded. Clean up resources (close connections, stop threads).

### `on_prompt()`

Return a string to append to the prompt (return `''` to add nothing).

```python
def on_prompt(self) -> str:
    return f' (venv:{os.path.basename(os.environ.get("VIRTUAL_ENV",""))})'
```

---

## Registering commands

```python
self.register_command('mycommand', self._mycommand)

# With autocomplete hints
self.register_command('mycommand', self._mycommand, completions=['--flag', '--verbose'])

# With explicit help text shown by `plugin info`
self.register_command('mycommand', self._mycommand, help='Run my custom command')
```

Command functions have the signature:

```python
def _mycommand(self, shell, args: list[str]) -> int:
    # args[0] is the command name itself (like sys.argv[0])
    # args[1:] are the arguments the user typed
    # Return 0 for success, non-zero for error
    ...
```

---

## Accessing shell state

Inside any command function, `shell` gives you full access to the running shell:

```python
def _mycommand(self, shell, args):
    # Read config
    autocorrect = shell.config.get('autocorrect')

    # Add to history
    shell.history.add('my synthetic entry')

    # Read/write aliases
    shell.aliases['myalias'] = 'mycommand --default-flag'

    # Get current theme
    theme = shell.theme_manager.current_theme
    color = theme['colors']['prompt_user']

    # Execute a shell line
    shell.execute_line('ls -la')

    return 0
```

---

## Full example — Docker plugin

```python title="~/.xshell/plugins/docker_plugin.py"
import subprocess
from xshell.plugins.base import XShellPlugin

class DockerPlugin(XShellPlugin):
    name        = 'docker'
    description = 'Docker shortcuts: dps, dimg, dlogs, dexec'
    version     = '1.0.0'

    def on_load(self, shell):
        super().on_load(shell)
        self.register_command('dps',   self._dps,   ['--all', '-a'])
        self.register_command('dimg',  self._dimg,  ['--all'])
        self.register_command('dlogs', self._dlogs, ['-f', '--tail'])
        self.register_command('dexec', self._dexec, ['-it'])
        self.register_command('dstop', self._dstop)
        self.register_command('drm',   self._drm,   ['-f'])

    def _dps(self, shell, args):
        return self._run(['docker', 'ps'] + args[1:])

    def _dimg(self, shell, args):
        return self._run(['docker', 'images'] + args[1:])

    def _dlogs(self, shell, args):
        return self._run(['docker', 'logs'] + args[1:])

    def _dexec(self, shell, args):
        return self._run(['docker', 'exec'] + args[1:])

    def _dstop(self, shell, args):
        return self._run(['docker', 'stop'] + args[1:])

    def _drm(self, shell, args):
        return self._run(['docker', 'rm'] + args[1:])

    @staticmethod
    def _run(cmd):
        try:
            return subprocess.run(cmd).returncode
        except FileNotFoundError:
            print('docker: command not found')
            return 127
```

Load and use:

```bash
plugin load docker
dps -a
dlogs -f my-container
dexec -it my-container bash
```

---

## Publishing your plugin

1. Put the file in `plugins/` (project-local, tracked by git)
2. In a packaged or installed setup, others can drop it into their `~/.xshell/plugins/` with no code changes
3. They add the plugin name to their `config.json` `plugins` list

---

## Plugin base class API

```python
class XShellPlugin:
    name:        str   # required, unique lowercase id
    description: str   # shown in 'plugin list'
    version:     str   # e.g. '1.0.0'
    author:      str

    def on_load(self, shell):   ...   # register commands here
    def on_unload(self):        ...   # clean up
    def on_prompt(self) -> str: ...   # extra prompt text

    def register_command(self, name, fn, completions=None, help=''): ...
    def commands(self) -> dict:         ...
    def completions_for(self, cmd: str) -> list: ...
    def help_for(self, cmd: str) -> str: ...
```

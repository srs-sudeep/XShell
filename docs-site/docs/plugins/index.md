---
id: index
title: Plugin System
sidebar_position: 1
---

# Plugin System

XShell has a runtime plugin system. Plugins are Python classes that can:

- Register new shell commands
- Hook into the prompt (add extra segments)
- Run setup/teardown code on load/unload

## Architecture

```
PluginManager
  ├── loads bundled modules from xshell/plugins/builtin/
  ├── loads from ~/.xshell/plugins/         (user plugins)
  └── loads from <project-root>/plugins/    (project-local plugins)
```

Each plugin is a Python file containing exactly one subclass of `XShellPlugin`.

## Managing plugins at runtime

```bash
plugin list             # list loaded plugins with descriptions + commands
plugin available        # everything XShell can load
plugin info myplugin    # description, version, author, commands, completions
plugin load myplugin    # load ~/.xshell/plugins/myplugin.py or plugins/myplugin.py
plugin unload myplugin  # unload a loaded plugin
plugin reload myplugin  # unload + reload (picks up code edits)
```

## Configuring auto-load

Edit `~/.xshell/config.json`:

```json
{
  "plugins": ["git", "sysinfo", "calc", "myplugin"]
}
```

Plugins in this list are loaded automatically at startup. If a plugin fails to load,
a warning is printed but XShell continues normally.

## Plugin search order

When you run `plugin load <name>`:

1. Check built-in modules under `xshell/plugins/builtin/`
2. Check `~/.xshell/plugins/<name>.py`
3. Check `<project-root>/plugins/<name>.py`

`<project-root>` means the source checkout that contains `main.py`, `build.py`, and
the top-level `plugins/` directory.

## Bundled plugins

This checkout includes bundled `git`, `sysinfo`, and `calc` plugins under
`xshell/plugins/builtin/`. They are enabled by default via the config defaults.

## Writing your own

See [Writing Plugins](./writing-plugins) for a step-by-step guide.

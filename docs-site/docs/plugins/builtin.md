---
id: builtin
title: Bundled Plugins
sidebar_position: 2
---

# Bundled Plugins

This checkout includes three bundled plugins that are available out of the box:

## `git`

Shortcuts for common git workflows:

- `gst`
- `glog`
- `gdiff`
- `gadd`
- `gcommit`
- `gpush`
- `gpull`
- `gbranch`
- `gcheckout`
- `gstash`
- `grebase`

## `sysinfo`

System diagnostics commands:

- `sysinfo`
- `diskusage`
- `netinfo`
- `procs`
- `uptime`

`psutil` enables the rich CPU / memory / process information; without it, the
plugin degrades gracefully and prints installation hints for unsupported commands.

## `calc`

Safe calculator and converter commands:

- `calc`
- `convert`
- `hex2dec`
- `dec2hex`
- `dec2bin`

Use `plugin info <name>` inside XShell for the exact command descriptions and
autocomplete hints.

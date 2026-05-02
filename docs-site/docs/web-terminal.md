---
id: web-terminal
title: Web Terminal
sidebar_position: 6
---

# Web Terminal

XShell includes a browser-based terminal that uses the same core engine as the
native shell. It's powered by **Flask** and **Socket.IO** for real-time bidirectional
communication.

## Starting the web terminal

```bash
python main.py --web               # opens on http://127.0.0.1:5000
python main.py --web --port 8080   # custom port
```

The browser opens automatically. If it doesn't, navigate to `http://127.0.0.1:<port>`.

In a source checkout, the web server resolves `templates/` and `static/` from the
repository root rather than the shell's current working directory. That means
`python /full/path/to/main.py --web` works even when launched from another folder.

## Features

| Feature            | Description                                                 |
| ------------------ | ----------------------------------------------------------- |
| **ANSI colours**   | Full 16-colour ANSI rendering, including bold and dim       |
| **Theme switcher** | Click 🎨 in the title bar to change themes live             |
| **History**        | Arrow keys navigate history; ghost text shows suggestions   |
| **Ctrl+L**         | Clear the terminal output                                   |
| **Ctrl+C**         | Send ^C and clear input                                     |
| **Status bar**     | Shows connection status, CWD, current theme, last exit code |
| **Resize-aware**   | Layout adapts to window size                                |

## Architecture

```
Browser                         Server (Python)
──────────────────────────────────────────────────
user types command
  │
  ├─ socket.emit('command')  ──→  handle_command()
  │                                    │
  │                               captures stdout/stderr
  │                               runs shell.execute_line()
  │                                    │
  │  ←── socket.emit('output')  ───────┘
  │
renders ANSI text in <div>
```

Each browser tab gets its own `_WebShell` session with isolated history, aliases,
and working directory.

## Theme switching via socket

```
browser  ──→  socket.emit('get_themes')  ──→  server sends list
browser  ──→  socket.emit('set_theme', {theme: 'gruvbox'})  ──→  server switches theme
```

## Limitations vs native shell

| Feature                    | Native             | Web                 |
| -------------------------- | ------------------ | ------------------- |
| Tab completion             | Full               | Not yet (planned)   |
| PTY / interactive programs | No                 | No                  |
| Ctrl+R history search      | Yes                | No                  |
| ANSI truecolor (24-bit)    | Terminal-dependent | No (16-colour only) |
| Concurrent sessions        | N/A                | Yes (one per tab)   |

## Security note

The web server runs on `127.0.0.1` (localhost only) by default and executes
shell commands with your user permissions. **Do not expose it on a public
network interface** without adding authentication and HTTPS.

For team/remote use, add a reverse proxy (nginx, Caddy) with auth in front of it.

## Running as a background service

```bash
# Keep it running after terminal closes
nohup python main.py --web --port 5000 &

# Or with a process manager like PM2
pm2 start "python main.py --web" --name xshell-web
```

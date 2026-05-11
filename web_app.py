"""
XShell web interface.
Runs the XShell core engine behind a Flask/Socket.IO server
and serves a browser-based terminal UI.
"""

import base64
import os
import sys
import threading
import traceback
import webbrowser
from pathlib import Path

from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit

# Resolve resource paths for both dev and PyInstaller builds
_DEV_ROOT = Path(__file__).resolve().parent


def _res(rel: str) -> str:
    base = Path(getattr(sys, '_MEIPASS', _DEV_ROOT))
    return str(base / rel)


app = Flask(
    __name__,
    template_folder=_res('templates'),
    static_folder=_res('static'),
)
app.config['SECRET_KEY'] = 'xshell-secret-2025'
# Werkzeug's dev server cannot complete Engine.IO WebSocket upgrades reliably
# (AssertionError: write() before start_response). Stay on long-polling unless you
# run behind a server that supports WebSockets (e.g. eventlet with monkey_patch).
socketio = SocketIO(
    app,
    cors_allowed_origins='*',
    async_mode='threading',
    allow_upgrades=False,
    max_http_buffer_size=50 * 1024 * 1024,
)

# Per-session shell state (keyed by socket session id)
_sessions: dict = {}
_lock = threading.Lock()
# Serialise global stdout/stderr redirection — concurrent tabs would otherwise
# restore each other's streams and corrupt the HTTP/Socket.IO response.
_stdout_lock = threading.Lock()


def _get_or_create_shell(sid: str):
    with _lock:
        if sid not in _sessions:
            from xshell.config.manager import ConfigManager
            from xshell.core.autocorrect import AutoCorrect
            from xshell.core.executor import CommandExecutor
            from xshell.core.history import HistoryManager
            from xshell.core.parser import CommandParser
            from xshell.plugins.manager import PluginManager
            from xshell.core.shell import XShell
            from xshell.themes.manager import ThemeManager

            class _WebShell:
                BANNER = XShell.BANNER

                def __init__(self):
                    self.config = ConfigManager()
                    self.theme_manager = ThemeManager(self.config)
                    self.history = HistoryManager()
                    self.autocorrect = AutoCorrect()
                    self.aliases = dict(self.config.get('aliases', {}))
                    self.env = dict(os.environ)
                    self.running = True
                    self.exit_code = 0
                    self.last_exit_code = 0
                    self.parser = CommandParser()
                    self.executor = CommandExecutor(self)
                    self.plugin_manager = PluginManager(self)
                    self.plugin_manager.load_configured_plugins()
                    self._background_jobs = {}
                    self._job_counter = 0

                def _print_banner(self) -> None:
                    XShell._print_banner(self)

                def _apply_terminal_colors(self) -> None:
                    XShell._apply_terminal_colors(self)

                def execute_line(self, line: str) -> int:
                    import re
                    line = self._expand_aliases(line)
                    # Inline assignment
                    if re.match(r'^[A-Za-z_]\w*=', line) and ' ' not in line.split('=')[0]:
                        k, _, v = line.partition('=')
                        v = v.strip('"\'')
                        self.env[k] = v
                        os.environ[k] = v
                        return 0
                    cmd_list = self.parser.parse(line)
                    if not cmd_list.pipelines:
                        return 0
                    return self.executor.execute_command_list(cmd_list)

                def _expand_aliases(self, line: str) -> str:
                    parts = line.split(None, 1)
                    if parts and parts[0] in self.aliases:
                        rest = (' ' + parts[1]) if len(parts) > 1 else ''
                        return self.aliases[parts[0]] + rest
                    return line

                def get_completions(self, partial: str):
                    """Return tab completion candidates for partial input."""
                    from xshell.core.builtins import list_builtins
                    words = partial.split()
                    is_cmd = len(words) == 0 or (len(words) == 1 and not partial.endswith(' '))
                    prefix = words[-1] if words and not partial.endswith(' ') else ''

                    results = []
                    if is_cmd:
                        results += [b for b in list_builtins() if b.startswith(prefix)]
                        results += [a for a in self.aliases if a.startswith(prefix)]
                        if self.plugin_manager:
                            results += [c for c in self.plugin_manager.all_commands() if c.startswith(prefix)]
                        for d in os.environ.get('PATH', '').split(os.pathsep):
                            try:
                                for e in os.scandir(d):
                                    n = e.name
                                    if sys.platform == 'win32':
                                        n = os.path.splitext(n)[0]
                                    if n.lower().startswith(prefix.lower()):
                                        results.append(n)
                            except OSError:
                                pass
                    else:
                        expanded = os.path.expanduser(os.path.expandvars(prefix))
                        if os.sep in expanded or (os.altsep and os.altsep in expanded):
                            dirpart, filepart = os.path.split(expanded)
                            base = dirpart or '.'
                        else:
                            base = '.'
                            filepart = expanded
                        try:
                            for e in sorted(os.scandir(base), key=lambda x: x.name.lower()):
                                name = e.name
                                if name.lower().startswith(filepart.lower()):
                                    full = os.path.join(dirpart if os.sep in expanded else '', name)
                                    if e.is_dir():
                                        full += '/'
                                    results.append(full)
                        except OSError:
                            pass

                    # Check plugin-specific completions
                    if not is_cmd and words and self.plugin_manager:
                        cmd_name = words[0]
                        fn = self.plugin_manager.get_command(cmd_name)
                        if fn:
                            plugin = next(
                                (p for p in self.plugin_manager._plugins.values()
                                 if cmd_name in p.commands()),
                                None
                            )
                            if plugin:
                                comps = plugin.completions_for(cmd_name)
                                if comps:
                                    results = [c for c in comps(self, prefix) if c.startswith(prefix)]

                    # Deduplicate and limit
                    seen = set()
                    unique = []
                    for r in results:
                        if r not in seen:
                            seen.add(r)
                            unique.append(r)
                        if len(unique) >= 30:
                            break
                    return unique

            _sessions[sid] = _WebShell()
        return _sessions[sid]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download/<path:filename>')
def download_file(filename):
    """Server-side file download endpoint."""
    safe = os.path.normpath(os.path.join(os.getcwd(), filename))
    if not safe.startswith(os.getcwd()):
        return 'Forbidden', 403
    if not os.path.isfile(safe):
        return 'Not found', 404
    return send_file(safe, as_attachment=True)


# ---------------------------------------------------------------------------
# Socket.IO events
# ---------------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    sid = _get_sid()
    shell = _get_or_create_shell(sid)
    parts = []
    if shell.config.get('show_banner', True):
        import io
        with _stdout_lock:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            cap = io.StringIO()
            sys.stdout = cap
            sys.stderr = cap
            try:
                shell._print_banner()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        parts.append(cap.getvalue())
    parts.append(_welcome(after_banner=bool(parts)))
    emit('output', {'data': ''.join(parts), 'type': 'info', 'cwd': os.getcwd()})


@socketio.on('disconnect')
def handle_disconnect():
    sid = _get_sid()
    with _lock:
        _sessions.pop(sid, None)


@socketio.on('command')
def handle_command(payload):
    sid = _get_sid()
    command = payload if isinstance(payload, str) else payload.get('data', '')
    command = command.strip()
    if not command:
        return

    shell = _get_or_create_shell(sid)
    shell.history.add(command)

    import io
    with _stdout_lock:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        cap_out = io.StringIO()
        cap_err = io.StringIO()
        sys.stdout = cap_out
        sys.stderr = cap_err
        exit_code = 0
        try:
            exit_code = shell.execute_line(command)
        except SystemExit as e:
            exit_code = e.code or 0
            shell.running = False
        except Exception:
            cap_err.write(traceback.format_exc())
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        out = cap_out.getvalue()
        err = cap_err.getvalue()

    if out:
        emit('output', {'data': out, 'type': 'stdout'})
    if err:
        emit('output', {'data': err, 'type': 'stderr'})

    emit('output', {
        'data': '\n', 'type': 'prompt',
        'cwd': os.getcwd(), 'code': exit_code,
    })


@socketio.on('complete')
def handle_complete(payload):
    """Tab completion — return candidates for partial input."""
    sid = _get_sid()
    partial = payload.get('partial', '') if isinstance(payload, dict) else ''
    shell = _get_or_create_shell(sid)
    try:
        completions = shell.get_completions(partial)
    except Exception:
        completions = []
    emit('completions', {'completions': completions})


@socketio.on('file_upload')
def handle_file_upload(payload):
    """Receive a base64-encoded file from the browser."""
    if not isinstance(payload, dict):
        emit('output', {'data': 'Upload failed: invalid payload\n', 'type': 'stderr'})
        return
    filename = payload.get('filename', 'upload')
    content_b64 = payload.get('content', '')
    try:
        content = base64.b64decode(content_b64)
        # Save to CWD
        safe_name = os.path.basename(filename)
        dest = os.path.join(os.getcwd(), safe_name)
        with open(dest, 'wb') as fh:
            fh.write(content)
        emit('output', {
            'data': f"File '{safe_name}' uploaded ({len(content)} bytes) → {dest}\n",
            'type': 'info',
        })
        emit('output', {'data': '', 'type': 'prompt', 'cwd': os.getcwd(), 'code': 0})
    except Exception as e:
        emit('output', {'data': f"Upload failed: {e}\n", 'type': 'stderr'})
        emit('output', {'data': '', 'type': 'prompt', 'cwd': os.getcwd(), 'code': 1})


@socketio.on('file_download_request')
def handle_file_download(payload):
    """Stream a file back to the browser as base64."""
    filename = payload.get('filename', '')
    safe = os.path.normpath(os.path.join(os.getcwd(), filename))
    if not safe.startswith(os.getcwd()):
        emit('output', {'data': "Download denied: path traversal\n", 'type': 'stderr'})
        return
    if not os.path.isfile(safe):
        emit('output', {'data': f"File not found: {filename}\n", 'type': 'stderr'})
        return
    try:
        with open(safe, 'rb') as fh:
            content = base64.b64encode(fh.read()).decode('ascii')
        emit('file_download', {'filename': os.path.basename(safe), 'content': content})
    except Exception as e:
        emit('output', {'data': f"Download failed: {e}\n", 'type': 'stderr'})


@socketio.on('resize')
def handle_resize(payload):
    pass


@socketio.on('get_themes')
def handle_get_themes():
    from xshell.config.manager import ConfigManager
    from xshell.themes.manager import ThemeManager
    tm = ThemeManager(ConfigManager())
    theme_data = {
        name: tm.get_theme(name).get('colors', {})
        for name in tm.list_themes()
    }
    emit('themes', {'themes': tm.list_themes(), 'colors': theme_data})


@socketio.on('set_theme')
def handle_set_theme(payload):
    sid = _get_sid()
    shell = _get_or_create_shell(sid)
    if not isinstance(payload, dict):
        payload = {}
    name = payload.get('theme', 'default')
    if shell.theme_manager.set_theme(name):
        colors = shell.theme_manager.current_theme.get('colors', {})
        emit('theme_changed', {'theme': name, 'colors': colors})
    else:
        emit('output', {'data': f"Theme '{name}' not found.\n", 'type': 'stderr'})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sid():
    from flask import request
    return request.sid


def _welcome(*, after_banner: bool = False):
    """Opening text; when after_banner is True, the ASCII banner was already shown."""
    from xshell import __version__
    cwd = os.getcwd()
    if after_banner:
        return (
            f"Working directory: {cwd}\n"
            f"Drag files to upload. Right-click for options.\n\n"
        )
    return (
        f"XShell v{__version__} — Web Terminal\n"
        f"Working directory: {cwd}\n"
        f"Type 'help' to list commands. Drag files to upload. Right-click for options.\n\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_web(port: int = 5000, open_browser: bool = True) -> None:
    for p in range(port, port + 20):
        try:
            print(f"Starting XShell web server on http://127.0.0.1:{p}")
            if open_browser:
                threading.Timer(1.0, lambda: webbrowser.open(f'http://127.0.0.1:{p}')).start()
            socketio.run(
                app,
                host='127.0.0.1',
                port=p,
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=True,
            )
            break
        except OSError:
            print(f"Port {p} in use, trying next…")
    else:
        print("Could not find an available port (tried 5000-5019)", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    run_web()

"""
XShell main REPL.
Uses prompt_toolkit for cross-platform readline, syntax highlighting, tab completion,
history search (Ctrl+R), and key bindings.
"""

import getpass
import os
import socket
import sys
import time
from pathlib import Path
from typing import Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style

try:
    from pygments.lexers.shell import BashLexer
    _HAS_PYGMENTS = True
except ImportError:
    _HAS_PYGMENTS = False

from ..config.manager import ConfigManager
from ..plugins.manager import PluginManager
from ..themes.manager import ThemeManager
from .autocorrect import AutoCorrect
from .builtins import list_builtins
from .executor import CommandExecutor
from .history import HistoryManager
from .parser import CommandParser

# ---------------------------------------------------------------------------
# Tab completer
# ---------------------------------------------------------------------------

class XShellCompleter(Completer):
    def __init__(self, shell: 'XShell'):
        self.shell = shell

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        words = text.split()
        word = document.get_word_before_cursor(WORD=True)

        is_command = len(words) == 0 or (len(words) == 1 and not text.endswith(' '))

        if is_command:
            yield from self._complete_command(word)
        else:
            # Check if current word starts with - to suggest flags
            if word.startswith('-'):
                return
            yield from self._complete_path(word)

    def _complete_command(self, prefix: str):
        seen = set()
        # Built-ins
        for name in list_builtins():
            if name.startswith(prefix) and name not in seen:
                seen.add(name)
                yield Completion(name, start_position=-len(prefix), display_meta='builtin')
        # Aliases
        for name in self.shell.aliases:
            if name.startswith(prefix) and name not in seen:
                seen.add(name)
                yield Completion(name, start_position=-len(prefix), display_meta='alias')
        # Plugin commands
        if self.shell.plugin_manager:
            for name in self.shell.plugin_manager.all_commands():
                if name.startswith(prefix) and name not in seen:
                    seen.add(name)
                    yield Completion(name, start_position=-len(prefix), display_meta='plugin')
        # PATH executables
        for d in os.environ.get('PATH', '').split(os.pathsep):
            try:
                for entry in os.scandir(d):
                    n = entry.name
                    if sys.platform == 'win32':
                        n = os.path.splitext(n)[0]
                    if n.lower().startswith(prefix.lower()) and n not in seen:
                        seen.add(n)
                        yield Completion(n, start_position=-len(prefix), display_meta='cmd')
            except OSError:
                continue

    def _complete_path(self, prefix: str):
        expanded = os.path.expanduser(prefix)
        if os.path.sep in expanded or (os.altsep and os.altsep in expanded):
            dirpart, filepart = os.path.split(expanded)
            base = dirpart or '.'
        else:
            base = '.'
            filepart = expanded

        try:
            for entry in sorted(os.scandir(base), key=lambda e: e.name.lower()):
                name = entry.name
                if name.lower().startswith(filepart.lower()):
                    full = os.path.join(dirpart if os.path.sep in expanded else '', name)
                    full = full + ('/' if entry.is_dir() else '')
                    yield Completion(
                        full,
                        start_position=-len(prefix),
                        display_meta='dir' if entry.is_dir() else 'file',
                    )
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Key bindings
# ---------------------------------------------------------------------------

def _build_keybindings(vi_mode: bool = False) -> KeyBindings:
    kb = KeyBindings()

    @kb.add('c-l')
    def _clear(event):
        clear()

    @kb.add('c-d')
    def _eof(event):
        event.app.exit(exception=EOFError)

    # Accept suggestion ghost text with right arrow
    @kb.add('right')
    def _accept_suggestion(event):
        buf = event.app.current_buffer
        suggestion = buf.suggestion
        if suggestion:
            buf.insert_text(suggestion.text)
        else:
            buf.cursor_right()

    return kb


# ---------------------------------------------------------------------------
# Main shell class
# ---------------------------------------------------------------------------

class XShell:
    BANNER = r"""
  __  __ _____  _          _ _
 \ \/ // ____|| |        | | |
  >  <| (___  | |__   ___| | |
 / /\ \\___ \ | '_ \ / _ \ | |
/ ____ \___) || | | |  __/ | |
/_/    \_\____/ |_| |_|\___|_|_|
"""

    def __init__(
        self,
        load_plugins: bool = True,
        theme: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        self.config = ConfigManager(config_path)
        self.theme_manager = ThemeManager(self.config)
        if theme:
            self.theme_manager.set_theme(theme)

        self.history = HistoryManager(
            max_size=self.config.get('history_size', 2000)
        )
        self.parser = CommandParser()
        self.executor = CommandExecutor(self)
        self.autocorrect = AutoCorrect()

        self.plugin_manager: Optional[PluginManager] = None
        if load_plugins:
            self.plugin_manager = PluginManager(self)
            self.plugin_manager.load_configured_plugins()

        self.env = dict(os.environ)
        self.aliases: dict = dict(self.config.get('aliases', {}))
        self.running = True
        self.exit_code = 0
        self.last_exit_code = 0
        self._background_jobs: Dict[int, dict] = {}
        self._job_counter = 0
        self._last_cmd_time: float = 0.0

        # Source startup files
        self._source_rc()

    # ------------------------------------------------------------------
    # REPL
    # ------------------------------------------------------------------

    def run(self) -> int:
        self._print_startup_view()

        history_file = self.history.path
        vi_mode = self.config.get('vi_mode', False)

        session: PromptSession = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=XShellCompleter(self),
            lexer=PygmentsLexer(BashLexer) if _HAS_PYGMENTS else None,
            style=self._build_style(),
            key_bindings=_build_keybindings(vi_mode),
            complete_while_typing=self.config.get('complete_while_typing', True),
            mouse_support=False,
            enable_history_search=True,
            vi_mode=vi_mode,
            rprompt=self._build_rprompt if self.config.get('rprompt', True) else None,
        )

        self._check_per_project_rc()

        while self.running:
            try:
                prompt_text = self._build_prompt()
                t_start = time.time()
                line = session.prompt(ANSI(prompt_text))
                if not line.strip():
                    continue
                self.history.add(line)
                self.last_exit_code = self.execute_line(line)
                self._last_cmd_time = time.time() - t_start
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                print()
                break

        return self.exit_code

    def execute_line(self, line: str) -> int:
        """Execute a raw input line. Returns exit code."""
        line = self._expand_aliases(line)
        # Handle inline variable assignment: VAR=value
        import re
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

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_prompt(self) -> str:
        theme = self.theme_manager.current_theme
        colors = theme.get('colors', {})

        user_color = _ansi(colors.get('prompt_user', 'bright_cyan'))
        host_color = _ansi(colors.get('prompt_host', 'bright_green'))
        cwd_color  = _ansi(colors.get('prompt_cwd', 'bright_yellow'))
        git_color  = _ansi(colors.get('prompt_git', 'bright_magenta'))
        reset      = '\033[0m'

        user = getpass.getuser()
        host = socket.gethostname().split('.')[0]
        cwd  = _short_cwd()
        git  = _git_branch()
        git_status = _git_status_indicator()

        git_part = f" {git_color}({git}{git_status}){reset}" if git else ''

        # Notify plugins
        plugin_parts = ''
        if self.plugin_manager:
            for p in self.plugin_manager._plugins.values():
                try:
                    extra = p.on_prompt()
                    if extra:
                        plugin_parts += extra
                except Exception:
                    pass

        venv = _venv_name()
        venv_part = f"\033[33m({venv}) \033[0m" if venv else ''

        fmt = theme.get('prompt', {}).get('format', '{default}')
        if fmt == '{default}' or not fmt:
            return (
                f"{venv_part}"
                f"{user_color}{user}{reset}@"
                f"{host_color}{host}{reset}:"
                f"{cwd_color}{cwd}{reset}"
                f"{git_part}"
                f"{plugin_parts}"
                f" \033[1m$\033[0m "
            )

        return (
            fmt
            .replace('{user}', f"{user_color}{user}{reset}")
            .replace('{host}', f"{host_color}{host}{reset}")
            .replace('{cwd}',  f"{cwd_color}{cwd}{reset}")
            .replace('{git}',  git_part)
            .replace('{$}',    '\033[1m$\033[0m')
            + ' '
        )

    def _build_rprompt(self) -> ANSI:
        """Right-aligned prompt: exit code + last command duration."""
        parts = []
        code = self.last_exit_code
        if code == 0:
            parts.append('\033[32m✓\033[0m')
        else:
            parts.append(f'\033[31m✗ {code}\033[0m')

        elapsed = self._last_cmd_time
        if elapsed > 0.1:
            parts.append(f'\033[2m{elapsed:.1f}s\033[0m')

        now = time.strftime('%H:%M')
        parts.append(f'\033[2m{now}\033[0m')

        return ANSI('  '.join(parts))

    def _build_style(self) -> Style:
        theme = self.theme_manager.current_theme
        colors = theme.get('colors', {})
        bg = colors.get('background', '#1e1e1e')
        fg = colors.get('foreground', '#f0f0f0')
        return Style.from_dict({
            '': f'bg:{bg} {fg}',
            'completion-menu.completion': f'bg:{bg} {fg}',
            'completion-menu.completion.current': 'bg:#444 bold',
            'auto-suggestion': '#555555 italic',
        })

    # ------------------------------------------------------------------
    # RC / startup files
    # ------------------------------------------------------------------

    def _source_rc(self) -> None:
        """Source ~/.xshell/rc.xsh on startup."""
        if sys.platform == 'win32':
            rc = Path(os.environ.get('APPDATA', Path.home())) / 'XShell' / 'rc.xsh'
        else:
            rc = Path.home() / '.xshell' / 'rc.xsh'

        if rc.exists():
            try:
                with open(rc, encoding='utf-8') as fh:
                    for raw_line in fh:
                        line = raw_line.strip()
                        if line and not line.startswith('#'):
                            self.execute_line(line)
            except Exception as e:
                print(f"[rc] warning: {e}", file=sys.stderr)

    def _check_per_project_rc(self) -> None:
        """Source .xshellrc in current directory if it exists."""
        rc = Path(os.getcwd()) / '.xshellrc'
        if rc.exists():
            try:
                with open(rc, encoding='utf-8') as fh:
                    for raw_line in fh:
                        line = raw_line.strip()
                        if line and not line.startswith('#'):
                            self.execute_line(line)
                print("\033[2m[sourced .xshellrc]\033[0m")
            except Exception as e:
                print(f"[.xshellrc] warning: {e}", file=sys.stderr)

    # ------------------------------------------------------------------
    # Alias expansion
    # ------------------------------------------------------------------

    def _expand_aliases(self, line: str) -> str:
        parts = line.split(None, 1)
        if parts and parts[0] in self.aliases:
            rest = (' ' + parts[1]) if len(parts) > 1 else ''
            return self.aliases[parts[0]] + rest
        return line

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    def _print_startup_view(self) -> None:
        if self.config.get('show_banner', True):
            self._print_banner()
        if self.config.get('show_neofetch', True):
            try:
                self.execute_line('neofetch')
            except Exception:
                pass

    def _print_banner(self) -> None:
        from xshell import __version__
        theme = self.theme_manager.current_theme
        color = _ansi(theme.get('colors', {}).get('prompt_host', 'bright_cyan'))
        reset = '\033[0m'
        print(f"{color}{self.BANNER}{reset}")
        print(f"  XShell v{__version__}  |  type 'help' for commands  |  Ctrl+D to exit\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_COLOR_MAP = {
    'black':          '\033[30m',
    'red':            '\033[31m',
    'green':          '\033[32m',
    'yellow':         '\033[33m',
    'blue':           '\033[34m',
    'magenta':        '\033[35m',
    'cyan':           '\033[36m',
    'white':          '\033[37m',
    'bright_black':   '\033[90m',
    'bright_red':     '\033[91m',
    'bright_green':   '\033[92m',
    'bright_yellow':  '\033[93m',
    'bright_blue':    '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan':    '\033[96m',
    'bright_white':   '\033[97m',
}


def _ansi(name: str) -> str:
    if name.startswith('#'):
        return ''
    return _COLOR_MAP.get(name.lower(), '\033[0m')


def _short_cwd() -> str:
    cwd = os.getcwd()
    home = str(Path.home())
    if cwd.startswith(home):
        cwd = '~' + cwd[len(home):]
    parts = cwd.replace('\\', '/').split('/')
    if len(parts) > 3:
        cwd = '/'.join(['…'] + parts[-2:])
    return cwd


def _git_branch() -> Optional[str]:
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=1,
        )
        branch = result.stdout.strip()
        if branch and branch != 'HEAD':
            return branch
        if branch == 'HEAD':
            sha = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, timeout=1,
            ).stdout.strip()
            return f"({sha})"
    except Exception:
        pass
    return None


def _git_status_indicator() -> str:
    """Return ±N/? counts for staged/unstaged changes."""
    try:
        import subprocess
        out = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            text=True, timeout=1, stderr=subprocess.DEVNULL
        )
        staged = sum(1 for l in out.splitlines() if l[:1] not in (' ', '?'))
        unstaged = sum(1 for l in out.splitlines() if l[1:2] in ('M', 'D') or l[:1] == '?')
        parts = []
        if staged:
            parts.append(f'+{staged}')
        if unstaged:
            parts.append(f'~{unstaged}')
        return (' ' + ' '.join(parts)) if parts else ''
    except Exception:
        return ''


def _venv_name() -> Optional[str]:
    venv = os.environ.get('VIRTUAL_ENV') or os.environ.get('CONDA_DEFAULT_ENV')
    if venv:
        return os.path.basename(venv)
    return None

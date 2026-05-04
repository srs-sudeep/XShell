"""
Built-in commands for XShell.
All builtins receive (shell, args) and return an exit code (int).
"""

import glob
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .shell import XShell


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict = {}


def builtin(name: str):
    def decorator(fn):
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_builtin(name: str):
    return _REGISTRY.get(name)


def list_builtins() -> List[str]:
    return sorted(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_err(msg: str) -> None:
    print(f"\033[31m{msg}\033[0m", file=sys.stderr)


def _print_ok(msg: str) -> None:
    print(f"\033[32m{msg}\033[0m")


BOLD  = '\033[1m'
DIM   = '\033[2m'
CYAN  = '\033[36m'
YEL   = '\033[33m'
MAG   = '\033[35m'
GRN   = '\033[32m'
RESET = '\033[0m'

_NAMED_FG: dict = {
    'black':          '\033[30m', 'bright_black':   '\033[90m',
    'red':            '\033[31m', 'bright_red':     '\033[91m',
    'green':          '\033[32m', 'bright_green':   '\033[92m',
    'yellow':         '\033[33m', 'bright_yellow':  '\033[93m',
    'blue':           '\033[34m', 'bright_blue':    '\033[94m',
    'magenta':        '\033[35m', 'bright_magenta': '\033[95m',
    'cyan':           '\033[36m', 'bright_cyan':    '\033[96m',
    'white':          '\033[37m', 'bright_white':   '\033[97m',
}


def _hex_fg(color: str) -> str:
    """Return an ANSI fg escape for a named or #rrggbb color."""
    if color.startswith('#') and len(color) == 7:
        try:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            return f'\033[38;2;{r};{g};{b}m'
        except ValueError:
            pass
    return _NAMED_FG.get(color.lower(), CYAN)


def _hex_bg(color: str) -> str:
    """Return an ANSI bg escape for a #rrggbb color."""
    if color.startswith('#') and len(color) == 7:
        try:
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            return f'\033[48;2;{r};{g};{b}m'
        except ValueError:
            pass
    return ''


def _wants_help(args: List[str]) -> bool:
    return '--help' in args or '-h' in args


def _help(usage: str, description: str, options: Optional[List[tuple]] = None,
          examples: Optional[List[str]] = None) -> int:
    """Print a uniform --help block and return 0."""
    print(f'\n  {BOLD}Usage:{RESET}  {usage}')
    print(f'\n  {description}')
    if options:
        print(f'\n  {BOLD}Options / sub-commands:{RESET}')
        w = max(len(o[0]) for o in options)
        for opt, desc in options:
            print(f'    {CYAN}{opt:<{w}}{RESET}  {desc}')
    if examples:
        print(f'\n  {BOLD}Examples:{RESET}')
        for ex in examples:
            print(f'    {DIM}{ex}{RESET}')
    print()
    return 0


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

@builtin('cd')
def cmd_cd(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('cd [dir]',
            'Change the current working directory.',
            [('-', 'Switch to the previous directory'),
             ('~', 'Switch to the home directory')],
            ['cd /tmp', 'cd -', 'cd ~/projects'])
    if len(args) < 2:
        target = os.environ.get('HOME', str(Path.home()))
    elif args[1] == '-':
        target = shell.env.get('OLDPWD', os.getcwd())
    else:
        target = os.path.expanduser(os.path.expandvars(args[1]))

    try:
        old = os.getcwd()
        os.chdir(target)
        shell.env['OLDPWD'] = old
        shell.env['PWD'] = os.getcwd()
        return 0
    except FileNotFoundError:
        _print_err(f"cd: {args[1]}: No such file or directory")
        return 1
    except NotADirectoryError:
        _print_err(f"cd: {args[1]}: Not a directory")
        return 1
    except PermissionError:
        _print_err(f"cd: {args[1]}: Permission denied")
        return 1


@builtin('pwd')
def cmd_pwd(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('pwd', 'Print the current working directory.')
    print(os.getcwd())
    return 0


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------

@builtin('ls')
def cmd_ls(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('ls [-a] [-l] [path ...]',
            'List directory contents.',
            [('-a, --all', 'Include hidden files (dotfiles)'),
             ('-l',        'Long format: type, size, name')],
            ['ls', 'ls -la /tmp', 'ls -a ~/.xshell'])
    show_all = '-a' in args or '--all' in args
    long_fmt = '-l' in args
    paths = [a for a in args[1:] if not a.startswith('-')] or ['.']

    for path in paths:
        try:
            entries = sorted(os.listdir(path))
        except OSError as e:
            _print_err(f"ls: {path}: {e.strerror}")
            continue

        if not show_all:
            entries = [e for e in entries if not e.startswith('.')]

        if long_fmt:
            for e in entries:
                full = os.path.join(path, e)
                try:
                    stat = os.stat(full)
                    kind = 'd' if os.path.isdir(full) else '-'
                    size = stat.st_size
                    color = '\033[34m' if os.path.isdir(full) else '\033[0m'
                    print(f"{kind} {size:>10}  {color}{e}\033[0m")
                except OSError:
                    print(e)
        else:
            cols = []
            for e in entries:
                full = os.path.join(path, e)
                if os.path.isdir(full):
                    cols.append(f"\033[34m{e}/\033[0m")
                elif os.access(full, os.X_OK) and sys.platform != 'win32':
                    cols.append(f"\033[32m{e}\033[0m")
                else:
                    cols.append(e)
            print('  '.join(cols))
    return 0


# Alias dir -> ls on all platforms
@builtin('dir')
def cmd_dir(shell: 'XShell', args: List[str]) -> int:
    return cmd_ls(shell, ['ls'] + args[1:])


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

@builtin('echo')
def cmd_echo(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('echo [-n] [-e] [text ...]',
            'Print text to standard output.',
            [('-n', 'Do not print a trailing newline'),
             ('-e', 'Interpret backslash escape sequences (\\n, \\t, …)')],
            ['echo hello world', 'echo -n no newline', 'echo -e "line1\\nline2"'])
    newline = True
    interpret = False
    parts = args[1:]
    filtered = []
    for p in parts:
        if p == '-n':
            newline = False
        elif p == '-e':
            interpret = True
        else:
            filtered.append(p)

    text = ' '.join(filtered)
    if interpret:
        text = text.encode('raw_unicode_escape').decode('unicode_escape')
    print(text, end='\n' if newline else '')
    return 0


# ---------------------------------------------------------------------------
# Terminal control
# ---------------------------------------------------------------------------

@builtin('clear')
def cmd_clear(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('clear', 'Clear the terminal screen.')
    if sys.platform == 'win32':
        os.system('cls')
    else:
        print('\033[2J\033[H', end='')
    return 0


@builtin('cls')
def cmd_cls(shell: 'XShell', args: List[str]) -> int:
    return cmd_clear(shell, args)


@builtin('banner')
def cmd_banner(shell: 'XShell', args: List[str]) -> int:
    """Show the XShell banner."""
    if _wants_help(args):
        return _help('banner', 'Print the XShell startup banner.')
    shell._print_banner()
    return 0


def _format_uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, sec = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m {sec}s"
    if hours:
        return f"{hours}h {minutes}m {sec}s"
    return f"{minutes}m {sec}s"


@builtin('neofetch')
def cmd_neofetch(shell: 'XShell', args: List[str]) -> int:
    """Show a neofetch-style XShell system summary."""
    if _wants_help(args):
        return _help('neofetch',
            'Show a neofetch-style summary with the XShell logo and system details.',
            examples=['neofetch'])

    try:
        import psutil  # type: ignore
    except ImportError:
        psutil = None

    from xshell import __version__

    uname = platform.uname()
    user = os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'
    host = uname.node.split('.')[0] if uname.node else 'localhost'

    uptime = 'n/a'
    mem_line = 'n/a'
    if psutil is not None:
        try:
            import time
            uptime = _format_uptime(int(time.time() - psutil.boot_time()))
            vm = psutil.virtual_memory()
            used_gb = vm.used / (1024 ** 3)
            total_gb = vm.total / (1024 ** 3)
            mem_line = f"{used_gb:.1f} GiB / {total_gb:.1f} GiB ({vm.percent:.0f}%)"
        except Exception:
            pass

    theme_colors = shell.theme_manager.current_theme.get('colors', {})
    accent = _hex_fg(theme_colors.get('prompt_host', 'bright_cyan'))
    label  = _hex_fg(theme_colors.get('prompt_cwd',  'bright_yellow'))

    # Color palette swatch — one █ block per themed key
    swatch_keys = ['prompt_user', 'prompt_host', 'prompt_cwd', 'prompt_git',
                   'error', 'success', 'warning', 'info']
    swatch = ''
    for key in swatch_keys:
        c = theme_colors.get(key, '')
        swatch += f'{_hex_fg(c)}███{RESET}' if c else ''

    info = [
        f"{BOLD}{accent}{user}@{host}{RESET}",
        f"{label}OS{RESET}:       {uname.system} {uname.release} ({uname.machine})",
        f"{label}Kernel{RESET}:   {uname.version.split(':')[0]}",
        f"{label}Shell{RESET}:    XShell {__version__}",
        f"{label}Python{RESET}:   {platform.python_version()}",
        f"{label}Uptime{RESET}:   {uptime}",
        f"{label}Memory{RESET}:   {mem_line}",
        f"{label}Theme{RESET}:    {shell.theme_manager.current_name}",
        f"{label}Colors{RESET}:   {theme_colors.get('background', '')}  {theme_colors.get('foreground', '')}",
        f"{label}PWD{RESET}:      {os.getcwd()}",
        '',
        swatch,
    ]

    logo = shell.BANNER.strip('\n').splitlines()
    logo_w = max((len(line) for line in logo), default=0)
    rows = max(len(logo), len(info))

    print()
    for i in range(rows):
        left = logo[i] if i < len(logo) else ''
        right = info[i] if i < len(info) else ''
        print(f"{accent}{left:<{logo_w}}{RESET}  {right}")
    print()
    return 0


@builtin('fetch')
def cmd_fetch(shell: 'XShell', args: List[str]) -> int:
    """Alias for neofetch."""
    return cmd_neofetch(shell, ['neofetch'] + args[1:])


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

@builtin('history')
def cmd_history(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('history [-c] [-n N]',
            'Show or manage the command history.',
            [('-c, --clear', 'Clear all history entries'),
             ('-n, --last N', 'Show only the last N entries')],
            ['history', 'history -n 20', 'history -c'])
    if '-c' in args or '--clear' in args:
        shell.history.clear()
        _print_ok("History cleared.")
        return 0

    n = None
    for i, a in enumerate(args):
        if a in ('-n', '--last') and i + 1 < len(args):
            try:
                n = int(args[i + 1])
            except ValueError:
                pass

    entries = shell.history.get_all()
    if n:
        entries = entries[-n:]

    for idx, entry in enumerate(entries, 1):
        print(f"  {idx:4d}  {entry}")
    return 0


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

@builtin('alias')
def cmd_alias(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('alias [name[=value] ...]',
            'Define or display shell aliases.',
            [('alias',          'List all current aliases'),
             ('alias ll',       'Show the value of alias ll'),
             ('alias ll=ls -l', 'Define a new alias')],
            ['alias', 'alias ll="ls -l"', r'alias gs=git\ status'])
    if len(args) == 1:
        for name, val in sorted(shell.aliases.items()):
            print(f"alias {name}='{val}'")
        return 0

    for spec in args[1:]:
        if '=' in spec:
            name, _, value = spec.partition('=')
            shell.aliases[name.strip()] = value.strip().strip("'\"")
        else:
            val = shell.aliases.get(spec)
            if val:
                print(f"alias {spec}='{val}'")
            else:
                _print_err(f"alias: {spec}: not found")
    return 0


@builtin('unalias')
def cmd_unalias(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('unalias name [name ...]',
            'Remove one or more shell aliases.',
            examples=['unalias ll', 'unalias ll gs'])
    if len(args) < 2:
        _print_err("unalias: usage: unalias name [name ...]")
        return 1
    for name in args[1:]:
        if name in shell.aliases:
            del shell.aliases[name]
        else:
            _print_err(f"unalias: {name}: not found")
    return 0


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

@builtin('export')
def cmd_export(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('export [NAME[=VALUE] ...]',
            'Set environment variables (exports them to child processes).',
            [('export',          'List all exported variables'),
             ('export FOO=bar',  'Set and export FOO'),
             ('export FOO',      'Export an already-set shell variable')],
            ['export EDITOR=vim', 'export PATH="$PATH:/usr/local/bin"'])
    if len(args) == 1:
        for k, v in sorted(os.environ.items()):
            print(f"export {k}={v!r}")
        return 0

    for spec in args[1:]:
        if '=' in spec:
            k, _, v = spec.partition('=')
            os.environ[k] = v
            shell.env[k] = v
        else:
            if spec in shell.env:
                os.environ[spec] = shell.env[spec]
    return 0


@builtin('unset')
def cmd_unset(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('unset name [name ...]',
            'Remove shell and environment variables.',
            examples=['unset TMPDIR', 'unset FOO BAR'])
    for name in args[1:]:
        os.environ.pop(name, None)
        shell.env.pop(name, None)
    return 0


@builtin('env')
def cmd_env(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('env', 'Print all environment variables (KEY=value, sorted).')
    for k, v in sorted(os.environ.items()):
        print(f"{k}={v}")
    return 0


# ---------------------------------------------------------------------------
# File operations (cross-platform fallbacks)
# ---------------------------------------------------------------------------

@builtin('mkdir')
def cmd_mkdir(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('mkdir [-p] dir [dir ...]',
            'Create one or more directories.',
            [('-p', 'Create parent directories as needed; no error if directory exists')],
            ['mkdir mydir', 'mkdir -p a/b/c'])
    parents = '-p' in args
    for d in [a for a in args[1:] if not a.startswith('-')]:
        try:
            Path(d).mkdir(parents=parents, exist_ok=parents)
        except FileExistsError:
            _print_err(f"mkdir: {d}: File exists")
        except OSError as e:
            _print_err(f"mkdir: {d}: {e.strerror}")
    return 0


@builtin('rm')
def cmd_rm(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('rm [-r] [-f] path [path ...]',
            'Remove files or directories.',
            [('-r, -rf', 'Recursively remove directories and their contents'),
             ('-f',      'Ignore non-existent files; suppress errors')],
            ['rm file.txt', 'rm -r old_dir/', 'rm -rf build/'])
    recursive = '-r' in args or '-rf' in args or '-fr' in args
    force = '-f' in args or '-rf' in args
    targets = [a for a in args[1:] if not a.startswith('-')]
    for t in targets:
        matches = glob.glob(t)
        if not matches and not force:
            _print_err(f"rm: {t}: No such file or directory")
            continue
        for path in matches:
            try:
                if os.path.isdir(path):
                    if recursive:
                        shutil.rmtree(path)
                    else:
                        _print_err(f"rm: {path}: Is a directory")
                else:
                    os.remove(path)
            except OSError as e:
                if not force:
                    _print_err(f"rm: {path}: {e.strerror}")
    return 0


@builtin('cp')
def cmd_cp(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('cp [-r] source [source ...] dest',
            'Copy files or directories.',
            [('-r, -R', 'Copy directories recursively')],
            ['cp a.txt b.txt', 'cp -r src/ dest/'])
    recursive = '-r' in args or '-R' in args
    paths = [a for a in args[1:] if not a.startswith('-')]
    if len(paths) < 2:
        _print_err("cp: missing destination")
        return 1
    *sources, dest = paths
    for src in sources:
        try:
            if os.path.isdir(src):
                if recursive:
                    dst = os.path.join(dest, os.path.basename(src)) if os.path.isdir(dest) else dest
                    shutil.copytree(src, dst)
                else:
                    _print_err(f"cp: {src}: omitting directory (use -r)")
            else:
                shutil.copy2(src, dest)
        except OSError as e:
            _print_err(f"cp: {src}: {e.strerror}")
    return 0


@builtin('mv')
def cmd_mv(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('mv source [source ...] dest',
            'Move or rename files and directories.',
            examples=['mv old.txt new.txt', 'mv *.log logs/'])
    paths = [a for a in args[1:] if not a.startswith('-')]
    if len(paths) < 2:
        _print_err("mv: missing destination")
        return 1
    *sources, dest = paths
    for src in sources:
        try:
            shutil.move(src, dest)
        except OSError as e:
            _print_err(f"mv: {src}: {e.strerror}")
    return 0


@builtin('cat')
def cmd_cat(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('cat [file ...]',
            'Concatenate and print files. With no arguments, reads from stdin.',
            examples=['cat file.txt', 'cat a.txt b.txt', 'cat > new.txt'])
    files = [a for a in args[1:] if not a.startswith('-')]
    if not files:
        # read stdin
        try:
            for line in sys.stdin:
                print(line, end='')
        except KeyboardInterrupt:
            pass
        return 0
    for f in files:
        try:
            with open(f, encoding='utf-8', errors='replace') as fh:
                print(fh.read(), end='')
        except OSError as e:
            _print_err(f"cat: {f}: {e.strerror}")
    return 0


@builtin('touch')
def cmd_touch(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('touch file [file ...]',
            'Create files if they do not exist, or update their modification time.',
            examples=['touch newfile.txt', 'touch a b c'])
    for f in args[1:]:
        Path(f).touch()
    return 0


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

@builtin('which')
def cmd_which(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('which command',
            'Show the full path of a command found on PATH.',
            examples=['which python', 'which git'])
    if len(args) < 2:
        _print_err("which: usage: which command")
        return 1
    found = shutil.which(args[1])
    if found:
        print(found)
        return 0
    _print_err(f"which: {args[1]}: not found")
    return 1


@builtin('type')
def cmd_type(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('type name',
            'Show how a name would be interpreted (builtin, alias, or external command).',
            examples=['type cd', 'type ll', 'type python'])
    if len(args) < 2:
        _print_err("type: usage: type name")
        return 1
    name = args[1]
    if name in _REGISTRY:
        print(f"{name} is a shell builtin")
    elif name in shell.aliases:
        print(f"{name} is aliased to '{shell.aliases[name]}'")
    else:
        path = shutil.which(name)
        if path:
            print(f"{name} is {path}")
        else:
            _print_err(f"type: {name}: not found")
            return 1
    return 0


# ---------------------------------------------------------------------------
# Shell management
# ---------------------------------------------------------------------------

@builtin('source')
def cmd_source(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('source <file>',
            'Execute commands from a file in the current shell session.',
            examples=['source ~/.xshell/rc.xsh', 'source ./setup.xsh'])
    if len(args) < 2:
        _print_err("source: usage: source <file>")
        return 1
    path = os.path.expanduser(args[1])
    try:
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith('#'):
                    shell.execute_line(line)
        return 0
    except OSError as e:
        _print_err(f"source: {path}: {e.strerror}")
        return 1


@builtin('exit')
def cmd_exit(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('exit [code]',
            'Exit the shell with an optional numeric exit code (default 0).',
            examples=['exit', 'exit 1'])
    code = int(args[1]) if len(args) > 1 and args[1].isdigit() else 0
    shell.running = False
    shell.exit_code = code
    return code


@builtin('quit')
def cmd_quit(shell: 'XShell', args: List[str]) -> int:
    return cmd_exit(shell, args)


# ---------------------------------------------------------------------------
# Theme / plugin management (delegated to shell)
# ---------------------------------------------------------------------------

@builtin('theme')
def cmd_theme(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('theme [list | set <name> | info <name> | <name>]',
            'Manage the active colour theme.',
            [('list',       'Show all available themes (* = active)'),
             ('info <name>','Show full details and colour palette for a theme'),
             ('set <name>', 'Switch to a theme and save the preference'),
             ('<name>',     'Shorthand for  theme set <name>')],
            ['theme list', 'theme gruvbox', 'theme set catppuccin', 'theme info tokyo-night'])

    sub = args[1] if len(args) > 1 else 'list'

    if sub in ('list', 'ls') or len(args) == 1:
        themes = shell.theme_manager.list_themes()
        current = shell.theme_manager.current_name
        print(f'\n  {BOLD}Available themes{RESET}\n')
        for t in themes:
            data = shell.theme_manager.get_theme(t) or {}
            desc = data.get('description', '')
            marker = f'  {GRN}*{RESET}' if t == current else '   '
            name_col = f'{CYAN}{t}{RESET}' if t == current else t
            print(f'  {marker} {name_col:<22} {DIM}{desc}{RESET}')
        print(f'\n  {DIM}Use  theme info <name>  for the full colour palette.{RESET}\n')
        return 0

    if sub == 'info' and len(args) > 2:
        return _cmd_theme_info(shell, args[2])

    if sub == 'set' and len(args) > 2:
        name = args[2]
    else:
        name = sub  # bare  `theme gruvbox`

    if shell.theme_manager.set_theme(name):
        _print_ok(f"Theme set to '{name}'")
        shell.config.set('theme', name)
        shell.config.save()
        shell._apply_terminal_colors()
        return 0
    _print_err(f"theme: '{name}' not found. Run 'theme list' to see available themes.")
    return 1


def _cmd_theme_info(shell: 'XShell', name: str) -> int:
    data = shell.theme_manager.get_theme(name)
    if data is None:
        _print_err(f"theme info: '{name}' not found")
        return 1
    current = shell.theme_manager.current_name
    marker = f'  {GRN}(active){RESET}' if name == current else ''
    print(f'\n  {BOLD}{data.get("name", name)}{RESET}{marker}')
    desc = data.get('description', '')
    if desc:
        print(f'  {desc}')
    colors = data.get('colors', {})
    if colors:
        print(f'\n  {BOLD}Colour palette:{RESET}')
        w = max(len(k) for k in colors)
        for key, val in colors.items():
            print(f'    {CYAN}{key:<{w}}{RESET}  {val}')
    prompt = data.get('prompt', {})
    if prompt:
        fmt = prompt.get('format', '')
        print(f'\n  {BOLD}Prompt format:{RESET}  {fmt}')
    print()


@builtin('plugin')
def cmd_plugin(shell: 'XShell', args: List[str]) -> int:
    if _wants_help(args):
        return _help('plugin <sub-command> [name]',
            'Manage XShell plugins.',
            [('list',            'Show loaded plugins with their descriptions and commands'),
             ('available',       'Show every discoverable plugin (builtin / local / user)'),
             ('info <name>',     'Detailed info: description, version, author, commands'),
             ('load <name>',     'Load a plugin into the current session'),
             ('unload <name>',   'Unload a plugin from the current session'),
             ('reload <name>',   'Unload then re-load a plugin')],
            ['plugin list', 'plugin available', 'plugin info git',
             'plugin load todo', 'plugin reload calc'])

    sub = args[1] if len(args) > 1 else 'list'
    pm = shell.plugin_manager
    if pm is None:
        _print_err("plugin: plugin system disabled")
        return 1

    if sub in ('list', 'ls'):
        loaded = pm.loaded_names()
        if not loaded:
            print("  (no plugins loaded)")
            return 0
        print(f'\n  {BOLD}Loaded plugins{RESET}\n')
        for name in loaded:
            p = pm.get(name)
            desc  = getattr(p, 'description', '')
            ver   = getattr(p, 'version', '')
            ver_s = f'  {DIM}v{ver}{RESET}' if ver else ''
            print(f'  {CYAN}{name}{RESET}{ver_s}')
            if desc:
                print(f'    {desc}')
            cmds = p.commands() if p else {}
            if cmds:
                for cmd_name in sorted(cmds):
                    hint = p.help_for(cmd_name) if hasattr(p, 'help_for') else ''
                    hint = hint.splitlines()[0] if hint else ''
                    hint_s = f'  {DIM}— {hint}{RESET}' if hint else ''
                    print(f'    {GRN}{cmd_name}{RESET}{hint_s}')
            print()
        return 0

    if sub in ('available', 'av', 'all'):
        return _cmd_plugin_available(shell, pm)

    if sub == 'info' and len(args) > 2:
        return _cmd_plugin_info(shell, pm, args[2])

    if sub == 'load' and len(args) > 2:
        ok, msg = pm.load(args[2])
        (print if ok else _print_err)(msg)
        return 0 if ok else 1

    if sub == 'unload' and len(args) > 2:
        ok, msg = pm.unload(args[2])
        (print if ok else _print_err)(msg)
        return 0 if ok else 1

    if sub == 'reload' and len(args) > 2:
        pm.unload(args[2])
        ok, msg = pm.load(args[2])
        (print if ok else _print_err)(msg)
        return 0 if ok else 1

    _print_err(f"plugin: unknown sub-command '{sub}'. Use list/available/info/load/unload/reload.")
    return 1


def _cmd_plugin_info(shell: 'XShell', pm, name: str) -> int:
    """Show full details for one plugin (loaded or not)."""
    p = pm.get(name)

    # If not loaded, try to instantiate temporarily just to read metadata
    if p is None:
        import importlib
        import importlib.util

        from xshell.plugins.manager import _BUILTIN_MAP, _PROJECT_ROOT, _module_exists
        mod = None
        if name in _BUILTIN_MAP and _module_exists(_BUILTIN_MAP[name]):
            try:
                mod = importlib.import_module(_BUILTIN_MAP[name])
            except ImportError:
                pass
        if mod is None:
            for candidate in [
                _PROJECT_ROOT / 'plugins' / f'{name}.py',
                Path.home() / '.xshell' / 'plugins' / f'{name}.py',
            ]:
                if candidate.exists():
                    spec = importlib.util.spec_from_file_location(f'xshell_plugin_{name}', candidate)
                    mod = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(mod)
                    except Exception:
                        mod = None
                    break
        if mod:
            cls = _find_plugin_class(mod)
            if cls:
                try:
                    p = cls()
                    p.on_load(shell)   # register commands so we can inspect them
                    _loaded_temp = True
                except Exception:
                    p = None
    else:
        _loaded_temp = False

    if p is None:
        _print_err(f"plugin info: '{name}' not found")
        return 1

    is_loaded = name in pm.loaded_names()
    status = f'{GRN}loaded{RESET}' if is_loaded else f'{DIM}not loaded{RESET}'
    print(f'\n  {BOLD}{getattr(p, "name", name)}{RESET}  {status}')
    desc = getattr(p, 'description', '')
    if desc:
        print(f'  {desc}')
    ver    = getattr(p, 'version', '')
    author = getattr(p, 'author', '')
    if ver or author:
        meta = '  '.join(filter(None, [f'v{ver}' if ver else '', author]))
        print(f'  {DIM}{meta}{RESET}')

    cmds = p.commands() if p else {}
    if cmds:
        print(f'\n  {BOLD}Commands:{RESET}')
        w = max(len(c) for c in cmds)
        for cmd_name in sorted(cmds):
            hint = p.help_for(cmd_name) if hasattr(p, 'help_for') else ''
            comps = p.completions_for(cmd_name)
            print(f'    {GRN}{cmd_name:<{w}}{RESET}  {hint}')
            if comps:
                comp_str = '  '.join(f'{DIM}{c}{RESET}' for c in comps[:8])
                ellipsis = f'{DIM} …{RESET}' if len(comps) > 8 else ''
                print(f'    {" "*(w+2)}{DIM}completions:{RESET} {comp_str}{ellipsis}')
    print()
    return 0


def _cmd_plugin_available(shell: 'XShell', pm) -> int:
    """Scan all discovery locations and list every plugin available to load."""
    import os as _os
    from pathlib import Path as _Path

    loaded = set(pm.loaded_names())

    # Collect (name, source_label, description) for every discoverable plugin
    entries: dict = {}  # name -> (source, desc)

    # 1. Built-in map ─ only those whose modules actually exist
    from xshell.plugins.manager import _BUILTIN_MAP, _module_exists
    for name, mod_path in sorted(_BUILTIN_MAP.items()):
        if _module_exists(mod_path):
            try:
                mod = __import__(mod_path, fromlist=[''])
                cls = _find_plugin_class(mod)
                desc = getattr(cls, 'description', '') if cls else ''
            except Exception:
                desc = ''
            entries[name] = ('builtin', desc)

    # 2. User plugin directory
    if sys.platform == 'win32':
        user_dir = _Path(_os.environ.get('APPDATA', _Path.home())) / 'XShell' / 'plugins'
    else:
        user_dir = _Path.home() / '.xshell' / 'plugins'
    if user_dir.exists():
        for f in sorted(user_dir.glob('*.py')):
            name = f.stem
            if name not in entries:
                desc = _desc_from_file(f)
                entries[name] = ('user', desc)

    # 3. Project-local plugins/ directory
    from xshell.plugins.manager import _PROJECT_ROOT
    local_dir = _PROJECT_ROOT / 'plugins'
    if local_dir.exists():
        for f in sorted(local_dir.glob('*.py')):
            name = f.stem
            if name.startswith('.') or name == '__init__':
                continue
            if name not in entries:
                desc = _desc_from_file(f)
                entries[name] = ('local', desc)

    if not entries:
        print("  (no plugins found)")
        return 0

    # Determine column widths
    max_name = max(len(n) for n in entries)
    max_src  = max(len(s) for s, _ in entries.values())

    _SRC_COLOR = {'builtin': '\033[36m', 'local': '\033[33m', 'user': '\033[35m'}
    RESET = '\033[0m'
    BOLD  = '\033[1m'
    DIM   = '\033[2m'

    print(f"\n  {BOLD}{'NAME':<{max_name}}  {'SOURCE':<{max_src}}  DESCRIPTION{RESET}")
    print('  ' + '─' * (max_name + max_src + 36))
    for name, (src, desc) in sorted(entries.items()):
        loaded_marker = '\033[32m ●\033[0m' if name in loaded else DIM + ' ○' + RESET
        color = _SRC_COLOR.get(src, '')
        print(f"  {name:<{max_name}}{loaded_marker} "
              f" {color}{src:<{max_src}}{RESET}  {desc}")
    print()
    print(f"  {DIM}● loaded  ○ available  "
          f"\033[36mbuiltin\033[0m{DIM} / "
          f"\033[33mlocal\033[0m{DIM} / "
          f"\033[35muser{RESET}")
    print()
    return 0


def _find_plugin_class(mod):
    """Return the first XShellPlugin subclass found in a module."""
    import inspect
    try:
        from xshell.plugins.base import XShellPlugin
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, XShellPlugin) and obj is not XShellPlugin:
                return obj
    except Exception:
        pass
    return None


def _desc_from_file(path: 'Path') -> str:
    """Extract the description class attribute from a plugin file without importing it."""
    try:
        src = path.read_text(encoding='utf-8', errors='replace')
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith('description') and '=' in stripped:
                _, _, val = stripped.partition('=')
                return val.strip().strip("'\"")
    except OSError:
        pass
    return ''


# ---------------------------------------------------------------------------
# Job control
# ---------------------------------------------------------------------------

@builtin('jobs')
def cmd_jobs(shell: 'XShell', args: List[str]) -> int:
    jobs = getattr(shell, '_background_jobs', {})
    if not jobs:
        print("  (no background jobs)")
        return 0
    print(f"\033[1m{'[ID]':>4}  {'PID':>7}  Status     Command\033[0m")
    for job_id, entry in sorted(jobs.items()):
        proc = entry['proc']
        rc = proc.poll()
        status = '\033[32mrunning\033[0m' if rc is None else f'\033[31mexited({rc})\033[0m'
        print(f"  [{job_id}]  {proc.pid:>7}  {status}  {entry['cmd']}")
    return 0


@builtin('fg')
def cmd_fg(shell: 'XShell', args: List[str]) -> int:
    jobs = getattr(shell, '_background_jobs', {})
    if not jobs:
        print("fg: no background jobs", file=sys.stderr)
        return 1
    try:
        job_id = int(args[1]) if len(args) > 1 else max(jobs.keys())
    except (ValueError, TypeError):
        _print_err(f"fg: {args[1]}: invalid job id")
        return 1
    if job_id not in jobs:
        _print_err(f"fg: [{job_id}]: no such job")
        return 1
    proc = jobs[job_id]['proc']
    try:
        proc.wait()
        return proc.returncode
    except KeyboardInterrupt:
        return 130
    finally:
        jobs.pop(job_id, None)


@builtin('bg')
def cmd_bg(shell: 'XShell', args: List[str]) -> int:
    jobs = getattr(shell, '_background_jobs', {})
    if not jobs:
        print("bg: no background jobs", file=sys.stderr)
        return 1
    # bg just lists stopped jobs in this implementation (no SIGSTOP support cross-platform)
    return cmd_jobs(shell, args)


@builtin('kill')
def cmd_kill(shell: 'XShell', args: List[str]) -> int:
    import signal as _signal
    if len(args) < 2:
        _print_err("kill: usage: kill [-SIGNAL] <pid|%jobid>")
        return 1
    sig = _signal.SIGTERM
    targets = args[1:]
    # Check for signal flag
    if targets[0].startswith('-'):
        sig_name = targets[0][1:].upper()
        try:
            sig = int(sig_name)
        except ValueError:
            sig_map = {'TERM': 15, 'KILL': 9, 'HUP': 1, 'INT': 2, 'QUIT': 3}
            sig = sig_map.get(sig_name, 15)
        targets = targets[1:]

    for target in targets:
        if target.startswith('%'):
            job_id = int(target[1:])
            jobs = getattr(shell, '_background_jobs', {})
            if job_id in jobs:
                try:
                    os.kill(jobs[job_id]['proc'].pid, sig)
                    _print_ok(f"Killed job [{job_id}]")
                except OSError as e:
                    _print_err(f"kill: {e}")
            else:
                _print_err(f"kill: [{job_id}]: no such job")
        else:
            try:
                pid = int(target)
                os.kill(pid, sig)
                _print_ok(f"Sent signal {sig} to PID {pid}")
            except ValueError:
                _print_err(f"kill: {target}: invalid PID")
            except OSError as e:
                _print_err(f"kill: {e}")
    return 0


# ---------------------------------------------------------------------------
# Update & config
# ---------------------------------------------------------------------------

@builtin('update')
def cmd_update(shell: 'XShell', args: List[str]) -> int:
    from xshell import __version__
    from xshell.core.updater import (
        check_latest_version,
        is_newer,
        upgrade_git,
        upgrade_pip,
    )

    sub = args[1] if len(args) > 1 else 'check'

    if sub == 'check':
        print("Checking for updates...", end='', flush=True)
        latest = check_latest_version()
        if latest is None:
            print("\r\033[33mCould not reach PyPI. Check your connection.\033[0m")
            return 1
        if is_newer(latest, __version__):
            print(f"\r\033[33mUpdate available: {__version__} → {latest}\033[0m")
            print("Run 'update pip' to upgrade via pip.")
        else:
            print(f"\r\033[32mXShell is up to date ({__version__})\033[0m")
        return 0

    if sub == 'pip':
        print("Upgrading via pip...")
        ok, out = upgrade_pip()
        if ok:
            _print_ok("Upgrade successful! Restart XShell to apply.")
        else:
            _print_err(f"Upgrade failed:\n{out}")
        return 0 if ok else 1

    if sub == 'git':
        path = args[2] if len(args) > 2 else '.'
        print("Pulling latest from git...")
        ok, out = upgrade_git(path)
        if ok:
            _print_ok(f"Updated:\n{out}")
        else:
            _print_err(f"Git pull failed:\n{out}")
        return 0 if ok else 1

    _print_err(f"update: unknown sub-command '{sub}'. Use: check, pip, git")
    return 1


@builtin('config')
def cmd_config(shell: 'XShell', args: List[str]) -> int:
    sub = args[1] if len(args) > 1 else 'list'

    if sub in ('list', 'ls', 'show'):
        import json
        print("\033[1mXShell configuration:\033[0m")
        for k, v in sorted(vars(shell.config).get('_data', {}).items()):
            print(f"  {k:<30} {json.dumps(v)}")
        return 0

    if sub == 'get' and len(args) > 2:
        val = shell.config.get(args[2])
        if val is None:
            _print_err(f"config: key '{args[2]}' not set")
            return 1
        import json
        print(json.dumps(val))
        return 0

    if sub == 'set' and len(args) > 3:
        import json
        key = args[2]
        try:
            value = json.loads(args[3])
        except json.JSONDecodeError:
            value = args[3]
        shell.config.set(key, value)
        shell.config.save()
        _print_ok(f"config.{key} = {json.dumps(value)}")
        return 0

    if sub == 'reset' and len(args) > 2:
        shell.config._data.pop(args[2], None)
        shell.config.save()
        _print_ok(f"config.{args[2]} reset to default")
        return 0

    if sub == 'export':
        import json
        path = args[2] if len(args) > 2 else 'xshell-config-export.json'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(shell.config._data, fh, indent=2)
        _print_ok(f"Config exported to '{path}'")
        return 0

    if sub == 'import':
        import json
        if len(args) < 3:
            _print_err("config import: path required")
            return 1
        try:
            with open(args[2], encoding='utf-8') as fh:
                data = json.load(fh)
            shell.config._data.update(data)
            shell.config.save()
            _print_ok(f"Config imported from '{args[2]}'")
            return 0
        except (OSError, json.JSONDecodeError) as e:
            _print_err(f"config import: {e}")
            return 1

    if sub == 'path':
        print(shell.config._path if hasattr(shell.config, '_path') else '(unknown)')
        return 0

    _print_err(f"config: unknown sub-command '{sub}'. Use: list, get, set, reset, export, import, path")
    return 1


# ---------------------------------------------------------------------------
# Script runner
# ---------------------------------------------------------------------------

@builtin('run')
def cmd_run(shell: 'XShell', args: List[str]) -> int:
    if len(args) < 2:
        _print_err("run: usage: run <script.xsh> [args...]")
        return 1
    path = os.path.expanduser(args[1])
    if not os.path.exists(path):
        _print_err(f"run: '{path}': not found")
        return 1
    from xshell.core.scripting import run_script
    return run_script(shell, path, args[2:])


# ---------------------------------------------------------------------------
# Plugin marketplace
# ---------------------------------------------------------------------------

@builtin('pkg')
def cmd_pkg(shell: 'XShell', args: List[str]) -> int:
    from xshell.plugins.registry import (
        fetch_registry,
        install_plugin,
        list_installed,
        search_plugins,
        uninstall_plugin,
    )
    sub = args[1] if len(args) > 1 else 'help'

    if sub in ('search', 'find'):
        query = ' '.join(args[2:])
        print("Fetching plugin registry...")
        plugins = fetch_registry()
        if not plugins:
            print("  (registry unavailable — check your connection)")
            return 1
        results = search_plugins(query, plugins) if query else plugins
        if not results:
            print(f"  No plugins matching '{query}'")
            return 0
        print(f"\033[1m{'Name':<20} {'Version':<10} Description\033[0m")
        for p in results:
            print(f"  {p.get('name',''):<20} {p.get('version',''):<10} {p.get('description','')}")
        return 0

    if sub == 'install':
        if len(args) < 3:
            _print_err("pkg install: plugin name required")
            return 1
        plugins = fetch_registry()
        ok, msg = install_plugin(args[2], plugins)
        (print if ok else _print_err)(msg)
        return 0 if ok else 1

    if sub == 'remove':
        if len(args) < 3:
            _print_err("pkg remove: plugin name required")
            return 1
        ok, msg = uninstall_plugin(args[2])
        (print if ok else _print_err)(msg)
        return 0 if ok else 1

    if sub == 'list':
        installed = list_installed()
        if not installed:
            print("No user-installed plugins.")
        for name in installed:
            print(f"  {name}")
        return 0

    print("Usage: pkg [search <query>|install <name>|remove <name>|list]")
    return 0


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

@builtin('help')
def cmd_help(shell: 'XShell', args: List[str]) -> int:
    if len(args) > 1:
        name = args[1]
        fn = get_builtin(name)
        if fn and fn.__doc__:
            print(fn.__doc__)
        elif fn:
            print(f"{name}: built-in command (no extended help)")
        else:
            _print_err(f"help: {name}: not a shell builtin")
        return 0

    print("\033[1mXShell built-in commands\033[0m")
    print()
    cols = list_builtins()
    width = max(len(c) for c in cols) + 2
    per_row = max(1, 72 // width)
    for i in range(0, len(cols), per_row):
        print('  ' + ''.join(c.ljust(width) for c in cols[i:i + per_row]))
    print()
    print("Type 'help <command>' for details on a specific command.")
    return 0

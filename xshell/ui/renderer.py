"""
XShell output renderer.
Wraps rich for tables, panels, syntax highlighting, and progress bars.
Gracefully falls back to plain print() if rich is unavailable.
"""

import sys
from typing import Any, Dict, List, Optional, Sequence

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import track
    from rich import box
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

_console = None

def _get_console():
    global _console
    if _console is None and _HAS_RICH:
        _console = Console()
    return _console


def print_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    title: Optional[str] = None,
    style: str = 'cyan',
) -> None:
    if not _HAS_RICH:
        if title:
            print(f"\n{title}")
        print('  ' + '  '.join(str(h) for h in headers))
        print('  ' + '  '.join('-' * len(str(h)) for h in headers))
        for row in rows:
            print('  ' + '  '.join(str(c) for c in row))
        return

    c = _get_console()
    t = Table(title=title, box=box.ROUNDED, header_style=f"bold {style}")
    for h in headers:
        t.add_column(str(h))
    for row in rows:
        t.add_row(*[str(c) for c in row])
    c.print(t)


def print_panel(content: str, title: str = '', style: str = 'blue') -> None:
    if not _HAS_RICH:
        if title:
            print(f"--- {title} ---")
        print(content)
        return
    _get_console().print(Panel(content, title=title, border_style=style))


def print_code(code: str, language: str = 'python', theme: str = 'monokai') -> None:
    if not _HAS_RICH:
        print(code)
        return
    _get_console().print(Syntax(code, language, theme=theme))


def _is_unicode_safe() -> bool:
    try:
        '✓✗⚠ℹ'.encode(sys.stdout.encoding or 'ascii')
        return True
    except (UnicodeEncodeError, LookupError):
        return False


_UNICODE = _is_unicode_safe()
_OK  = '✓' if _UNICODE else '[OK]'
_ERR = '✗' if _UNICODE else '[!]'
_INF = 'ℹ' if _UNICODE else '[i]'
_WRN = '⚠'  if _UNICODE else '[?]'


def print_error(msg: str) -> None:
    if _HAS_RICH:
        _get_console().print(f"[bold red]{_ERR} {msg}[/bold red]")
    else:
        print(f"\033[31m{_ERR} {msg}\033[0m", file=sys.stderr)


def print_success(msg: str) -> None:
    if _HAS_RICH:
        _get_console().print(f"[bold green]{_OK} {msg}[/bold green]")
    else:
        print(f"\033[32m{_OK} {msg}\033[0m")


def print_info(msg: str) -> None:
    if _HAS_RICH:
        _get_console().print(f"[bold blue]{_INF} {msg}[/bold blue]")
    else:
        print(f"\033[34m{_INF} {msg}\033[0m")


def print_warning(msg: str) -> None:
    if _HAS_RICH:
        _get_console().print(f"[bold yellow]{_WRN} {msg}[/bold yellow]")
    else:
        print(f"\033[33m{_WRN} {msg}\033[0m")

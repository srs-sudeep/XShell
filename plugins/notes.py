"""
XShell Notes plugin — drop-in example plugin.

Quick plain-text notes stored in ~/.xshell/notes/<name>.txt

Commands:
  note new <name>          — create/open a note (opens $EDITOR)
  note write <name> <text> — append a line without opening editor
  note list                — list all notes
  note show <name>         — print a note
  note grep <pattern>      — search across all notes
  note rm <name>           — delete a note

Install:  plugin load notes
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell


def _notes_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'XShell' / 'notes'
    else:
        base = Path.home() / '.xshell' / 'notes'
    base.mkdir(parents=True, exist_ok=True)
    return base


def _resolve(name: str) -> Path:
    if not name.endswith('.txt'):
        name += '.txt'
    return _notes_dir() / name


class NotesPlugin(XShellPlugin):
    name        = 'notes'
    description = 'Quick plain-text notes — note new/write/list/show/grep/rm'
    version     = '1.0.0'
    author      = 'XShell Examples'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command(
            'note', self._note,
            ['new', 'write', 'list', 'show', 'grep', 'rm', 'remove'],
        )

    def _note(self, shell: 'XShell', args: List[str]) -> int:
        sub = args[1] if len(args) > 1 else 'list'

        if sub in ('list', 'ls'):
            return self._list()
        if sub == 'new' and len(args) > 2:
            return self._new(args[2])
        if sub == 'write' and len(args) > 3:
            return self._write(args[2], ' '.join(args[3:]))
        if sub == 'show' and len(args) > 2:
            return self._show(args[2])
        if sub == 'grep' and len(args) > 2:
            return self._grep(' '.join(args[2:]))
        if sub in ('rm', 'remove') and len(args) > 2:
            return self._rm(args[2])

        self._usage()
        return 0

    # ── Sub-commands ──────────────────────────────────────────────────────

    def _list(self) -> int:
        notes = sorted(_notes_dir().glob('*.txt'))
        if not notes:
            print('  (no notes yet — use "note new <name>")')
            return 0
        for n in notes:
            lines = n.read_text(encoding='utf-8', errors='replace').splitlines()
            preview = lines[0][:60] if lines else ''
            size_kb = n.stat().st_size / 1024
            print(f"  \033[36m{n.stem:20s}\033[0m  {size_kb:5.1f} KB  {preview}")
        return 0

    def _new(self, name: str) -> int:
        path = _resolve(name)
        editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or (
            'notepad' if sys.platform == 'win32' else 'nano'
        )
        try:
            subprocess.run([editor, str(path)])
        except FileNotFoundError:
            print(f'note: editor {editor!r} not found. Use "note write {name} <text>" instead.')
            return 1
        return 0

    def _write(self, name: str, text: str) -> int:
        path = _resolve(name)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
        print(f'  \033[32m+\033[0m appended to {path.stem}')
        return 0

    def _show(self, name: str) -> int:
        path = _resolve(name)
        if not path.exists():
            print(f'note: {name!r} not found', file=sys.stderr)
            return 1
        print(f'\033[1m── {path.stem} ──\033[0m')
        print(path.read_text(encoding='utf-8', errors='replace'))
        return 0

    def _grep(self, pattern: str) -> int:
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            print(f'note grep: invalid pattern: {e}', file=sys.stderr)
            return 1
        found = False
        for path in sorted(_notes_dir().glob('*.txt')):
            for lineno, line in enumerate(
                path.read_text(encoding='utf-8', errors='replace').splitlines(), 1
            ):
                if rx.search(line):
                    highlighted = rx.sub(
                        lambda m: f'\033[93m{m.group()}\033[0m', line
                    )
                    print(f'  \033[36m{path.stem}\033[0m:{lineno}: {highlighted}')
                    found = True
        if not found:
            print(f'  (no matches for {pattern!r})')
        return 0

    def _rm(self, name: str) -> int:
        path = _resolve(name)
        if not path.exists():
            print(f'note: {name!r} not found', file=sys.stderr)
            return 1
        path.unlink()
        print(f'  \033[31m-\033[0m deleted {path.stem}')
        return 0

    def _usage(self) -> None:
        print('Usage:')
        print('  note list                — list all notes')
        print('  note new <name>          — create/edit note in $EDITOR')
        print('  note write <name> <text> — append text without editor')
        print('  note show <name>         — print note')
        print('  note grep <pattern>      — search all notes')
        print('  note rm <name>           — delete note')

"""
XShell Todo plugin — drop-in example plugin.

Manages a simple todo list stored in ~/.xshell/todo.json.

Commands:
  todo [list]         — list todos (default)
  todo add <text>     — add a new item
  todo done <id>      — mark item as done
  todo undone <id>    — mark item as not done
  todo remove <id>    — delete item
  todo clear          — delete all completed items
  todo reset          — delete everything

Install:  plugin load todo
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell


def _store_path() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'XShell'
    else:
        base = Path.home() / '.xshell'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'todo.json'


def _load(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save(path: Path, items: list) -> None:
    path.write_text(json.dumps(items, indent=2), encoding='utf-8')


class TodoPlugin(XShellPlugin):
    name        = 'todo'
    description = 'Simple todo list — todo add/done/remove/list'
    version     = '1.0.0'
    author      = 'XShell Examples'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self._path = _store_path()
        self.register_command(
            'todo', self._todo,
            ['add', 'done', 'undone', 'remove', 'rm', 'clear', 'reset', 'list'],
        )

    def _todo(self, shell: 'XShell', args: List[str]) -> int:
        sub = args[1] if len(args) > 1 else 'list'

        if sub in ('list', 'ls') or (len(args) == 1):
            return self._list()
        if sub == 'add' and len(args) > 2:
            return self._add(' '.join(args[2:]))
        if sub == 'done' and len(args) > 2:
            return self._set_done(args[2], True)
        if sub in ('undone', 'undo') and len(args) > 2:
            return self._set_done(args[2], False)
        if sub in ('remove', 'rm') and len(args) > 2:
            return self._remove(args[2])
        if sub == 'clear':
            return self._clear_done()
        if sub == 'reset':
            return self._reset()

        self._print_usage()
        return 0

    # ── Sub-commands ──────────────────────────────────────────────────────

    def _list(self) -> int:
        items = _load(self._path)
        if not items:
            print('  (no todos)')
            return 0
        for item in items:
            done  = item.get('done', False)
            check = '\033[32m[x]\033[0m' if done else '\033[90m[ ]\033[0m'
            text  = f"\033[90m{item['text']}\033[0m" if done else item['text']
            added = item.get('added', '')[:10]
            print(f"  {check} {item['id']:>3}.  {text}  \033[90m{added}\033[0m")
        total  = len(items)
        done_n = sum(1 for i in items if i.get('done'))
        print(f"\n  {done_n}/{total} done")
        return 0

    def _add(self, text: str) -> int:
        items = _load(self._path)
        new_id = max((i['id'] for i in items), default=0) + 1
        items.append({
            'id':    new_id,
            'text':  text,
            'done':  False,
            'added': datetime.now().isoformat(timespec='seconds'),
        })
        _save(self._path, items)
        print(f"  \033[32m+\033[0m [{new_id}] {text}")
        return 0

    def _set_done(self, id_str: str, done: bool) -> int:
        try:
            tid = int(id_str)
        except ValueError:
            print(f'todo: invalid id {id_str!r}', file=sys.stderr)
            return 1
        items = _load(self._path)
        for item in items:
            if item['id'] == tid:
                item['done'] = done
                _save(self._path, items)
                marker = '\033[32m[x]\033[0m' if done else '[ ]'
                print(f"  {marker} [{tid}] {item['text']}")
                return 0
        print(f'todo: item {tid} not found', file=sys.stderr)
        return 1

    def _remove(self, id_str: str) -> int:
        try:
            tid = int(id_str)
        except ValueError:
            print(f'todo: invalid id {id_str!r}', file=sys.stderr)
            return 1
        items = _load(self._path)
        before = len(items)
        items = [i for i in items if i['id'] != tid]
        if len(items) == before:
            print(f'todo: item {tid} not found', file=sys.stderr)
            return 1
        _save(self._path, items)
        print(f'  \033[31m-\033[0m removed [{tid}]')
        return 0

    def _clear_done(self) -> int:
        items = _load(self._path)
        kept = [i for i in items if not i.get('done')]
        removed = len(items) - len(kept)
        _save(self._path, kept)
        print(f'  Removed {removed} completed item(s)')
        return 0

    def _reset(self) -> int:
        _save(self._path, [])
        print('  Todo list cleared')
        return 0

    def _print_usage(self) -> None:
        print('Usage:')
        print('  todo [list]       — show all todos')
        print('  todo add <text>   — add a todo')
        print('  todo done <id>    — mark as done')
        print('  todo undone <id>  — mark as not done')
        print('  todo remove <id>  — delete item')
        print('  todo clear        — remove completed items')
        print('  todo reset        — remove everything')

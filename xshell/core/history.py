"""
Persistent command history for XShell.
Stores history in ~/.xshell/history (or %APPDATA%/XShell/history on Windows).
"""

import os
import sys
from pathlib import Path
from typing import List, Optional


def _get_history_path() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'XShell'
    else:
        base = Path.home() / '.xshell'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'history'


class HistoryManager:
    def __init__(self, max_size: int = 2000):
        self.max_size = max_size
        self.path = _get_history_path()
        self._entries: List[str] = []
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, line: str) -> None:
        """Add a command to history, deduplicating consecutive identical entries."""
        line = line.strip()
        if not line:
            return
        if self._entries and self._entries[-1] == line:
            return
        self._entries.append(line)
        if len(self._entries) > self.max_size:
            self._entries = self._entries[-self.max_size:]
        self._save()

    def get_all(self) -> List[str]:
        return list(self._entries)

    def clear(self) -> None:
        self._entries = []
        self._save()

    def search(self, query: str) -> List[str]:
        """Return all entries containing query (case-insensitive), most recent first."""
        q = query.lower()
        return [e for e in reversed(self._entries) if q in e.lower()]

    def last(self, n: int = 10) -> List[str]:
        return self._entries[-n:]

    def __len__(self) -> int:
        return len(self._entries)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self.path.exists():
            try:
                text = self.path.read_text(encoding='utf-8', errors='replace')
                self._entries = [l for l in text.splitlines() if l.strip()]
            except OSError:
                self._entries = []

    def _save(self) -> None:
        try:
            self.path.write_text('\n'.join(self._entries) + '\n', encoding='utf-8')
        except OSError:
            pass

"""
Autocorrect engine for XShell.
Uses Levenshtein distance to suggest the closest known command when a typo is detected.
"""

import os
import sys
from typing import List, Optional, Tuple


def levenshtein(a: str, b: str) -> int:
    """Compute edit distance between two strings."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[len(b)]


def _get_path_commands() -> List[str]:
    """Collect all executable names from PATH."""
    commands = []
    path_dirs = os.environ.get('PATH', '').split(os.pathsep)
    exts = {'.exe', '.cmd', '.bat'} if sys.platform == 'win32' else set()

    for d in path_dirs:
        try:
            for entry in os.scandir(d):
                if entry.is_file():
                    name = entry.name
                    if sys.platform == 'win32':
                        root, ext = os.path.splitext(name)
                        if ext.lower() in exts:
                            commands.append(root.lower())
                    else:
                        if os.access(entry.path, os.X_OK):
                            commands.append(name)
        except (OSError, PermissionError):
            continue
    return commands


class AutoCorrect:
    # Only suggest if the edit distance is within this threshold
    MAX_DISTANCE = 2

    def __init__(self):
        self._path_commands: Optional[List[str]] = None

    def _known_commands(self, builtins: List[str], plugin_cmds: List[str]) -> List[str]:
        if self._path_commands is None:
            self._path_commands = _get_path_commands()
        return list(set(builtins + plugin_cmds + self._path_commands))

    def suggest(
        self,
        typed: str,
        builtins: List[str],
        plugin_cmds: List[str],
    ) -> Optional[str]:
        """Return the best suggestion for a mistyped command, or None."""
        if not typed:
            return None
        candidates = self._known_commands(builtins, plugin_cmds)
        best: Optional[Tuple[int, str]] = None
        typed_l = typed.lower()

        for cmd in candidates:
            d = levenshtein(typed_l, cmd.lower())
            if d <= self.MAX_DISTANCE:
                if best is None or d < best[0]:
                    best = (d, cmd)

        return best[1] if best else None

    def invalidate_cache(self) -> None:
        """Force a PATH rescan on the next call."""
        self._path_commands = None

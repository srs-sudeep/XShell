"""
XShell configuration manager.
Config stored in:
  - Windows: %APPDATA%/XShell/config.json
  - macOS/Linux: ~/.xshell/config.json
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

_DEFAULTS = {
    "theme": "default",
    "show_banner": True,
    "plugins": ["git", "sysinfo", "calc"],
    "history_size": 2000,
    "autocorrect": True,
    "complete_while_typing": True,
    "prompt_format": "{default}",
    "rprompt": True,
    "vi_mode": False,
    "aliases": {
        "ll": "ls -l",
        "la": "ls -a",
        "lla": "ls -la",
        "..": "cd ..",
        "...": "cd ../..",
        "....": "cd ../../..",
        "g": "git",
        "py": "python",
        "py3": "python3",
    },
}


def _config_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'XShell'
    else:
        base = Path.home() / '.xshell'
    base.mkdir(parents=True, exist_ok=True)
    return base


class ConfigManager:
    def __init__(self, path: Optional[str] = None):
        self._path = Path(path) if path else _config_dir() / 'config.json'
        self._data: dict = dict(_DEFAULTS)
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def all(self) -> dict:
        return dict(self._data)

    def save(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2),
                encoding='utf-8',
            )
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path.exists():
            try:
                on_disk = json.loads(self._path.read_text(encoding='utf-8'))
                self._data.update(on_disk)
            except (json.JSONDecodeError, OSError):
                pass
        else:
            self.save()  # write defaults on first run

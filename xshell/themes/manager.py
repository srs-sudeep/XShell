"""
XShell theme manager.
Themes live as JSON files in:
  - Built-in: xshell/themes/builtin/
  - User: ~/.xshell/themes/  (or %APPDATA%/XShell/themes/ on Windows)
"""

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from ..config.manager import ConfigManager

_BUILTIN_DIR = Path(__file__).parent / 'builtin'
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PROJECT_THEMES_DIR = _PROJECT_ROOT / 'themes'


def _user_themes_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'XShell' / 'themes'
    else:
        base = Path.home() / '.xshell' / 'themes'
    base.mkdir(parents=True, exist_ok=True)
    return base


class ThemeManager:
    def __init__(self, config: 'ConfigManager'):
        self.config = config
        self._themes: Dict[str, dict] = {}
        self._scan()
        initial = config.get('theme', 'default')
        if not self.set_theme(initial):
            self.set_theme('default')

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_theme(self) -> dict:
        return self._current

    @property
    def current_name(self) -> str:
        return self._current_name

    def list_themes(self) -> List[str]:
        return sorted(self._themes.keys())

    def set_theme(self, name: str) -> bool:
        if name in self._themes:
            self._current = self._themes[name]
            self._current_name = name
            return True
        return False

    def get_theme(self, name: str) -> Optional[dict]:
        return self._themes.get(name)

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def _scan(self) -> None:
        for source in (_BUILTIN_DIR, _PROJECT_THEMES_DIR, _user_themes_dir()):
            if source.exists():
                for f in source.glob('*.json'):
                    try:
                        data = json.loads(f.read_text(encoding='utf-8'))
                        key = f.stem.lower()
                        self._themes[key] = data
                    except (json.JSONDecodeError, OSError):
                        pass

        if not self._themes:
            self._themes['default'] = _FALLBACK_THEME

        self._current = self._themes.get('default', _FALLBACK_THEME)
        self._current_name = 'default'


_FALLBACK_THEME = {
    "name": "Default",
    "colors": {
        "background": "#1e1e1e",
        "foreground": "#f0f0f0",
        "prompt_user": "bright_cyan",
        "prompt_host": "bright_green",
        "prompt_cwd": "bright_yellow",
        "prompt_git": "bright_magenta",
        "error": "bright_red",
        "success": "bright_green",
        "info": "bright_blue",
        "warning": "bright_yellow",
    },
    "prompt": {"format": "{default}"},
}

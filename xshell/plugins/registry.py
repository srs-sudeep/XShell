"""
XShell plugin registry / marketplace.
Fetches a JSON index from a remote URL and allows search + install.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

_REGISTRY_URL = (
    "https://raw.githubusercontent.com/srs-sudeep/XShell/main/plugins/registry.json"
)

_LOCAL_CACHE: Optional[Path] = None


def _cache_path() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', '~')).expanduser()
    else:
        base = Path.home()
    return base / '.xshell' / 'plugin_registry_cache.json'


def _user_plugin_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', '~')).expanduser()
    else:
        base = Path.home()
    p = base / '.xshell' / 'plugins'
    p.mkdir(parents=True, exist_ok=True)
    return p


def fetch_registry(timeout: int = 8) -> List[Dict[str, Any]]:
    """Download registry index (or return cached copy)."""
    cache = _cache_path()
    try:
        req = urllib.request.Request(
            _REGISTRY_URL, headers={"User-Agent": "xshell/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return data.get('plugins', [])
    except Exception:
        if cache.exists():
            try:
                data = json.loads(cache.read_text(encoding='utf-8'))
                return data.get('plugins', [])
            except Exception:
                pass
    return []


def search_plugins(query: str, plugins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = query.lower()
    return [
        p for p in plugins
        if q in p.get('name', '').lower()
        or q in p.get('description', '').lower()
        or q in ' '.join(p.get('tags', [])).lower()
    ]


def install_plugin(name: str, plugins: List[Dict[str, Any]]) -> tuple[bool, str]:
    """Download plugin file into user plugin directory."""
    matches = [p for p in plugins if p.get('name') == name]
    if not matches:
        return False, f"Plugin '{name}' not found in registry."
    plugin_info = matches[0]
    url = plugin_info.get('url', '')
    if not url:
        return False, f"Plugin '{name}' has no download URL."

    dest = _user_plugin_dir() / f"{name}.py"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "xshell/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return True, f"Plugin '{name}' installed to {dest}"
    except Exception as e:
        return False, f"Failed to install '{name}': {e}"


def uninstall_plugin(name: str) -> tuple[bool, str]:
    dest = _user_plugin_dir() / f"{name}.py"
    if dest.exists():
        dest.unlink()
        return True, f"Plugin '{name}' removed."
    return False, f"Plugin '{name}' not found in user plugins directory."


def list_installed() -> List[str]:
    plugin_dir = _user_plugin_dir()
    return sorted(p.stem for p in plugin_dir.glob('*.py'))

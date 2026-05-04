"""
XShell self-update / version check utility.
Checks PyPI for newer versions and optionally upgrades via pip.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Optional, Tuple

from xshell import __version__

_PYPI_URL = "https://pypi.org/pypi/xshell/json"
_GIT_REMOTE = "https://github.com/srs-sudeep/XShell"


def _parse_version(v: str) -> Tuple[int, ...]:
    try:
        return tuple(int(x) for x in v.strip().lstrip('v').split('.')[:3])
    except Exception:
        return (0,)


def check_latest_version(timeout: int = 5) -> Optional[str]:
    """Return the latest PyPI version string, or None on error."""
    try:
        req = urllib.request.Request(
            _PYPI_URL, headers={"User-Agent": f"xshell/{__version__}"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["info"]["version"]
    except Exception:
        return None


def is_newer(remote: str, current: str = __version__) -> bool:
    return _parse_version(remote) > _parse_version(current)


def upgrade_pip() -> Tuple[bool, str]:
    """Run pip install --upgrade xshell, return (success, output)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "xshell"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)


def upgrade_git(repo_path: str = ".") -> Tuple[bool, str]:
    """Run git pull in repo_path, return (success, output)."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "pull"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, str(e)

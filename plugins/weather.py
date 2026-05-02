"""
XShell Weather plugin — drop-in example plugin.

Fetches weather from wttr.in (no API key required).

Commands:
  weather [city]       — current conditions + 3-day forecast (default: auto-detect)
  weather now [city]   — one-line current conditions only
  weather moon         — moon phase

Install:  plugin load weather
Requires: Python 3 stdlib only (urllib)
"""

import sys
import urllib.request
import urllib.error
import urllib.parse
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell

_BASE = 'https://wttr.in/'


def _fetch(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except urllib.error.URLError as e:
        return f'\033[31mError: {e.reason}\033[0m'
    except Exception as e:
        return f'\033[31mError: {e}\033[0m'


class WeatherPlugin(XShellPlugin):
    name        = 'weather'
    description = 'Weather via wttr.in — weather [city], weather now [city]'
    version     = '1.0.0'
    author      = 'XShell Examples'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command('weather', self._weather, ['now', 'moon'])

    def _weather(self, shell: 'XShell', args: List[str]) -> int:
        sub = args[1] if len(args) > 1 else ''

        if sub == 'moon':
            print(_fetch(f'{_BASE}moon?T'))
            return 0

        if sub == 'now':
            city = '+'.join(args[2:]) if len(args) > 2 else ''
            loc  = urllib.parse.quote(city) if city else ''
            # ?format=4 → one line: "City: icon temp"
            print(_fetch(f'{_BASE}{loc}?format=4&T'))
            return 0

        # Full forecast
        city = '+'.join(args[1:]) if len(args) > 1 else ''
        loc  = urllib.parse.quote(city) if city else ''
        # ?T = no colours (ANSI is fine); omit ?T to get colours
        print(_fetch(f'{_BASE}{loc}?T'))
        return 0

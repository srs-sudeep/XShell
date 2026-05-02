"""
XShell HTTP plugin — drop-in example plugin.

Lightweight HTTP client for quick API calls and file downloads.

Commands:
  get  <url> [headers...]   — GET request, pretty-print response
  post <url> <body> [h...]  — POST with body (JSON auto-detected)
  head <url>                — HEAD request, show response headers
  download <url> [file]     — download URL to a file

Header syntax: Key:Value  (e.g. Authorization:Bearer TOKEN)

Install:  plugin load http
Requires: Python 3 stdlib only (urllib, json)
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell

_DEFAULT_HEADERS = {
    'User-Agent': 'XShell-HTTP/1.0',
    'Accept':     '*/*',
}


def _parse_headers(raw: List[str]) -> dict:
    """Parse Key:Value strings into a dict."""
    h = {}
    for item in raw:
        if ':' in item:
            k, _, v = item.partition(':')
            h[k.strip()] = v.strip()
    return h


def _pretty(body: str, content_type: str) -> str:
    if 'json' in content_type:
        try:
            return json.dumps(json.loads(body), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass
    return body


class HttpPlugin(XShellPlugin):
    name        = 'http'
    description = 'HTTP client — get, post, head, download'
    version     = '1.0.0'
    author      = 'XShell Examples'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command('get',      self._get)
        self.register_command('post',     self._post)
        self.register_command('head',     self._head)
        self.register_command('download', self._download)

    # ── Commands ──────────────────────────────────────────────────────────

    def _get(self, shell: 'XShell', args: List[str]) -> int:
        """GET <url> [Key:Value ...]"""
        if len(args) < 2:
            print('Usage: get <url> [Key:Value ...]', file=sys.stderr)
            return 1
        url     = args[1]
        headers = {**_DEFAULT_HEADERS, **_parse_headers(args[2:])}
        return self._request('GET', url, headers=headers)

    def _post(self, shell: 'XShell', args: List[str]) -> int:
        """POST <url> <body> [Key:Value ...]"""
        if len(args) < 3:
            print('Usage: post <url> <body> [Key:Value ...]', file=sys.stderr)
            return 1
        url  = args[1]
        body = args[2]
        headers = dict(_DEFAULT_HEADERS)
        headers.update(_parse_headers(args[3:]))
        # Auto-detect JSON body
        try:
            json.loads(body)
            headers.setdefault('Content-Type', 'application/json')
        except json.JSONDecodeError:
            headers.setdefault('Content-Type', 'text/plain')
        return self._request('POST', url, data=body.encode(), headers=headers)

    def _head(self, shell: 'XShell', args: List[str]) -> int:
        """HEAD <url>"""
        if len(args) < 2:
            print('Usage: head <url>', file=sys.stderr)
            return 1
        url = args[1]
        req = urllib.request.Request(url, method='HEAD', headers=_DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f'\033[1mHTTP {resp.status} {resp.reason}\033[0m')
                for k, v in resp.headers.items():
                    print(f'  \033[36m{k}\033[0m: {v}')
            return 0
        except urllib.error.HTTPError as e:
            print(f'\033[31mHTTP {e.code} {e.reason}\033[0m', file=sys.stderr)
            return 1
        except Exception as e:
            print(f'\033[31m{e}\033[0m', file=sys.stderr)
            return 1

    def _download(self, shell: 'XShell', args: List[str]) -> int:
        """download <url> [filename]"""
        if len(args) < 2:
            print('Usage: download <url> [filename]', file=sys.stderr)
            return 1
        url      = args[1]
        filename = args[2] if len(args) > 2 else os.path.basename(
            urllib.parse.urlparse(url).path
        ) or 'download'
        dest = Path(filename)
        try:
            print(f'Downloading {url} → {dest}')
            urllib.request.urlretrieve(url, dest)
            size = dest.stat().st_size
            print(f'\033[32mDone\033[0m  {size:,} bytes → {dest}')
            return 0
        except Exception as e:
            print(f'\033[31m{e}\033[0m', file=sys.stderr)
            return 1

    # ── Shared ────────────────────────────────────────────────────────────

    def _request(
        self, method: str, url: str,
        data: bytes = None, headers: dict = None,
    ) -> int:
        req = urllib.request.Request(
            url, data=data, headers=headers or {}, method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                ct   = resp.headers.get('Content-Type', '')
                body = resp.read().decode('utf-8', errors='replace')
                print(f'\033[1mHTTP {resp.status} {resp.reason}\033[0m')
                print(_pretty(body, ct))
            return 0
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            print(f'\033[31mHTTP {e.code} {e.reason}\033[0m', file=sys.stderr)
            if body:
                ct = e.headers.get('Content-Type', '')
                print(_pretty(body, ct), file=sys.stderr)
            return 1
        except Exception as e:
            print(f'\033[31m{e}\033[0m', file=sys.stderr)
            return 1

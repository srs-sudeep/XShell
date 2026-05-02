"""
XShell prompt builder utilities.
Provides classic, powerline-style, and minimal prompt generators.
"""

import os
import sys
import getpass
import socket
import subprocess
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Info helpers
# ---------------------------------------------------------------------------

def user() -> str:
    return getpass.getuser()


def hostname(short: bool = True) -> str:
    h = socket.gethostname()
    return h.split('.')[0] if short else h


def cwd(max_parts: int = 3) -> str:
    raw = os.getcwd()
    home = str(Path.home())
    if raw.startswith(home):
        raw = '~' + raw[len(home):]
    parts = raw.replace('\\', '/').split('/')
    if len(parts) > max_parts:
        return '…/' + '/'.join(parts[-2:])
    return '/'.join(parts)


def git_branch() -> Optional[str]:
    try:
        r = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, timeout=1,
        )
        b = r.stdout.strip()
        if b == 'HEAD':
            sha = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True, text=True, timeout=1,
            ).stdout.strip()
            return f"({sha})"
        return b or None
    except Exception:
        return None


def git_status_indicator() -> str:
    try:
        r = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=1,
        )
        lines = r.stdout.splitlines()
        staged   = sum(1 for l in lines if l[:1] not in (' ', '?', ''))
        unstaged = sum(1 for l in lines if l[1:2] in ('M', 'D') or l[:1] == '?')
        parts = []
        if staged:
            parts.append(f'+{staged}')
        if unstaged:
            parts.append(f'~{unstaged}')
        return (' ' + ' '.join(parts)) if parts else ''
    except Exception:
        return ''


def venv_name() -> Optional[str]:
    venv = os.environ.get('VIRTUAL_ENV') or os.environ.get('CONDA_DEFAULT_ENV')
    if venv:
        return os.path.basename(venv)
    return None


# ---------------------------------------------------------------------------
# Classic prompt
# ---------------------------------------------------------------------------

def build_classic_prompt(
    user_color: str = '\033[96m',
    host_color: str = '\033[92m',
    cwd_color: str  = '\033[93m',
    git_color: str  = '\033[95m',
    venv_color: str = '\033[94m',
    reset: str = '\033[0m',
    show_venv: bool = True,
) -> str:
    parts = []

    venv = venv_name()
    if venv and show_venv:
        parts.append(f"{venv_color}({venv}){reset} ")

    parts.append(f"{user_color}{user()}{reset}")
    parts.append(f"@")
    parts.append(f"{host_color}{hostname()}{reset}")
    parts.append(f":")
    parts.append(f"{cwd_color}{cwd()}{reset}")

    branch = git_branch()
    if branch:
        gst = git_status_indicator()
        parts.append(f" {git_color}({branch}{gst}){reset}")

    parts.append(f" \033[1m$\033[0m ")
    return ''.join(parts)


# ---------------------------------------------------------------------------
# Powerline prompt  (requires Nerd Font / Powerline font in terminal)
# ---------------------------------------------------------------------------

_PL_SEP     = ''  # Solid right arrow
_PL_SEP_ALT = ''  # Thin right arrow
_PL_GIT     = ''  # Branch symbol
_PL_PYTHON  = ''  # Python symbol


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    if len(h) < 6:
        return '200;200;200'
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r};{g};{b}"


def build_powerline_prompt(theme_colors: dict | None = None) -> str:
    colors = theme_colors or {}

    bg_user = colors.get('prompt_user_bg', '#61afef')
    bg_cwd  = colors.get('prompt_cwd_bg',  '#e5c07b')
    bg_git  = colors.get('prompt_git_bg',  '#c678dd')
    bg_end  = colors.get('background',     '#1e1e1e')
    fg_dark = '28;28;28'

    try:
        u    = f"{user()}@{hostname()}"
        c    = cwd()
        git  = git_branch()
        gst  = git_status_indicator().strip()
        venv = venv_name()

        reset = '\033[0m'
        result = ''

        def seg(text: str, bg: str, next_bg: str) -> str:
            return (
                f"\033[38;2;{fg_dark}m\033[48;2;{_hex_to_rgb(bg)}m {text} "
                f"\033[0m\033[38;2;{_hex_to_rgb(bg)}m\033[48;2;{_hex_to_rgb(next_bg)}m{_PL_SEP}{reset}"
            )

        segments = [(u, bg_user)]
        if venv:
            bg_venv = colors.get('prompt_venv_bg', '#d19a66')
            segments.insert(0, (f"{_PL_PYTHON} {venv}", bg_venv))
        segments.append((c, bg_cwd))

        if git:
            label = f"{_PL_GIT} {git}"
            if gst:
                label += f" {gst}"
            segments.append((label, bg_git))

        # Render all segments
        for i, (text, bg) in enumerate(segments):
            next_bg = segments[i + 1][1] if i + 1 < len(segments) else bg_end
            result += seg(text, bg, next_bg)

        # Final closing arrow
        last_bg = segments[-1][1]
        result += f"\033[38;2;{_hex_to_rgb(last_bg)}m\033[48;2;{_hex_to_rgb(bg_end)}m{_PL_SEP}{reset} "

        return result
    except Exception:
        return build_classic_prompt()


# ---------------------------------------------------------------------------
# Minimal prompt  (for slow systems or narrow terminals)
# ---------------------------------------------------------------------------

def build_minimal_prompt(color: str = '\033[32m', reset: str = '\033[0m') -> str:
    return f"{color}{cwd()}{reset} $ "

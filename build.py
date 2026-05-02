#!/usr/bin/env python3
"""
XShell build script.
Packages XShell into a standalone executable using PyInstaller.

Usage:
  python build.py               Build the native shell (main.py)
  python build.py --web         Build the web terminal (web_app.py)
  python build.py --clean       Remove build/dist only, no rebuild
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def _module_exists(module_path: str) -> bool:
    try:
        return importlib.util.find_spec(module_path) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

# Data files to bundle (src : dest inside the package)
_DATA = [
    ('templates',  'templates'),
    ('static',     'static'),
    ('themes',     'themes'),
    ('plugins',    'plugins'),
]

# Hidden imports needed at runtime
_HIDDEN = [
    'engineio.async_drivers.threading',
    'eventlet.hubs.epolls',
    'eventlet.hubs.kqueue',
    'eventlet.hubs.selects',
    'prompt_toolkit',
    'prompt_toolkit.shortcuts',
    'prompt_toolkit.lexers',
    'prompt_toolkit.filters',
    'pygments.lexers.shell',
    'rich',
    'psutil',
    # Core plugins
    'xshell.plugins.builtin.git_plugin',
    'xshell.plugins.builtin.sysinfo_plugin',
    'xshell.plugins.builtin.calc_plugin',
    # Productivity plugins
    'xshell.plugins.builtin.z_plugin',
    'xshell.plugins.builtin.bookmark_plugin',
    'xshell.plugins.builtin.envload_plugin',
    'xshell.plugins.builtin.notify_plugin',
    'xshell.plugins.builtin.session_plugin',
    'xshell.plugins.builtin.ssh_plugin',
    'xshell.plugins.builtin.process_plugin',
    # Developer utility plugins
    'xshell.plugins.builtin.json_plugin',
    'xshell.plugins.builtin.csv_plugin',
    'xshell.plugins.builtin.hash_plugin',
    'xshell.plugins.builtin.encode_plugin',
    'xshell.plugins.builtin.ports_plugin',
    'xshell.plugins.builtin.diff_plugin',
    'xshell.plugins.builtin.k8s_plugin',
    'xshell.plugins.builtin.npm_plugin',
    'xshell.plugins.builtin.llm_plugin',
    # Core new modules
    'xshell.core.scripting',
    'xshell.core.updater',
    'xshell.plugins.registry',
]

_HIDDEN = [imp for imp in _HIDDEN if _module_exists(imp)]


def clean():
    for d in ('build', 'dist', '__pycache__'):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)
            print(f"  Removed {p}")
    for spec in ROOT.glob('*.spec'):
        spec.unlink()
        print(f"  Removed {spec}")


def _sep() -> str:
    return ';' if sys.platform == 'win32' else ':'


def build(target: str, name: str, windowed: bool = False):
    clean()

    sep = _sep()
    cmd = [
        'pyinstaller',
        f'--name={name}',
        '--onefile',
        '--clean',
    ]

    for src, dst in _DATA:
        if (ROOT / src).exists():
            cmd.append(f'--add-data={src}{sep}{dst}')

    for imp in _HIDDEN:
        cmd.append(f'--hidden-import={imp}')

    icon = ROOT / 'static' / 'terminal.ico'
    if icon.exists():
        cmd.append(f'--icon={icon}')

    if windowed and sys.platform != 'win32':
        cmd.append('--windowed')

    cmd.append(target)

    print(f"\nBuilding '{name}' from {target} …")
    print('  ' + ' '.join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode != 0:
        print(f"\nBuild FAILED (exit {result.returncode})")
        sys.exit(result.returncode)

    exe = ROOT / 'dist' / (name + ('.exe' if sys.platform == 'win32' else ''))
    if exe.exists():
        size = exe.stat().st_size / (1024 * 1024)
        print(f"\nBuild succeeded: {exe}  ({size:.1f} MB)")
    else:
        print(f"\nBuild succeeded. Output in {ROOT / 'dist'}")


def main():
    p = argparse.ArgumentParser(description='XShell build tool')
    p.add_argument('--web',   action='store_true', help='Build web terminal')
    p.add_argument('--clean', action='store_true', help='Clean only, no build')
    args = p.parse_args()

    if args.clean:
        clean()
        print("Clean done.")
        return

    if args.web:
        build('web_app.py', 'xshell-web')
    else:
        build('main.py', 'xshell')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
XShell — A feature-rich cross-platform shell

Usage:
  python main.py                  Run the native interactive shell
  python main.py --web            Run the web-based terminal (browser UI)
  python main.py --web --port N   Web UI on custom port
  python main.py --theme <name>   Start with a specific theme
  python main.py --no-plugins     Disable the plugin system
  python main.py --version        Print version and exit
  python main.py -c "command"     Execute a single command and exit
"""

import sys
import argparse


def _parse_args():
    p = argparse.ArgumentParser(
        description='XShell — cross-platform shell',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--web',        action='store_true', help='Run web interface')
    p.add_argument('--port',       type=int, default=5000, help='Web server port')
    p.add_argument('--theme',      type=str, help='Set theme (default, dracula, nord, monokai, solarized)')
    p.add_argument('--no-plugins', action='store_true', dest='no_plugins', help='Disable plugins')
    p.add_argument('--version',    action='store_true', help='Show version')
    p.add_argument('-c',           dest='command', metavar='CMD', help='Execute command and exit')
    return p.parse_args()


def main():
    args = _parse_args()

    if args.version:
        from xshell import __version__
        print(f"XShell v{__version__}")
        sys.exit(0)

    if args.web:
        from web_app import run_web
        run_web(port=args.port)
        return

    from xshell.core.shell import XShell

    shell = XShell(
        load_plugins=not args.no_plugins,
        theme=args.theme,
    )

    if args.command:
        code = shell.execute_line(args.command)
        sys.exit(code)

    sys.exit(shell.run())


if __name__ == '__main__':
    main()

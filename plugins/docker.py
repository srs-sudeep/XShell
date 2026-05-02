"""
XShell Docker plugin — drop-in example plugin.

Commands: dps, dimg, dbuild, dlogs, dexec, dstop, drm, dprune

Install:  plugin load docker
Remove:   plugin unload docker
"""

import subprocess
import sys
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell


def _docker(*args) -> int:
    try:
        return subprocess.run(['docker', *args]).returncode
    except FileNotFoundError:
        print('docker: Docker is not installed or not on PATH', file=sys.stderr)
        return 127


class DockerPlugin(XShellPlugin):
    name        = 'docker'
    description = 'Docker shortcuts — dps, dimg, dbuild, dlogs, dexec, dstop, drm, dprune'
    version     = '1.0.0'
    author      = 'XShell Examples'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command('dps',    self._dps,    ['--all', '-a', '--format'])
        self.register_command('dimg',   self._dimg,   ['--all', '-a', '--format'])
        self.register_command('dbuild', self._dbuild, ['-t', '--no-cache', '--platform'])
        self.register_command('dlogs',  self._dlogs,  ['-f', '--tail', '--since'])
        self.register_command('dexec',  self._dexec,  ['-it', '-i', '-t'])
        self.register_command('dstop',  self._dstop)
        self.register_command('drm',    self._drm,    ['-f', '-v'])
        self.register_command('dprune', self._dprune, ['-f', '--volumes'])
        self.register_command('dpull',  self._dpull)
        self.register_command('dpush',  self._dpush)

    # ── Commands ──────────────────────────────────────────────────────────

    def _dps(self, shell: 'XShell', args: List[str]) -> int:
        """List running containers.  dps [-a]"""
        extra = args[1:] if len(args) > 1 else []
        return _docker('ps', *extra)

    def _dimg(self, shell: 'XShell', args: List[str]) -> int:
        """List images.  dimg [-a]"""
        return _docker('images', *args[1:])

    def _dbuild(self, shell: 'XShell', args: List[str]) -> int:
        """Build an image.  dbuild -t name:tag [path]"""
        extra = args[1:] if len(args) > 1 else ['.']
        return _docker('build', *extra)

    def _dlogs(self, shell: 'XShell', args: List[str]) -> int:
        """Show container logs.  dlogs [-f] <container>"""
        if len(args) < 2:
            print('Usage: dlogs [-f] [--tail N] <container>', file=sys.stderr)
            return 1
        return _docker('logs', *args[1:])

    def _dexec(self, shell: 'XShell', args: List[str]) -> int:
        """Exec into container.  dexec <container> [cmd]"""
        if len(args) < 2:
            print('Usage: dexec <container> [cmd]', file=sys.stderr)
            return 1
        extra = args[2:] if len(args) > 2 else ['sh']
        return _docker('exec', '-it', args[1], *extra)

    def _dstop(self, shell: 'XShell', args: List[str]) -> int:
        """Stop one or more containers.  dstop <container> [...]"""
        if len(args) < 2:
            print('Usage: dstop <container> [container ...]', file=sys.stderr)
            return 1
        return _docker('stop', *args[1:])

    def _drm(self, shell: 'XShell', args: List[str]) -> int:
        """Remove containers.  drm [-f] <container> [...]"""
        if len(args) < 2:
            print('Usage: drm [-f] <container> [container ...]', file=sys.stderr)
            return 1
        return _docker('rm', *args[1:])

    def _dprune(self, shell: 'XShell', args: List[str]) -> int:
        """Remove all stopped containers and dangling images.  dprune [-f]"""
        extra = args[1:] if len(args) > 1 else ['-f']
        _docker('container', 'prune', *extra)
        return _docker('image', 'prune', *extra)

    def _dpull(self, shell: 'XShell', args: List[str]) -> int:
        """Pull an image.  dpull <image>"""
        if len(args) < 2:
            print('Usage: dpull <image>', file=sys.stderr)
            return 1
        return _docker('pull', *args[1:])

    def _dpush(self, shell: 'XShell', args: List[str]) -> int:
        """Push an image.  dpush <image>"""
        if len(args) < 2:
            print('Usage: dpush <image>', file=sys.stderr)
            return 1
        return _docker('push', *args[1:])

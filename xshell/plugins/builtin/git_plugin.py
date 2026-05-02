"""
XShell git plugin — built-in.

Provides short aliases for the most common git operations.

Commands:
  gst              git status
  glog             pretty commit graph (last 20)
  gdiff            git diff
  gadd [files]     git add . (or specified paths)
  gcommit [flags]  git commit
  gpush [flags]    git push
  gpull [flags]    git pull
  gbranch [flags]  git branch
  gcheckout [flags] git checkout
  gstash [sub]     git stash [pop|list|drop]
  grebase [flags]  git rebase
"""

import subprocess
import sys
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell


def _git(*args) -> int:
    try:
        return subprocess.run(['git', *args]).returncode
    except FileNotFoundError:
        print('git: git is not installed or not on PATH', file=sys.stderr)
        return 127


class GitPlugin(XShellPlugin):
    name        = 'git'
    description = 'Git shortcuts — gst, glog, gdiff, gadd, gcommit, gpush, gpull, …'
    version     = '1.0.0'
    author      = 'XShell'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command('gst',       self._gst,       ['-s', '-b', '--short'])
        self.register_command('glog',      self._glog,      ['--all', '--oneline', '--stat'])
        self.register_command('gdiff',     self._gdiff,     ['--staged', '--stat'])
        self.register_command('gadd',      self._gadd,      ['-p', '-u', '--all'])
        self.register_command('gcommit',   self._gcommit,   ['-m', '-a', '--amend'])
        self.register_command('gpush',     self._gpush,     ['-u', '--force-with-lease'])
        self.register_command('gpull',     self._gpull,     ['--rebase', '--ff-only'])
        self.register_command('gbranch',   self._gbranch,   ['-a', '-d', '-D', '-r'])
        self.register_command('gcheckout', self._gcheckout, ['-b', '-B', '--track'])
        self.register_command('gstash',    self._gstash,    ['pop', 'list', 'drop', 'show'])
        self.register_command('grebase',   self._grebase,   ['--interactive', '-i', '--abort', '--continue'])

    # ── Commands ──────────────────────────────────────────────────────────

    def _gst(self, shell: 'XShell', args: List[str]) -> int:
        """git status"""
        return _git('status', *args[1:])

    def _glog(self, shell: 'XShell', args: List[str]) -> int:
        """Pretty one-line graph log (last 20 entries)."""
        extra = args[1:]
        if not extra:
            extra = ['--oneline', '--graph', '--decorate', '--all', '-20']
        return _git('log', *extra)

    def _gdiff(self, shell: 'XShell', args: List[str]) -> int:
        """git diff"""
        return _git('diff', *args[1:])

    def _gadd(self, shell: 'XShell', args: List[str]) -> int:
        """git add . (or specified paths)"""
        paths = args[1:] if len(args) > 1 else ['.']
        return _git('add', *paths)

    def _gcommit(self, shell: 'XShell', args: List[str]) -> int:
        """git commit"""
        return _git('commit', *args[1:])

    def _gpush(self, shell: 'XShell', args: List[str]) -> int:
        """git push"""
        return _git('push', *args[1:])

    def _gpull(self, shell: 'XShell', args: List[str]) -> int:
        """git pull"""
        return _git('pull', *args[1:])

    def _gbranch(self, shell: 'XShell', args: List[str]) -> int:
        """git branch"""
        return _git('branch', *args[1:])

    def _gcheckout(self, shell: 'XShell', args: List[str]) -> int:
        """git checkout"""
        return _git('checkout', *args[1:])

    def _gstash(self, shell: 'XShell', args: List[str]) -> int:
        """git stash [pop|list|drop|show]"""
        sub = args[1] if len(args) > 1 else 'list'
        return _git('stash', sub, *args[2:])

    def _grebase(self, shell: 'XShell', args: List[str]) -> int:
        """git rebase"""
        return _git('rebase', *args[1:])

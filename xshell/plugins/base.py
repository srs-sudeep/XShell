"""
Base class for all XShell plugins.
Every plugin must subclass XShellPlugin and implement at minimum `name`.
"""

from typing import TYPE_CHECKING, Callable, Dict, List

if TYPE_CHECKING:
    from ..core.shell import XShell


class XShellPlugin:
    """Abstract base for XShell plugins."""

    # Required: unique lowercase identifier
    name: str = ''
    # Optional human-readable description
    description: str = ''
    # Semantic version string
    version: str = '1.0.0'
    # Author info
    author: str = ''

    def __init__(self):
        self._shell = None
        self._commands: Dict[str, Callable] = {}
        self._completions: Dict[str, List[str]] = {}
        self._help: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def on_load(self, shell: 'XShell') -> None:
        """Called when the plugin is loaded. Register commands here."""
        self._shell = shell

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        self._shell = None

    def on_prompt(self) -> str:
        """Return extra text to append to the prompt (empty = nothing)."""
        return ''

    # ------------------------------------------------------------------
    # Command registration helpers
    # ------------------------------------------------------------------

    def register_command(self, name: str, fn: Callable, completions: List[str] = None, help: str = '') -> None:
        self._commands[name] = fn
        if completions:
            self._completions[name] = completions
        # Use explicit help string, fall back to function docstring
        self._help[name] = help or (fn.__doc__ or '').strip()

    def commands(self) -> Dict[str, Callable]:
        return dict(self._commands)

    def completions_for(self, cmd: str) -> List[str]:
        return self._completions.get(cmd, [])

    def help_for(self, cmd: str) -> str:
        return self._help.get(cmd, '')

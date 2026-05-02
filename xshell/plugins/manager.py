"""
XShell plugin manager.
Loads built-in plugins from xshell/plugins/builtin/ and user plugins from
~/.xshell/plugins/ (or %APPDATA%/XShell/plugins/ on Windows).
"""

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple

from .base import XShellPlugin

if TYPE_CHECKING:
    from ..core.shell import XShell

_BUILTIN_MAP = {
    'git':      'xshell.plugins.builtin.git_plugin',
    'sysinfo':  'xshell.plugins.builtin.sysinfo_plugin',
    'calc':     'xshell.plugins.builtin.calc_plugin',
    # Productivity
    'z':        'xshell.plugins.builtin.z_plugin',
    'bookmark': 'xshell.plugins.builtin.bookmark_plugin',
    'envload':  'xshell.plugins.builtin.envload_plugin',
    'notify':   'xshell.plugins.builtin.notify_plugin',
    'session':  'xshell.plugins.builtin.session_plugin',
    'ssh':      'xshell.plugins.builtin.ssh_plugin',
    'process':  'xshell.plugins.builtin.process_plugin',
    # Developer utilities
    'json':     'xshell.plugins.builtin.json_plugin',
    'csv':      'xshell.plugins.builtin.csv_plugin',
    'hash':     'xshell.plugins.builtin.hash_plugin',
    'encode':   'xshell.plugins.builtin.encode_plugin',
    'ports':    'xshell.plugins.builtin.ports_plugin',
    'diff':     'xshell.plugins.builtin.diff_plugin',
    'k8s':      'xshell.plugins.builtin.k8s_plugin',
    'npm':      'xshell.plugins.builtin.npm_plugin',
    'llm':      'xshell.plugins.builtin.llm_plugin',
}

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _module_exists(module_path: str) -> bool:
    try:
        return importlib.util.find_spec(module_path) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _user_plugin_dir() -> Path:
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home())) / 'XShell' / 'plugins'
    else:
        base = Path.home() / '.xshell' / 'plugins'
    base.mkdir(parents=True, exist_ok=True)
    return base


class PluginManager:
    def __init__(self, shell: 'XShell'):
        self.shell = shell
        self._plugins: Dict[str, XShellPlugin] = {}
        self._commands: Dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_configured_plugins(self) -> None:
        configured = list(self.shell.config.get('plugins', []))
        missing_builtins: List[str] = []

        for name in configured:
            if name in _BUILTIN_MAP and not _module_exists(_BUILTIN_MAP[name]):
                missing_builtins.append(name)
                continue

            ok, msg = self.load(name)
            if not ok:
                print(f"[plugin] warning: {msg}", file=sys.stderr)

        if missing_builtins:
            self.shell.config.set(
                'plugins',
                [name for name in configured if name not in missing_builtins],
            )
            self.shell.config.save()

    def load(self, name: str) -> Tuple[bool, str]:
        if name in self._plugins:
            return False, f"plugin '{name}' already loaded"

        plugin = self._resolve(name)
        if plugin is None:
            return False, f"plugin '{name}' not found"

        try:
            plugin.on_load(self.shell)
        except Exception as exc:
            return False, f"plugin '{name}' failed to load: {exc}"

        self._plugins[name] = plugin
        for cmd_name, fn in plugin.commands().items():
            self._commands[cmd_name] = fn

        return True, f"plugin '{name}' loaded"

    def unload(self, name: str) -> Tuple[bool, str]:
        if name not in self._plugins:
            return False, f"plugin '{name}' is not loaded"
        plugin = self._plugins.pop(name)
        try:
            plugin.on_unload()
        except Exception:
            pass
        # Remove this plugin's commands
        for cmd_name in list(plugin.commands().keys()):
            self._commands.pop(cmd_name, None)
        return True, f"plugin '{name}' unloaded"

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def loaded_names(self) -> List[str]:
        return sorted(self._plugins.keys())

    def get(self, name: str) -> Optional[XShellPlugin]:
        return self._plugins.get(name)

    def get_command(self, name: str) -> Optional[Callable]:
        return self._commands.get(name)

    def all_commands(self) -> Dict[str, Callable]:
        return dict(self._commands)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def _resolve(self, name: str) -> Optional[XShellPlugin]:
        # 1. Built-in
        if name in _BUILTIN_MAP and _module_exists(_BUILTIN_MAP[name]):
            return self._load_module(name, _BUILTIN_MAP[name])

        # 2. User plugin directory
        user_dir = _user_plugin_dir()
        candidate = user_dir / f"{name}.py"
        if candidate.exists():
            return self._load_file(name, candidate)

        # 3. Also scan the project-local plugins/ directory
        local = _PROJECT_ROOT / 'plugins' / f"{name}.py"
        if local.exists():
            return self._load_file(name, local)

        return None

    def _load_module(self, name: str, module_path: str) -> Optional[XShellPlugin]:
        try:
            mod = importlib.import_module(module_path)
            return self._instantiate(mod, name)
        except ImportError as e:
            print(f"[plugin] import error for '{name}': {e}", file=sys.stderr)
            return None

    def _load_file(self, name: str, path: Path) -> Optional[XShellPlugin]:
        try:
            spec = importlib.util.spec_from_file_location(f"xshell_plugin_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return self._instantiate(mod, name)
        except Exception as e:
            print(f"[plugin] error loading '{path}': {e}", file=sys.stderr)
            return None

    @staticmethod
    def _instantiate(mod, name: str) -> Optional[XShellPlugin]:
        # Find a subclass of XShellPlugin in the module
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, XShellPlugin)
                and obj is not XShellPlugin
            ):
                return obj()
        return None

"""
XShell sysinfo plugin — built-in.

Provides system diagnostics commands. Uses psutil when available and
degrades gracefully to stdlib-only info when it is not installed.

Commands:
  sysinfo              OS / CPU / RAM summary
  diskusage [path]     disk usage for a path
  netinfo              network interfaces
  procs [-n N]         top processes by CPU
  uptime               system uptime
"""

import platform
import sys
from datetime import timedelta
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def _bar(pct: float, width: int = 20) -> str:
    filled = int(width * pct / 100)
    return '[' + '█' * filled + '░' * (width - filled) + ']'


class SysinfoPlugin(XShellPlugin):
    name        = 'sysinfo'
    description = 'System diagnostics — sysinfo, diskusage, netinfo, procs, uptime'
    version     = '1.0.0'
    author      = 'XShell'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command('sysinfo',   self._sysinfo,   ['--json'])
        self.register_command('diskusage', self._diskusage)
        self.register_command('netinfo',   self._netinfo)
        self.register_command('procs',     self._procs,     ['-n', '--sort-cpu', '--sort-mem'])
        self.register_command('uptime',    self._uptime)

    # ── sysinfo ───────────────────────────────────────────────────────────

    def _sysinfo(self, shell: 'XShell', args: List[str]) -> int:
        uname = platform.uname()
        print('\n  \033[1mSystem Information\033[0m')
        print(f'  OS:       {uname.system} {uname.release} ({uname.machine})')
        print(f'  Hostname: {uname.node}')
        print(f'  Python:   {platform.python_version()}')

        if _HAS_PSUTIL:
            cpu_pct = psutil.cpu_percent(interval=0.2)
            cpu_count = psutil.cpu_count()
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()

            ram_used_gb  = vm.used  / 1024 ** 3
            ram_total_gb = vm.total / 1024 ** 3
            swap_used_gb  = swap.used  / 1024 ** 3
            swap_total_gb = swap.total / 1024 ** 3

            print(f'  CPU:      {cpu_pct:.1f}% across {cpu_count} cores')
            print(f'  RAM:      {_bar(vm.percent)} {vm.percent:.1f}%  '
                  f'{ram_used_gb:.1f} GB / {ram_total_gb:.1f} GB')
            if swap.total > 0:
                print(f'  Swap:     {_bar(swap.percent)} {swap.percent:.1f}%  '
                      f'{swap_used_gb:.1f} GB / {swap_total_gb:.1f} GB')
        else:
            print('  (install psutil for CPU/RAM details: pip install psutil)')

        print()
        return 0

    # ── diskusage ─────────────────────────────────────────────────────────

    def _diskusage(self, shell: 'XShell', args: List[str]) -> int:
        path = args[1] if len(args) > 1 else ('C:\\' if sys.platform == 'win32' else '/')
        if not _HAS_PSUTIL:
            print('diskusage requires psutil — pip install psutil', file=sys.stderr)
            return 1
        try:
            usage = psutil.disk_usage(path)
            used_gb  = usage.used  / 1024 ** 3
            total_gb = usage.total / 1024 ** 3
            print(f'\n  Disk usage: {path}')
            print(f'  {_bar(usage.percent)} {usage.percent:.1f}%  '
                  f'{used_gb:.1f} GB / {total_gb:.1f} GB\n')
        except (FileNotFoundError, PermissionError) as e:
            print(f'diskusage: {e}', file=sys.stderr)
            return 1
        return 0

    # ── netinfo ───────────────────────────────────────────────────────────

    def _netinfo(self, shell: 'XShell', args: List[str]) -> int:
        if not _HAS_PSUTIL:
            print('netinfo requires psutil — pip install psutil', file=sys.stderr)
            return 1
        print('\n  \033[1mNetwork Interfaces\033[0m')
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        for iface, addr_list in sorted(addrs.items()):
            up = stats[iface].isup if iface in stats else False
            status = '\033[32m↑ up\033[0m' if up else '\033[31m↓ down\033[0m'
            ips = [a.address for a in addr_list if a.family.name in ('AF_INET', 'AF_INET6')]
            ip_str = ', '.join(ips) if ips else '(no IP)'
            print(f'  {iface:<16} {status}  {ip_str}')
        print()
        return 0

    # ── procs ─────────────────────────────────────────────────────────────

    def _procs(self, shell: 'XShell', args: List[str]) -> int:
        if not _HAS_PSUTIL:
            print('procs requires psutil — pip install psutil', file=sys.stderr)
            return 1

        n = 15
        sort_key = 'cpu_percent'
        i = 1
        while i < len(args):
            if args[i] == '-n' and i + 1 < len(args):
                try:
                    n = int(args[i + 1])
                    i += 2
                    continue
                except ValueError:
                    pass
            elif args[i] == '--sort-mem':
                sort_key = 'memory_percent'
            i += 1

        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x.get(sort_key, 0) or 0, reverse=True)
        procs = procs[:n]

        print(f'\n  {"PID":>7}  {"CPU%":>6}  {"MEM%":>6}  {"STATUS":<10}  NAME')
        print('  ' + '-' * 58)
        for p in procs:
            print(f'  {p["pid"]:>7}  {(p["cpu_percent"] or 0):>5.1f}%  '
                  f'{(p["memory_percent"] or 0):>5.1f}%  '
                  f'{p["status"]:<10}  {p["name"]}')
        print()
        return 0

    # ── uptime ────────────────────────────────────────────────────────────

    def _uptime(self, shell: 'XShell', args: List[str]) -> int:
        if not _HAS_PSUTIL:
            print('uptime requires psutil — pip install psutil', file=sys.stderr)
            return 1
        import time
        delta = timedelta(seconds=int(time.time() - psutil.boot_time()))
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days = delta.days
        if days:
            print(f'  Up {days}d {hours % 24}h {minutes}m {seconds}s')
        else:
            print(f'  Up {hours}h {minutes}m {seconds}s')
        return 0

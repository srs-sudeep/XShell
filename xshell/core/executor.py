"""
Command executor for XShell.
Handles environment expansion, glob expansion, pipes, redirects, and background jobs.
"""

import os
import sys
import glob
import subprocess
import threading
from typing import TYPE_CHECKING, List, Optional

from .parser import Command, Pipeline, CommandList, TokenType
from .builtins import get_builtin

if TYPE_CHECKING:
    from .shell import XShell


class CommandExecutor:
    def __init__(self, shell: 'XShell'):
        self.shell = shell

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def execute_command_list(self, cmd_list: CommandList) -> int:
        last_code = 0
        for pipeline, connector in cmd_list.pipelines:
            if connector == TokenType.AND and last_code != 0:
                break
            if connector == TokenType.OR and last_code == 0:
                break
            last_code = self.execute_pipeline(pipeline)
        return last_code

    def execute_pipeline(self, pipeline: Pipeline) -> int:
        if not pipeline.commands:
            return 0

        if pipeline.background:
            # Track as a job
            first_cmd = self._expand(pipeline.commands[0])
            cmd_str = ' '.join(first_cmd.args)
            try:
                proc = subprocess.Popen(
                    cmd_str, shell=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                if hasattr(self.shell, '_background_jobs'):
                    self.shell._job_counter += 1
                    job_id = self.shell._job_counter
                    self.shell._background_jobs[job_id] = {'proc': proc, 'cmd': cmd_str}
                    print(f"[{job_id}] {proc.pid}")
            except Exception as e:
                print(f"xshell: background: {e}", file=sys.stderr)
            return 0

        return self._run_pipeline(pipeline.commands)

    # ------------------------------------------------------------------
    # Internal pipeline execution
    # ------------------------------------------------------------------

    def _run_pipeline(self, commands: List[Command]) -> int:
        if len(commands) == 1:
            return self._run_single(commands[0], stdin=None, stdout=None)

        processes = []
        prev_stdout = None

        for i, cmd in enumerate(commands):
            is_last = i == len(commands) - 1
            expanded = self._expand(cmd)
            if not expanded.args:
                continue

            builtin_fn = get_builtin(expanded.args[0])
            if builtin_fn:
                # Builtins in a pipeline: capture output via subprocess trick isn't clean;
                # run them sequentially with captured output written to pipe.
                # For simplicity, builtins in a pipeline run with inherited stdin/stdout.
                code = builtin_fn(self.shell, expanded.args)
                prev_stdout = None
                continue

            stdin = prev_stdout
            if expanded.stdin_file:
                try:
                    stdin = open(expanded.stdin_file, 'rb')
                except OSError as e:
                    print(f"xshell: {e}", file=sys.stderr)
                    return 1

            if is_last:
                stdout = None  # inherit terminal stdout
                if expanded.stdout_file:
                    mode = 'a' if expanded.stdout_append else 'w'
                    try:
                        stdout = open(expanded.stdout_file, mode)
                    except OSError as e:
                        print(f"xshell: {e}", file=sys.stderr)
                        return 1
            else:
                stdout = subprocess.PIPE

            try:
                proc = subprocess.Popen(
                    expanded.args,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=None,
                    env=os.environ,
                )
                processes.append((proc, stdout))
                prev_stdout = proc.stdout
            except FileNotFoundError:
                print(f"xshell: {expanded.args[0]}: command not found", file=sys.stderr)
                return 127
            except PermissionError:
                print(f"xshell: {expanded.args[0]}: Permission denied", file=sys.stderr)
                return 126

        last_code = 0
        for proc, stdout_file in processes:
            proc.wait()
            last_code = proc.returncode
            if stdout_file and stdout_file != subprocess.PIPE:
                try:
                    stdout_file.close()
                except Exception:
                    pass
        return last_code

    def _run_single(
        self,
        cmd: Command,
        stdin=None,
        stdout=None,
    ) -> int:
        expanded = self._expand(cmd)
        if not expanded.args:
            return 0

        name = expanded.args[0]

        # Built-in check
        builtin_fn = get_builtin(name)
        if builtin_fn:
            return builtin_fn(self.shell, expanded.args)

        # Plugin command check
        if self.shell.plugin_manager:
            plugin_fn = self.shell.plugin_manager.get_command(name)
            if plugin_fn:
                return plugin_fn(self.shell, expanded.args)

        # External command
        stdin_fh = None
        stdout_fh = None
        try:
            if expanded.stdin_file:
                stdin_fh = open(expanded.stdin_file, 'rb')
            if expanded.stdout_file:
                mode = 'a' if expanded.stdout_append else 'w'
                stdout_fh = open(expanded.stdout_file, 'w', encoding='utf-8')

            proc = subprocess.Popen(
                expanded.args,
                stdin=stdin_fh or stdin,
                stdout=stdout_fh or stdout,
                stderr=None,
                env=os.environ,
            )
            proc.wait()
            return proc.returncode

        except FileNotFoundError:
            return self._handle_not_found(name)
        except PermissionError:
            print(f"xshell: {name}: Permission denied", file=sys.stderr)
            return 126
        except Exception as e:
            print(f"xshell: {name}: {e}", file=sys.stderr)
            return 1
        finally:
            if stdin_fh:
                stdin_fh.close()
            if stdout_fh:
                stdout_fh.close()

    def _handle_not_found(self, name: str) -> int:
        if self.shell.config.get('autocorrect', True):
            builtins = list(get_builtin.__module__ and [])
            from .builtins import list_builtins
            plugin_cmds = list(self.shell.plugin_manager.all_commands().keys()) if self.shell.plugin_manager else []
            suggestion = self.shell.autocorrect.suggest(name, list_builtins(), plugin_cmds)
            if suggestion:
                print(
                    f"\033[33mxshell: '{name}' not found. Did you mean '\033[1m{suggestion}\033[0;33m'?\033[0m",
                    file=sys.stderr,
                )
            else:
                print(f"xshell: {name}: command not found", file=sys.stderr)
        else:
            print(f"xshell: {name}: command not found", file=sys.stderr)
        return 127

    # ------------------------------------------------------------------
    # Expansion
    # ------------------------------------------------------------------

    def _expand(self, cmd: Command) -> Command:
        """Apply variable, tilde, glob, and command-substitution expansion to command args."""
        import re

        def _cmd_sub(text: str) -> str:
            """Replace $(...) with command output."""
            pattern = re.compile(r'\$\(([^)]+)\)')
            while True:
                m = pattern.search(text)
                if not m:
                    break
                inner = os.path.expandvars(m.group(1))
                try:
                    result = subprocess.check_output(
                        inner, shell=True, text=True, stderr=subprocess.DEVNULL
                    ).rstrip('\n')
                except Exception:
                    result = ''
                text = text[:m.start()] + result + text[m.end():]
            return text

        new_args = []
        for arg in cmd.args:
            # Command substitution first
            arg = _cmd_sub(arg)
            expanded = os.path.expanduser(os.path.expandvars(arg))
            # Glob expansion
            matches = glob.glob(expanded)
            if matches and any(c in arg for c in ('*', '?', '[')):
                new_args.extend(sorted(matches))
            else:
                new_args.append(expanded)

        return Command(
            args=new_args,
            stdin_file=cmd.stdin_file,
            stdout_file=cmd.stdout_file,
            stdout_append=cmd.stdout_append,
            background=cmd.background,
        )

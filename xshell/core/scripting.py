"""
XShell scripting engine — interprets .xsh files.
Supports: variables, if/elif/else/fi, for/done, while/done,
functions, command substitution $(...), arithmetic $((expr)).
"""

from __future__ import annotations

import os
import re
import sys
import subprocess
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .shell import XShell


# ---------------------------------------------------------------------------
# Tokeniser helpers
# ---------------------------------------------------------------------------

def _split_lines(text: str) -> List[str]:
    lines: List[str] = []
    buf = ''
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped.endswith('\\'):
            buf += stripped[:-1] + ' '
        else:
            lines.append(buf + stripped)
            buf = ''
    if buf:
        lines.append(buf)
    return lines


def _expand_vars(text: str, local_vars: Dict[str, str]) -> str:
    """Expand $VAR, ${VAR}, $((expr)), and $(cmd) in text."""
    text = _expand_cmd_substitution(text, local_vars)
    text = _expand_arithmetic(text, local_vars)

    def _replace(m: re.Match) -> str:
        name = m.group(1) or m.group(2)
        return local_vars.get(name, os.environ.get(name, ''))

    text = re.sub(r'\$\{(\w+)\}|\$(\w+)', _replace, text)
    return text


def _expand_cmd_substitution(text: str, local_vars: Dict[str, str]) -> str:
    pattern = re.compile(r'\$\(([^)]+)\)')
    while True:
        m = pattern.search(text)
        if not m:
            break
        inner = m.group(1)
        inner = _expand_vars(inner, local_vars)
        try:
            result = subprocess.check_output(
                inner, shell=True, text=True, stderr=subprocess.DEVNULL
            ).rstrip('\n')
        except Exception:
            result = ''
        text = text[:m.start()] + result + text[m.end():]
    return text


def _expand_arithmetic(text: str, local_vars: Dict[str, str]) -> str:
    pattern = re.compile(r'\$\(\(([^)]+)\)\)')
    while True:
        m = pattern.search(text)
        if not m:
            break
        expr = m.group(1)
        expr = re.sub(
            r'\$\{?(\w+)\}?',
            lambda x: local_vars.get(x.group(1), os.environ.get(x.group(1), '0')),
            expr,
        )
        try:
            result = str(int(eval(expr, {"__builtins__": {}})))  # noqa: S307
        except Exception:
            result = '0'
        text = text[:m.start()] + result + text[m.end():]
    return text


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

class ScriptInterpreter:
    """Executes .xsh scripts with basic control flow."""

    def __init__(self, shell: 'XShell'):
        self.shell = shell
        self.local_vars: Dict[str, str] = {}
        self.functions: Dict[str, List[str]] = {}
        self._return_code: int = 0
        self._return_flag: bool = False

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def run_file(self, path: str, args: List[str] | None = None) -> int:
        args = args or []
        try:
            with open(path, encoding='utf-8') as fh:
                source = fh.read()
        except OSError as e:
            print(f"xshell: {path}: {e.strerror}", file=sys.stderr)
            return 1

        # Positional params
        for i, a in enumerate(args):
            self.local_vars[str(i)] = a
        self.local_vars['#'] = str(len(args))
        self.local_vars['0'] = path

        lines = _split_lines(source)
        return self._exec_block(lines, 0, len(lines))[1]

    def run_string(self, source: str) -> int:
        lines = _split_lines(source)
        _, code = self._exec_block(lines, 0, len(lines))
        return code

    # ----------------------------------------------------------------
    # Block executor — returns (next_line_index, exit_code)
    # ----------------------------------------------------------------

    def _exec_block(self, lines: List[str], start: int, end: int) -> Tuple[int, int]:
        i = start
        last_code = 0
        while i < end:
            line = lines[i].strip()

            if not line or line.startswith('#'):
                i += 1
                continue

            # Variable assignment: NAME=value
            m = re.match(r'^(\w+)=(.*)', line)
            if m:
                name, val = m.group(1), m.group(2).strip('"\'')
                self.local_vars[name] = _expand_vars(val, self.local_vars)
                os.environ[name] = self.local_vars[name]
                i += 1
                continue

            # Function definition
            m = re.match(r'^(\w+)\s*\(\s*\)\s*\{?\s*$', line)
            if m:
                fname = m.group(1)
                i, body = self._collect_block(lines, i + 1, end, closing='')
                self.functions[fname] = body
                continue

            # if
            if line.startswith('if '):
                i, last_code = self._exec_if(lines, i, end)
                continue

            # for
            if line.startswith('for '):
                i, last_code = self._exec_for(lines, i, end)
                continue

            # while
            if line.startswith('while '):
                i, last_code = self._exec_while(lines, i, end)
                continue

            # return
            if line.startswith('return'):
                parts = line.split()
                try:
                    self._return_code = int(parts[1]) if len(parts) > 1 else last_code
                except ValueError:
                    self._return_code = last_code
                self._return_flag = True
                return i, self._return_code

            # break / continue  (handled by loop)
            if line in ('break', 'continue'):
                return i, 0

            # Expanded execution
            expanded = _expand_vars(line, self.local_vars)
            last_code = self._exec_line(expanded)
            if self._return_flag:
                return i, self._return_code
            i += 1

        return i, last_code

    # ----------------------------------------------------------------
    # Control flow helpers
    # ----------------------------------------------------------------

    def _collect_block(
        self, lines: List[str], start: int, end: int, closing: str = ''
    ) -> Tuple[int, List[str]]:
        """Collect lines until fi/done/closing brace."""
        body: List[str] = []
        close_words = {'fi', 'done', '}'}
        if closing:
            close_words = {closing}
        depth = 0
        open_words = {'if', 'for', 'while', 'function'}
        i = start
        while i < end:
            stripped = lines[i].strip()
            word0 = stripped.split()[0] if stripped.split() else ''
            if word0 in open_words:
                depth += 1
            if stripped in close_words or (stripped.rstrip(';') in close_words):
                if depth == 0:
                    return i + 1, body
                depth -= 1
            body.append(lines[i])
            i += 1
        return i, body

    def _exec_if(self, lines: List[str], i: int, end: int) -> Tuple[int, int]:
        line = lines[i].strip()
        # parse condition from "if <cond>; then"
        m = re.match(r'^if (.+?)(?:;?\s*then)?\s*$', line)
        cond_str = m.group(1).strip() if m else ''
        i += 1

        # skip optional 'then' line
        if i < end and lines[i].strip() in ('then', ''):
            i += 1

        # collect if-body
        i, if_body = self._collect_block(lines, i, end, closing='fi')

        # check for elif / else by scanning backward
        # (simplified: just collect then look for else/elif markers inside)
        else_body: List[str] = []
        for j, bl in enumerate(if_body):
            if bl.strip().startswith('else'):
                else_body = if_body[j + 1:]
                if_body = if_body[:j]
                break
            if bl.strip().startswith('elif '):
                # treat remaining as new block
                else_body = if_body[j:]
                if_body = if_body[:j]
                break

        cond_expanded = _expand_vars(cond_str, self.local_vars)
        cond_code = self._eval_condition(cond_expanded)

        if cond_code == 0:
            _, code = self._exec_block(if_body, 0, len(if_body))
        elif else_body:
            first = else_body[0].strip()
            if first.startswith('elif '):
                # recurse: patch into a fake 'if' block
                fake = [first[2:]] + else_body[1:]
                _, code = self._exec_if(fake, 0, len(fake))
            else:
                _, code = self._exec_block(else_body, 0, len(else_body))
        else:
            code = 0
        return i, code

    def _exec_for(self, lines: List[str], i: int, end: int) -> Tuple[int, int]:
        line = lines[i].strip()
        # for VAR in item1 item2...; do
        m = re.match(r'^for (\w+) in (.+?)(?:;\s*do)?\s*$', line)
        if not m:
            i += 1
            return i, 1
        var_name = m.group(1)
        items_str = _expand_vars(m.group(2), self.local_vars)
        items = items_str.split()
        i += 1
        if i < end and lines[i].strip() == 'do':
            i += 1
        i, body = self._collect_block(lines, i, end, closing='done')

        last_code = 0
        for item in items:
            self.local_vars[var_name] = item
            _, last_code = self._exec_block(body, 0, len(body))
            if self._return_flag:
                break
        return i, last_code

    def _exec_while(self, lines: List[str], i: int, end: int) -> Tuple[int, int]:
        line = lines[i].strip()
        m = re.match(r'^while (.+?)(?:;\s*do)?\s*$', line)
        cond_str = m.group(1).strip() if m else ''
        i += 1
        if i < end and lines[i].strip() == 'do':
            i += 1
        i, body = self._collect_block(lines, i, end, closing='done')

        last_code = 0
        iterations = 0
        while iterations < 10000:
            cond_expanded = _expand_vars(cond_str, self.local_vars)
            if self._eval_condition(cond_expanded) != 0:
                break
            _, last_code = self._exec_block(body, 0, len(body))
            if self._return_flag:
                break
            iterations += 1
        return i, last_code

    # ----------------------------------------------------------------
    # Condition evaluation
    # ----------------------------------------------------------------

    def _eval_condition(self, cond: str) -> int:
        """Return 0 (true) or 1 (false)."""
        cond = cond.strip()

        # [ ... ] test expression
        m = re.match(r'^\[\s+(.*?)\s+\]$', cond)
        if m:
            return self._test_expr(m.group(1))

        # [[ ... ]] extended test
        m = re.match(r'^\[\[\s+(.*?)\s+\]\]$', cond)
        if m:
            return self._test_expr(m.group(1))

        # Plain command
        return self._exec_line(cond)

    def _test_expr(self, expr: str) -> int:
        parts = expr.split()
        if len(parts) == 2:
            op, val = parts
            if op == '-z':
                return 0 if not val else 1
            if op == '-n':
                return 0 if val else 1
            if op in ('-f', '-e'):
                return 0 if os.path.exists(val) else 1
            if op == '-d':
                return 0 if os.path.isdir(val) else 1
        if len(parts) == 3:
            a, op, b = parts
            if op in ('=', '=='):
                return 0 if a == b else 1
            if op == '!=':
                return 0 if a != b else 1
            try:
                ai, bi = int(a), int(b)
                if op == '-eq':
                    return 0 if ai == bi else 1
                if op == '-ne':
                    return 0 if ai != bi else 1
                if op == '-lt':
                    return 0 if ai < bi else 1
                if op == '-le':
                    return 0 if ai <= bi else 1
                if op == '-gt':
                    return 0 if ai > bi else 1
                if op == '-ge':
                    return 0 if ai >= bi else 1
            except ValueError:
                pass
        return 1

    # ----------------------------------------------------------------
    # Single-line execution
    # ----------------------------------------------------------------

    def _exec_line(self, line: str) -> int:
        line = line.strip()
        if not line or line.startswith('#'):
            return 0

        # Call user-defined function
        parts = line.split(None, 1)
        if parts[0] in self.functions:
            fname = parts[0]
            func_args = parts[1].split() if len(parts) > 1 else []
            saved_vars = dict(self.local_vars)
            for i, a in enumerate(func_args, 1):
                self.local_vars[str(i)] = a
            _, code = self._exec_block(
                self.functions[fname], 0, len(self.functions[fname])
            )
            self.local_vars = saved_vars
            self._return_flag = False
            return code

        return self.shell.execute_line(line)


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def run_script(shell: 'XShell', path: str, args: List[str] | None = None) -> int:
    interp = ScriptInterpreter(shell)
    return interp.run_file(path, args)

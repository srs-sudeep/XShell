"""
XShell calc plugin — built-in.

Safe expression evaluator and unit converter using Python's ast module.
No arbitrary eval — only whitelisted operators, constants and functions.

Commands:
  calc <expression>         evaluate a math expression
  convert <val> <from> <to> convert between units
  hex2dec <hex>             hexadecimal → decimal
  dec2hex <int>             decimal → hexadecimal
  dec2bin <int>             decimal → binary
"""

import ast
import math
import operator
import sys
from typing import TYPE_CHECKING, List

from xshell.plugins.base import XShellPlugin

if TYPE_CHECKING:
    from xshell.core.shell import XShell


# ── Safe evaluator ────────────────────────────────────────────────────────────

_SAFE_CONSTANTS = {
    'pi':  math.pi,
    'e':   math.e,
    'tau': math.tau,
    'inf': math.inf,
}

_SAFE_FUNCTIONS = {
    'abs':     abs,
    'round':   round,
    'min':     min,
    'max':     max,
    'sum':     sum,
    'pow':     pow,
    'floor':   math.floor,
    'ceil':    math.ceil,
    'sqrt':    math.sqrt,
    'log':     math.log,
    'log2':    math.log2,
    'log10':   math.log10,
    'exp':     math.exp,
    'sin':     math.sin,
    'cos':     math.cos,
    'tan':     math.tan,
    'asin':    math.asin,
    'acos':    math.acos,
    'atan':    math.atan,
    'atan2':   math.atan2,
    'sinh':    math.sinh,
    'cosh':    math.cosh,
    'tanh':    math.tanh,
    'degrees': math.degrees,
    'radians': math.radians,
    'hypot':   math.hypot,
    'factorial': math.factorial,
    'gcd':     math.gcd,
    'lcm':     getattr(math, 'lcm', lambda a, b: abs(a * b) // math.gcd(a, b)),
    'hex':     hex,
    'bin':     bin,
    'oct':     oct,
}

_SAFE_OPS = {
    ast.Add:    operator.add,
    ast.Sub:    operator.sub,
    ast.Mult:   operator.mul,
    ast.Div:    operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod:    operator.mod,
    ast.Pow:    operator.pow,
    ast.UAdd:   operator.pos,
    ast.USub:   operator.neg,
    ast.BitAnd: operator.and_,
    ast.BitOr:  operator.or_,
    ast.BitXor: operator.xor,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.Invert: operator.invert,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f'unsupported constant: {node.value!r}')
    if isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[node.id]
        raise ValueError(f'unknown name: {node.id!r}')
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f'unsupported operator: {op_type.__name__}')
        return _SAFE_OPS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f'unsupported unary operator: {op_type.__name__}')
        return _SAFE_OPS[op_type](_safe_eval(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCTIONS:
            raise ValueError(f'unsupported function: {ast.dump(node.func)}')
        fn = _SAFE_FUNCTIONS[node.func.id]
        args = [_safe_eval(a) for a in node.args]
        return fn(*args)
    raise ValueError(f'unsupported expression type: {type(node).__name__}')


def calc_expr(expr: str):
    try:
        tree = ast.parse(expr.strip(), mode='eval')
        return _safe_eval(tree)
    except (SyntaxError, ValueError) as e:
        raise ValueError(str(e)) from e


# ── Unit conversion ───────────────────────────────────────────────────────────

# All values normalised to a base unit (metre, gram, second)
_LENGTH = {
    'mm': 1e-3, 'cm': 1e-2, 'm': 1.0, 'km': 1e3,
    'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144, 'mi': 1609.344,
}
_MASS = {
    'mg': 1e-3, 'g': 1.0, 'kg': 1e3, 't': 1e6,
    'oz': 28.3495, 'lb': 453.592, 'stone': 6350.29,
}
_TIME = {
    'ms': 1e-3, 's': 1.0, 'min': 60.0, 'hr': 3600.0,
    'day': 86400.0, 'week': 604800.0, 'yr': 31557600.0,
}
_TEMP_UNITS = {'c', 'f', 'k'}

_UNIT_TABLES = [_LENGTH, _MASS, _TIME]


def _convert_units(value: float, from_u: str, to_u: str) -> float:
    from_u = from_u.lower()
    to_u   = to_u.lower()

    # Temperature — special-cased
    if from_u in _TEMP_UNITS or to_u in _TEMP_UNITS:
        return _convert_temp(value, from_u, to_u)

    for table in _UNIT_TABLES:
        if from_u in table and to_u in table:
            return value * table[from_u] / table[to_u]

    raise ValueError(f"unknown or incompatible units: '{from_u}' → '{to_u}'")


def _convert_temp(value: float, from_u: str, to_u: str) -> float:
    # Normalise to Celsius first
    if from_u == 'c':
        celsius = value
    elif from_u == 'f':
        celsius = (value - 32) * 5 / 9
    elif from_u == 'k':
        celsius = value - 273.15
    else:
        raise ValueError(f"unknown temperature unit '{from_u}'")

    if to_u == 'c':
        return celsius
    if to_u == 'f':
        return celsius * 9 / 5 + 32
    if to_u == 'k':
        return celsius + 273.15
    raise ValueError(f"unknown temperature unit '{to_u}'")


# ── Plugin class ──────────────────────────────────────────────────────────────

class CalcPlugin(XShellPlugin):
    name        = 'calc'
    description = 'Safe calculator + unit converter — calc, convert, hex2dec, dec2hex'
    version     = '1.0.0'
    author      = 'XShell'

    def on_load(self, shell: 'XShell') -> None:
        super().on_load(shell)
        self.register_command('calc',    self._calc)
        self.register_command('convert', self._convert)
        self.register_command('hex2dec', self._hex2dec)
        self.register_command('dec2hex', self._dec2hex)
        self.register_command('dec2bin', self._dec2bin)

    def _calc(self, shell: 'XShell', args: List[str]) -> int:
        if len(args) < 2:
            print('Usage: calc <expression>', file=sys.stderr)
            return 1
        expr = ' '.join(args[1:])
        try:
            result = calc_expr(expr)
            # Pretty-print: strip trailing .0 for whole floats
            if isinstance(result, float) and result == int(result) and not math.isinf(result):
                print(int(result))
            else:
                print(result)
        except ValueError as e:
            print(f'calc: {e}', file=sys.stderr)
            return 1
        return 0

    def _convert(self, shell: 'XShell', args: List[str]) -> int:
        if len(args) != 4:
            print('Usage: convert <value> <from_unit> <to_unit>', file=sys.stderr)
            return 1
        try:
            value = float(args[1])
        except ValueError:
            print(f'convert: not a number: {args[1]}', file=sys.stderr)
            return 1
        try:
            result = _convert_units(value, args[2], args[3])
            print(f'{value:g} {args[2]} = {result:g} {args[3]}')
        except ValueError as e:
            print(f'convert: {e}', file=sys.stderr)
            return 1
        return 0

    def _hex2dec(self, shell: 'XShell', args: List[str]) -> int:
        if len(args) < 2:
            print('Usage: hex2dec <hex>', file=sys.stderr)
            return 1
        try:
            print(int(args[1], 16))
        except ValueError:
            print(f'hex2dec: invalid hex value: {args[1]}', file=sys.stderr)
            return 1
        return 0

    def _dec2hex(self, shell: 'XShell', args: List[str]) -> int:
        if len(args) < 2:
            print('Usage: dec2hex <integer>', file=sys.stderr)
            return 1
        try:
            print(hex(int(args[1])))
        except ValueError:
            print(f'dec2hex: invalid integer: {args[1]}', file=sys.stderr)
            return 1
        return 0

    def _dec2bin(self, shell: 'XShell', args: List[str]) -> int:
        if len(args) < 2:
            print('Usage: dec2bin <integer>', file=sys.stderr)
            return 1
        try:
            print(bin(int(args[1])))
        except ValueError:
            print(f'dec2bin: invalid integer: {args[1]}', file=sys.stderr)
            return 1
        return 0

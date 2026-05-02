"""
Command parser and tokenizer for XShell.
Handles pipes, redirects, semicolons, &&, ||, background (&), quotes, and escapes.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class TokenType(Enum):
    WORD = auto()
    PIPE = auto()
    REDIRECT_OUT = auto()     # >
    REDIRECT_APPEND = auto()  # >>
    REDIRECT_IN = auto()      # <
    BACKGROUND = auto()       # &
    SEMICOLON = auto()        # ;
    AND = auto()              # &&
    OR = auto()               # ||


@dataclass
class Token:
    type: TokenType
    value: str


@dataclass
class Command:
    args: List[str] = field(default_factory=list)
    stdin_file: Optional[str] = None
    stdout_file: Optional[str] = None
    stdout_append: bool = False
    background: bool = False

    @property
    def name(self) -> Optional[str]:
        return self.args[0] if self.args else None


@dataclass
class Pipeline:
    commands: List[Command] = field(default_factory=list)
    background: bool = False


@dataclass
class CommandList:
    # List of (Pipeline, connector) — connector is None|AND|OR|SEMICOLON
    pipelines: List[Tuple] = field(default_factory=list)


class CommandParser:
    def parse(self, line: str) -> CommandList:
        """Parse a raw input line into a CommandList."""
        line = line.strip()
        if not line or line.startswith('#'):
            return CommandList()
        tokens = self._tokenize(line)
        return self._parse_command_list(tokens)

    # ------------------------------------------------------------------
    # Tokenizer
    # ------------------------------------------------------------------

    def _tokenize(self, line: str) -> List[Token]:
        tokens: List[Token] = []
        chars = list(line)
        i = 0

        while i < len(chars):
            c = chars[i]

            if c in ' \t':
                i += 1
                continue

            if c == '|':
                if i + 1 < len(chars) and chars[i + 1] == '|':
                    tokens.append(Token(TokenType.OR, '||'))
                    i += 2
                else:
                    tokens.append(Token(TokenType.PIPE, '|'))
                    i += 1

            elif c == '&':
                if i + 1 < len(chars) and chars[i + 1] == '&':
                    tokens.append(Token(TokenType.AND, '&&'))
                    i += 2
                else:
                    tokens.append(Token(TokenType.BACKGROUND, '&'))
                    i += 1

            elif c == '>':
                if i + 1 < len(chars) and chars[i + 1] == '>':
                    tokens.append(Token(TokenType.REDIRECT_APPEND, '>>'))
                    i += 2
                else:
                    tokens.append(Token(TokenType.REDIRECT_OUT, '>'))
                    i += 1

            elif c == '<':
                tokens.append(Token(TokenType.REDIRECT_IN, '<'))
                i += 1

            elif c == ';':
                tokens.append(Token(TokenType.SEMICOLON, ';'))
                i += 1

            else:
                word, i = self._read_word(chars, i)
                tokens.append(Token(TokenType.WORD, word))

        return tokens

    def _read_word(self, chars: List[str], i: int) -> Tuple[str, int]:
        result = []
        while i < len(chars):
            c = chars[i]
            if c in ' \t|&>;<':
                break
            elif c in ('"', "'"):
                quote = c
                i += 1
                while i < len(chars) and chars[i] != quote:
                    if chars[i] == '\\' and quote == '"' and i + 1 < len(chars):
                        i += 1
                        result.append(chars[i])
                    else:
                        result.append(chars[i])
                    i += 1
                i += 1  # skip closing quote
            elif c == '\\' and i + 1 < len(chars):
                i += 1
                result.append(chars[i])
                i += 1
            else:
                result.append(c)
                i += 1
        return ''.join(result), i

    # ------------------------------------------------------------------
    # Tree builder
    # ------------------------------------------------------------------

    def _parse_command_list(self, tokens: List[Token]) -> CommandList:
        cmd_list = CommandList()
        current: List[Token] = []
        connector = None

        for token in tokens:
            if token.type in (TokenType.SEMICOLON, TokenType.AND, TokenType.OR):
                if current:
                    pipeline = self._parse_pipeline(current)
                    cmd_list.pipelines.append((pipeline, connector))
                    connector = token.type
                    current = []
            else:
                current.append(token)

        if current:
            pipeline = self._parse_pipeline(current)
            cmd_list.pipelines.append((pipeline, connector))

        return cmd_list

    def _parse_pipeline(self, tokens: List[Token]) -> Pipeline:
        pipeline = Pipeline()
        current: List[Token] = []
        background = False

        for token in tokens:
            if token.type == TokenType.PIPE:
                if current:
                    pipeline.commands.append(self._parse_command(current))
                    current = []
            elif token.type == TokenType.BACKGROUND:
                background = True
            else:
                current.append(token)

        if current:
            pipeline.commands.append(self._parse_command(current))

        pipeline.background = background
        return pipeline

    def _parse_command(self, tokens: List[Token]) -> Command:
        cmd = Command()
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.type == TokenType.REDIRECT_OUT:
                if i + 1 < len(tokens):
                    cmd.stdout_file = tokens[i + 1].value
                    cmd.stdout_append = False
                    i += 2
                else:
                    i += 1
            elif tok.type == TokenType.REDIRECT_APPEND:
                if i + 1 < len(tokens):
                    cmd.stdout_file = tokens[i + 1].value
                    cmd.stdout_append = True
                    i += 2
                else:
                    i += 1
            elif tok.type == TokenType.REDIRECT_IN:
                if i + 1 < len(tokens):
                    cmd.stdin_file = tokens[i + 1].value
                    i += 2
                else:
                    i += 1
            elif tok.type == TokenType.WORD:
                cmd.args.append(tok.value)
                i += 1
            else:
                i += 1
        return cmd

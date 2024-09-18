import re
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class LexicalError(BaseException):
    offset: int
    line: int
    col: int
    message: str


class TokenId(Enum):
    EOF = "EOF"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    EQUALS = "EQUALS"
    KW_TRUE = "KW_TRUE"
    KW_FALSE = "KW_FALSE"
    ID_NAME = "ID_NAME"
    LIT_NUM_DEC = "LIT_NUM_DEC"
    LIT_STRING = "LIT_STRING"


left_delimiter_to_right_delimiter = {
    TokenId.LPAREN: TokenId.RPAREN,
    TokenId.LBRACE: TokenId.RBRACE,
    TokenId.LBRACKET: TokenId.RBRACKET,
}

right_delimiters = set(left_delimiter_to_right_delimiter.values())


id_name_pattern = re.compile(r"[a-z_][a-zA-Z0-9'_]*#?")
lit_num_pattern = re.compile(r"-?[1-9][0-9]*(\.[0-9]+)?#?")
lit_string_pattern = re.compile(r'("(?!"").*?(?<!\\)(\\\\)*?")')


def is_word_char(c: str) -> bool:
    return c.isalnum() or c in "_#'"


@dataclass(frozen=True)
class Token:
    id: TokenId
    value: str
    offset: int
    size: int
    line: int
    col: int
    fabricated: bool = False
    error: bool = False


@dataclass
class BraceBlock:
    open_token: Token
    item_indentation: int | None = None


@dataclass
class LexicalAnalyzer:
    # Source to lex.
    source: str

    # Lexer position state.
    offset: int = 0
    line: int = 1
    col: int = 1

    # Right delimiters we expect to close, in order.
    open_delimiters: list[TokenId] = field(default_factory=list)

    # Records if we have yet to emit a token on the current line.
    first_token_on_line: bool = True

    # Records the indentation of the current line.
    line_indent: int = 0

    # Records the current brace block stack.
    brace_block_stack: list[BraceBlock] = field(default_factory=list)

    # The tokens we've emitted.
    tokens: list[Token] = field(default_factory=list)

    # Configuration.
    strict: bool = False

    def match_token(self, token_map: list[tuple[str, TokenId]], word: bool = False) -> Token | None:
        for token_str, token_id in token_map:
            if self.source.startswith(token_str, self.offset) and (
                not word
                or not is_word_char(
                    self.source[min(self.offset + len(token_str), len(self.source) - 1)]
                )
            ):
                token = Token(token_id, token_str, self.offset, len(token_str), self.line, self.col)
                self.offset += len(token_str)
                self.col += len(token_str)
                return token
        return None

    def emit_token(self, token: Token):
        """
        Emits a token, handling any extra token insertion logic.
        - Auto inserts matching right delimiters
        - Auto inserts semicolons where needed
        """

        # Right delimiter insertion logic.
        # Whenever we emit a left delimiter (i.e. one of "(", "{", "["), we push
        # the corresponding right delimiter to the open_delimiters stack.
        # Whenever we emit a right delimiter (i.e. one of ")", "}", "]"), we
        # check the top of the open_delimiters stack. If it doesn't match, we
        # emit "fabricated" right delimiters until the stack is empty or the
        # top of the stack matches the right delimiter.
        # Then we can emit the original token.
        # A similar process is performed for and open delimiters when we
        # encounter EOF.
        if token.id in left_delimiter_to_right_delimiter:
            # Push right delimiter to open_delimiters stack.
            right_delimiter = left_delimiter_to_right_delimiter[token.id]
            self.open_delimiters.append(right_delimiter)
        elif token.id in right_delimiters:
            # We have a right delimiter, so let's close any non-closed delimiters that don't match.
            if not self.strict:
                while self.open_delimiters and self.open_delimiters[-1] != token.id:
                    right_delimiter = self.open_delimiters.pop()
                    self.tokens.append(
                        Token(
                            right_delimiter,
                            "",
                            self.offset,
                            0,
                            self.line,
                            self.col,
                            fabricated=True,
                            error=True,
                        )
                    )
            # Pop the matching open delimiter.
            if self.open_delimiters:
                assert self.open_delimiters[-1] == token.id
                self.open_delimiters.pop()
        elif token.id == TokenId.EOF:
            # Close any open delimiters.
            while self.open_delimiters:
                right_delimiter = self.open_delimiters.pop()
                if right_delimiter == TokenId.RBRACE:
                    self.brace_block_stack.pop()
                self.tokens.append(
                    Token(
                        right_delimiter,
                        "",
                        self.offset,
                        0,
                        self.line,
                        self.col,
                        fabricated=True,
                        error=True,
                    )
                )

        # Core of semicolon insertion.
        # The grammar of the language uses semicolons to terminate attribute
        # definitions within blocks. However, we don't want to require the user
        # to have to actually provide them. Instead, a newline can terminate
        # an attribute definition and we can insert the semicolon for them.
        # Whenever we open a brace block (i.e. on emitting a "{" token), we
        # push a BraceBlock object to the brace_block_stack. This object
        # records the necessary information to determine if a semicolon
        # should be inserted.
        # Note: this occurs AFTER the right delimiter insertion logic.
        # FIXME: A closing brace fabricated by the lexer does not currently
        # interact with this logic.
        if token.id == TokenId.LBRACE:
            # Opening a brace block.
            self.brace_block_stack.append(BraceBlock(token))
        elif token.id == TokenId.RBRACE:
            # Closing a brace block.
            # Add a semicolon to end.
            if self.brace_block_stack:
                self.brace_block_stack.pop()
                # If the last token was already a semicolon, don't add another.
                if self.tokens[-1].id not in {TokenId.SEMICOLON, TokenId.RBRACE, TokenId.LBRACE}:
                    self.tokens.append(
                        Token(
                            TokenId.SEMICOLON,
                            "",
                            self.offset,
                            0,
                            self.line,
                            self.col,
                            fabricated=True,
                        )
                    )
        elif self.first_token_on_line and (self.tokens[-1].id not in {TokenId.RBRACE} if self.tokens else True):
            # If we're at the start of a line, we _may_ need to insert a
            # semicolon. Specifically if we're inside a brace block and the
            # token's indentation is <= the block's indentation.
            # When a brace block is first opened, it has no indentation. In
            # this case we set the indentation to the token's column.
            # If the previous token was a closing brace, we don't insert a
            # semicolon.
            # Otherwise, if the token's column is > the block's indentation,
            # we consider the current line to be an extension of the previous
            # line and don't insert a semicolon. (Offside rule)
            if self.brace_block_stack:
                if self.brace_block_stack[-1].item_indentation is None:
                    # In this case the top brace block has no indentation, so we set it.
                    self.brace_block_stack[-1].item_indentation = token.col
                elif (
                    token.col <= self.brace_block_stack[-1].item_indentation
                    and self.tokens[-1].id != TokenId.SEMICOLON
                ):  # Should this be == and auto-close on <?
                    self.tokens.append(
                        Token(
                            TokenId.SEMICOLON,
                            "",
                            self.offset,
                            0,
                            self.line,
                            self.col,
                            fabricated=True,
                        )
                    )

        # Finally we can add the original input token to the output.
        # The EOF token is special and is not actually added to the token list.
        if token.id != TokenId.EOF:
            self.tokens.append(token)

    def read_token(self) -> bool:
        while True:
            if self.offset >= len(self.source):
                self.emit_token(Token(TokenId.EOF, "", self.offset, 0, self.line, self.col))
                return False
            c = self.source[self.offset]
            if self.source.startswith("\r\n", self.offset):
                self.line += 1
                self.col = 1
                self.offset += 2
                self.first_token_on_line = True
            elif c in {"\r", "\n"}:
                self.line += 1
                self.col = 1
                self.offset += 1
                self.first_token_on_line = True
            elif c.isspace():
                self.offset += 1
                self.col += 1
            elif c == "#":
                # Comment, skip to end of line.
                # NOTE: We skip _to_ the end of the line, not past it.
                # Other rules will handle the newline.
                while self.offset < len(self.source) and self.source[self.offset] not in {"\r", "\n"}:
                    self.offset += 1
                    self.col += 1
            else:
                break

        if self.first_token_on_line:
            self.line_indent = self.col

        if tok := self.match_token(
            [
                ("(", TokenId.LPAREN),
                (")", TokenId.RPAREN),
                ("{", TokenId.LBRACE),
                ("}", TokenId.RBRACE),
                ("[", TokenId.LBRACKET),
                ("]", TokenId.RBRACKET),
                (",", TokenId.COMMA),
                (";", TokenId.SEMICOLON),
                ("=", TokenId.EQUALS),
            ]
        ):
            self.emit_token(tok)
        elif tok := self.match_token(
            [
                ("true", TokenId.KW_TRUE),
                ("false", TokenId.KW_FALSE),
            ],
            word=True,
        ):
            self.emit_token(tok)
        elif match := id_name_pattern.match(self.source, self.offset):
            size = len(match.group(0))
            self.emit_token(
                Token(TokenId.ID_NAME, match.group(0), self.offset, size, self.line, self.col)
            )
            self.offset += size
            self.col += size
        elif match := lit_num_pattern.match(self.source, self.offset):
            size = len(match.group(0))
            self.emit_token(
                Token(TokenId.LIT_NUM_DEC, match.group(0), self.offset, size, self.line, self.col)
            )
            self.offset += size
            self.col += size
        elif match := lit_string_pattern.match(self.source, self.offset):
            size = len(match.group(0))
            self.emit_token(
                Token(TokenId.LIT_STRING, match.group(0), self.offset, size, self.line, self.col)
            )
            self.offset += size
            self.col += size
        else:
            raise LexicalError(self.offset, self.line, self.col, f"Unexpected character {repr(self.source[self.offset])}")
        self.first_token_on_line = False
        return True


def rebuild_string(source: str, tokens: list[Token]) -> str:
    return "·".join(source[token.offset : token.offset + token.size] for token in tokens)


def tokenize(source: str) -> list[Token]:
    lexer = LexicalAnalyzer(source)
    while lexer.read_token():
        pass
    return lexer.tokens


def test(string: str) -> str:
    tokens = tokenize(string)
    return rebuild_string(string, tokens)


if __name__ == "__main__":
    import sys

    text = sys.stdin.read()
    toks = tokenize(text)
    for tok in toks:
        print(tok.value or tok.id.value)

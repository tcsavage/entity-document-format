from edf.block import Document
from edf.parser.build import build
from edf.parser.lex import tokenize
from edf.parser.parse import parse


def read_document(source: str) -> Document:
    return build(parse(tokenize(source)))


__all__ = ["read_document"]

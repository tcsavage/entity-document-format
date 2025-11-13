import pytest

from edf.parser.lex import LexicalError, tokenize, Token, TokenId

doc_simple_named = """\
named_block block_name {
    key1 = "value1"
    key2 = "value2"
}
"""

toks_simple_named = [
    Token(TokenId.ID_NAME, "named_block", 0, 11, 1, 1),
    Token(TokenId.ID_NAME, "block_name", 12, 10, 1, 13),
    Token(TokenId.LBRACE, "{", 23, 1, 1, 24),
    Token(TokenId.ID_NAME, "key1", 29, 4, 2, 5),
    Token(TokenId.EQUALS, "=", 34, 1, 2, 10),
    Token(TokenId.LIT_STRING, '"value1"', 36, 8, 2, 12),
    Token(TokenId.SEMICOLON, "", 49, 0, 3, 5, fabricated=True),
    Token(TokenId.ID_NAME, "key2", 49, 4, 3, 5),
    Token(TokenId.EQUALS, "=", 54, 1, 3, 10),
    Token(TokenId.LIT_STRING, '"value2"', 56, 8, 3, 12),
    Token(TokenId.SEMICOLON, "", 66, 0, 4, 2, fabricated=True),
    Token(TokenId.RBRACE, "}", 65, 1, 4, 1),
]

doc_simple_anon = """\
anon_block {
    key1 = "value1"
    key2 = "value2"
}
"""

toks_simple_anon = [
    Token(TokenId.ID_NAME, "anon_block", 0, 10, 1, 1),
    Token(TokenId.LBRACE, "{", 11, 1, 1, 12),
    Token(TokenId.ID_NAME, "key1", 17, 4, 2, 5),
    Token(TokenId.EQUALS, "=", 22, 1, 2, 10),
    Token(TokenId.LIT_STRING, '"value1"', 24, 8, 2, 12),
    Token(TokenId.SEMICOLON, "", 37, 0, 3, 5, fabricated=True),
    Token(TokenId.ID_NAME, "key2", 37, 4, 3, 5),
    Token(TokenId.EQUALS, "=", 42, 1, 3, 10),
    Token(TokenId.LIT_STRING, '"value2"', 44, 8, 3, 12),
    Token(TokenId.SEMICOLON, "", 54, 0, 4, 2, fabricated=True),
    Token(TokenId.RBRACE, "}", 53, 1, 4, 1),
]

doc_simple_value = """\
anon_block {
    "value"
}
"""

toks_simple_value = [
    Token(TokenId.ID_NAME, "anon_block", 0, 10, 1, 1),
    Token(TokenId.LBRACE, "{", 11, 1, 1, 12),
    Token(TokenId.LIT_STRING, '"value"', 17, 7, 2, 5),
    Token(TokenId.SEMICOLON, "", 26, 0, 3, 2, fabricated=True),
    Token(TokenId.RBRACE, "}", 25, 1, 3, 1),
]

doc_nested = """\
anon_block {
    key1 = "value1"
    key2 = "value2"
    
    nested_block block_name {
        key3 = "value3"
        key4 = "value4"
    }

    nested_anon_block {
        key5 = "value5"
        key6 = "value6"
    }
}
"""

toks_nested = [
    Token(TokenId.ID_NAME, "anon_block", 0, 10, 1, 1),
    Token(TokenId.LBRACE, "{", 11, 1, 1, 12),
    Token(TokenId.ID_NAME, "key1", 17, 4, 2, 5),
    Token(TokenId.EQUALS, "=", 22, 1, 2, 10),
    Token(TokenId.LIT_STRING, '"value1"', 24, 8, 2, 12),
    Token(TokenId.SEMICOLON, "", 37, 0, 3, 5, fabricated=True),
    Token(TokenId.ID_NAME, "key2", 37, 4, 3, 5),
    Token(TokenId.EQUALS, "=", 42, 1, 3, 10),
    Token(TokenId.LIT_STRING, '"value2"', 44, 8, 3, 12),
    Token(TokenId.SEMICOLON, "", 62, 0, 5, 5, fabricated=True),
    Token(TokenId.ID_NAME, "nested_block", 62, 12, 5, 5),
    Token(TokenId.ID_NAME, "block_name", 75, 10, 5, 18),
    Token(TokenId.LBRACE, "{", 86, 1, 5, 29),
    Token(TokenId.ID_NAME, "key3", 96, 4, 6, 9),
    Token(TokenId.EQUALS, "=", 101, 1, 6, 14),
    Token(TokenId.LIT_STRING, '"value3"', 103, 8, 6, 16),
    Token(TokenId.SEMICOLON, "", 120, 0, 7, 9, fabricated=True),
    Token(TokenId.ID_NAME, "key4", 120, 4, 7, 9),
    Token(TokenId.EQUALS, "=", 125, 1, 7, 14),
    Token(TokenId.LIT_STRING, '"value4"', 127, 8, 7, 16),
    Token(TokenId.SEMICOLON, "", 141, 0, 8, 6, fabricated=True),
    Token(TokenId.RBRACE, "}", 140, 1, 8, 5),
    Token(TokenId.ID_NAME, "nested_anon_block", 147, 17, 10, 5),
    Token(TokenId.LBRACE, "{", 165, 1, 10, 23),
    Token(TokenId.ID_NAME, "key5", 175, 4, 11, 9),
    Token(TokenId.EQUALS, "=", 180, 1, 11, 14),
    Token(TokenId.LIT_STRING, '"value5"', 182, 8, 11, 16),
    Token(TokenId.SEMICOLON, "", 199, 0, 12, 9, fabricated=True),
    Token(TokenId.ID_NAME, "key6", 199, 4, 12, 9),
    Token(TokenId.EQUALS, "=", 204, 1, 12, 14),
    Token(TokenId.LIT_STRING, '"value6"', 206, 8, 12, 16),
    Token(TokenId.SEMICOLON, "", 220, 0, 13, 6, fabricated=True),
    Token(TokenId.RBRACE, "}", 219, 1, 13, 5),
    Token(TokenId.RBRACE, "}", 221, 1, 14, 1),
]

doc_explicit_semis = """\
anon_block {
    key1 = "value1";
    key2 = "value2";
}
"""

toks_explicit_semis = [
    Token(TokenId.ID_NAME, "anon_block", 0, 10, 1, 1),
    Token(TokenId.LBRACE, "{", 11, 1, 1, 12),
    Token(TokenId.ID_NAME, "key1", 17, 4, 2, 5),
    Token(TokenId.EQUALS, "=", 22, 1, 2, 10),
    Token(TokenId.LIT_STRING, '"value1"', 24, 8, 2, 12),
    Token(TokenId.SEMICOLON, ";", 32, 1, 2, 20),
    Token(TokenId.ID_NAME, "key2", 38, 4, 3, 5),
    Token(TokenId.EQUALS, "=", 43, 1, 3, 10),
    Token(TokenId.LIT_STRING, '"value2"', 45, 8, 3, 12),
    Token(TokenId.SEMICOLON, ";", 53, 1, 3, 20),
    Token(TokenId.RBRACE, "}", 55, 1, 4, 1),
]

doc_explicit_semis_missing_final = """\
anon_block {
    key1 = "value1";
    key2 = "value2"
}
"""

toks_explicit_semis_missing_final = [
    Token(TokenId.ID_NAME, "anon_block", 0, 10, 1, 1),
    Token(TokenId.LBRACE, "{", 11, 1, 1, 12),
    Token(TokenId.ID_NAME, "key1", 17, 4, 2, 5),
    Token(TokenId.EQUALS, "=", 22, 1, 2, 10),
    Token(TokenId.LIT_STRING, '"value1"', 24, 8, 2, 12),
    Token(TokenId.SEMICOLON, ";", 32, 1, 2, 20),
    Token(TokenId.ID_NAME, "key2", 38, 4, 3, 5),
    Token(TokenId.EQUALS, "=", 43, 1, 3, 10),
    Token(TokenId.LIT_STRING, '"value2"', 45, 8, 3, 12),
    Token(TokenId.SEMICOLON, "", 55, 0, 4, 2, fabricated=True),
    Token(TokenId.RBRACE, "}", 54, 1, 4, 1),
]

doc_one_liner = """named_block block_name { key1 = "value1"; key2 = "value2" }"""

toks_one_liner = [
    Token(TokenId.ID_NAME, "named_block", 0, 11, 1, 1),
    Token(TokenId.ID_NAME, "block_name", 12, 10, 1, 13),
    Token(TokenId.LBRACE, "{", 23, 1, 1, 24),
    Token(TokenId.ID_NAME, "key1", 25, 4, 1, 26),
    Token(TokenId.EQUALS, "=", 30, 1, 1, 31),
    Token(TokenId.LIT_STRING, '"value1"', 32, 8, 1, 33),
    Token(TokenId.SEMICOLON, ";", 40, 1, 1, 41),
    Token(TokenId.ID_NAME, "key2", 42, 4, 1, 43),
    Token(TokenId.EQUALS, "=", 47, 1, 1, 48),
    Token(TokenId.LIT_STRING, '"value2"', 49, 8, 1, 50),
    Token(TokenId.SEMICOLON, "", 59, 0, 1, 60, fabricated=True),
    Token(TokenId.RBRACE, "}", 58, 1, 1, 59),
]

doc_whitespace_comments = """\
# This is a comment
named_block block_name{

    # This is another comment
    key1  ="value1"

    key2=   "value2"

}


"""

toks_whitespace_comments = [
    Token(TokenId.ID_NAME, "named_block", 20, 11, 2, 1),
    Token(TokenId.ID_NAME, "block_name", 32, 10, 2, 13),
    Token(TokenId.LBRACE, "{", 42, 1, 2, 23),
    Token(TokenId.ID_NAME, "key1", 79, 4, 5, 5),
    Token(TokenId.EQUALS, "=", 85, 1, 5, 11),
    Token(TokenId.LIT_STRING, '"value1"', 86, 8, 5, 12),
    Token(TokenId.SEMICOLON, "", 100, 0, 7, 5, fabricated=True),
    Token(TokenId.ID_NAME, "key2", 100, 4, 7, 5),
    Token(TokenId.EQUALS, "=", 104, 1, 7, 9),
    Token(TokenId.LIT_STRING, '"value2"', 108, 8, 7, 13),
    Token(TokenId.SEMICOLON, "", 119, 0, 9, 2, fabricated=True),
    Token(TokenId.RBRACE, "}", 118, 1, 9, 1),
]

doc_multi_line_attr = """\
named_block block_name {
    key1 = "value1"
    key2 =
        "value2"
}
"""

toks_multi_line_attr = [
    Token(TokenId.ID_NAME, "named_block", 0, 11, 1, 1),
    Token(TokenId.ID_NAME, "block_name", 12, 10, 1, 13),
    Token(TokenId.LBRACE, "{", 23, 1, 1, 24),
    Token(TokenId.ID_NAME, "key1", 29, 4, 2, 5),
    Token(TokenId.EQUALS, "=", 34, 1, 2, 10),
    Token(TokenId.LIT_STRING, '"value1"', 36, 8, 2, 12),
    Token(TokenId.SEMICOLON, "", 49, 0, 3, 5, fabricated=True),
    Token(TokenId.ID_NAME, "key2", 49, 4, 3, 5),
    Token(TokenId.EQUALS, "=", 54, 1, 3, 10),
    Token(TokenId.LIT_STRING, '"value2"', 64, 8, 4, 9),
    Token(TokenId.SEMICOLON, "", 74, 0, 5, 2, fabricated=True),
    Token(TokenId.RBRACE, "}", 73, 1, 5, 1),
]


@pytest.mark.parametrize(
    "text, expected",
    [
        (doc_simple_named, toks_simple_named),
        (doc_simple_anon, toks_simple_anon),
        (doc_simple_value, toks_simple_value),
        (doc_nested, toks_nested),
        (doc_explicit_semis, toks_explicit_semis),
        (doc_explicit_semis_missing_final, toks_explicit_semis_missing_final),
        (doc_one_liner, toks_one_liner),
        (doc_whitespace_comments, toks_whitespace_comments),
        (doc_multi_line_attr, toks_multi_line_attr),
    ],
)
def test_tokenize(text, expected):
    toks = tokenize(text)

    assert toks == expected


@pytest.mark.parametrize(
    "input",
    [
        "ab?cd",
        '"abc',
    ]
)
def test_tokenize_invalid(input):
    with pytest.raises(LexicalError):
        tokenize(input)

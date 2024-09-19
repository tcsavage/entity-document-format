import pytest

from edf.lex import tokenize
from edf.parse import NodeId, parse


doc_simple_named = """\
named_block block_name {
    key1 = "value1"
    key2 = "value2"
}
"""

node_ids_simple_named = [
    NodeId.BLOCK_INTRODUCER,
    NodeId.BLOCK_ID,
    NodeId.BLOCK_BODY_START,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.BLOCK
]

doc_simple_anon = """\
anon_block {
    key1 = "value1"
    key2 = "value2"
}
"""

node_ids_simple_anon = [
    NodeId.BLOCK_INTRODUCER,
    NodeId.BLOCK_BODY_START,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.BLOCK
]

doc_simple_value = """\
anon_block {
    "value"
}
"""

node_ids_simple_value = [
    NodeId.BLOCK_INTRODUCER,
    NodeId.BLOCK_BODY_START,
    NodeId.LIT_STRING,
    NodeId.BLOCK
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

node_ids_nested = [
    NodeId.BLOCK_INTRODUCER,
    NodeId.BLOCK_BODY_START,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.BLOCK_INTRODUCER,
    NodeId.BLOCK_ID,
    NodeId.BLOCK_BODY_START,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.BLOCK,
    NodeId.BLOCK_INTRODUCER,
    NodeId.BLOCK_BODY_START,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.ATTRIBUTE_INTRODUCER,
    NodeId.ATTRIBUTE_ASSIGNMENT,
    NodeId.LIT_STRING,
    NodeId.ATTRIBUTE,
    NodeId.BLOCK,
    NodeId.BLOCK
]


@pytest.mark.parametrize(
    "doc, node_ids",
    [
        (doc_simple_named, node_ids_simple_named),
        (doc_simple_anon, node_ids_simple_anon),
        (doc_simple_value, node_ids_simple_value),
        (doc_nested, node_ids_nested),
    ],
)
def test_build(doc, node_ids):
    tokens = tokenize(doc)
    tree = parse(tokens)
    assert [node.kind.id for node in tree] == node_ids
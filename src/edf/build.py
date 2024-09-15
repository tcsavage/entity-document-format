from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from edf.block import Block, Document
from edf.parse import Node, NodeId


@dataclass
class StackElem:
    node: Node
    value: Any = None


def build(parse_tree: Sequence[Node]) -> Document:
    stack: list[StackElem] = []

    for node in parse_tree:
        match node.kind.id:
            case NodeId.ATTRIBUTE_INTRODUCER:
                stack.append(StackElem(node, node.token.value))
            case NodeId.LIT_STRING:
                stack.append(StackElem(node, eval(node.token.value))) # FIXME: proper string unescaping
            case NodeId.LIT_NUMBER:
                s = node.token.value
                if "." in s:
                    value = float(s)
                else:
                    value = int(s)
                stack.append(StackElem(node, value))
            case NodeId.ATTRIBUTE:
                idx = -1
                while stack[idx].node.kind.id != NodeId.ATTRIBUTE_INTRODUCER:
                    idx -= 1
                children = stack[idx:]
                stack = stack[:idx]
                assert len(children) == 3
                attribute_name = children[0].value
                attribute_value = children[2].value
                stack.append(StackElem(node, (attribute_name, attribute_value)))
            case NodeId.BLOCK_INTRODUCER:
                stack.append(StackElem(node, node.token.value))
            case NodeId.BLOCK_ID:
                stack.append(StackElem(node, node.token.value))
            case NodeId.BLOCK:
                idx = -1
                while stack[idx].node.kind.id != NodeId.BLOCK_INTRODUCER:
                    idx -= 1
                
                # Get children
                children = stack[idx:]
                stack = stack[:idx]

                # Ensure we have at least the kind and body start
                assert len(children) >= 2 # At least a kind and body start

                # Get kind
                kind, *children = children
                kind = kind.value

                # Get block id if present
                if children[0].node.kind.id == NodeId.BLOCK_ID:
                    block_id, *children = children
                    block_id = block_id.value
                else:
                    block_id = None

                # Ensure the next node is the body start
                assert children[0].node.kind.id == NodeId.BLOCK_BODY_START
                children = children[1:]

                # Get attributes and blocks.
                attributes = {}
                for child in children:
                    if child.node.kind.id == NodeId.ATTRIBUTE:
                        name, value = child.value
                        attributes[name] = value
                    else:
                        raise ValueError(f"Unexpected node in block body: {child.node.kind.id}")
                
                # Create block
                block = Block(kind, block_id, attributes=attributes)
                stack.append(StackElem(node, block))
            case _:
                stack.append(StackElem(node))

    assert all(isinstance(elem.value, Block) for elem in stack), "Expected all root-level elements to be blocks"

    return [elem.value for elem in stack]
                

if __name__ == "__main__":
    import pprint
    import sys

    from edf.lex import tokenize
    from edf.parse import parse

    text = sys.stdin.read()
    toks = tokenize(text)
    parse_tree = parse(toks)
    doc = build(parse_tree)

    pprint.pprint(doc)

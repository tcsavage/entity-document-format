"""
Functions for representing EDF documents using JSON data (objects and arrays) in a canonical form.
"""

from typing import Any
from edf.block import Block, Document


def canonicalize_block_json(block: Block) -> Any:
    return {
        "$kind": block.kind,
        "$name": block.name,
        "$children": [canonicalize_block_json(child) for child in block.children],
        **block.attributes,
    }


def canonicalize_json(doc: Document) -> Any:
    return [canonicalize_block_json(block) for block in doc]

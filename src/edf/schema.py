from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union

from edf.block import Block, Document


@dataclass
class AttributeSchema:
    name: str
    type: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None


@dataclass
class SubBlockSchema:
    field: str
    block: Union["BlockSchema", Callable[[], "BlockSchema"]]
    multiplicity: Literal["one", "many"] = "many"


@dataclass
class BlockSchema:
    kind: str
    aliases: list[str] = field(default_factory=list)
    anonymous: bool = False
    attributes: list[AttributeSchema] = field(default_factory=list)
    sub_blocks: list[SubBlockSchema] = field(default_factory=list)


@dataclass
class Schema:
    blocks: list[BlockSchema] = field(default_factory=list)


block_schema = BlockSchema(
    kind="block",
    anonymous=False,
    attributes=[
        AttributeSchema(name="kind", type="string", required=True),
        AttributeSchema(name="aliases", default=None),
        AttributeSchema(name="anonymous", type="boolean", default=False),
    ],
    sub_blocks=[
        SubBlockSchema(
            field="attributes",
            multiplicity="many",
            block=BlockSchema(
                kind="attribute",
                attributes=[
                    AttributeSchema(name="name", type="string", required=True),
                    AttributeSchema(name="type"),
                    AttributeSchema(name="required", type="boolean", default=False),
                    AttributeSchema(name="default"),
                ],
            ),
        ),
        SubBlockSchema(
            field="sub_blocks",
            multiplicity="many",
            block=BlockSchema(
                kind="sub_block",
                attributes=[
                    AttributeSchema(name="field", type="string", required=True),
                    AttributeSchema(name="multiplicity", type="string", default="many"),
                ],
                sub_blocks=[
                    SubBlockSchema(field="block", multiplicity="one", block=lambda: block_schema)
                ],
            ),
        ),
    ],
)


schema_schema = Schema(blocks=[block_schema])


def analyze_schema_block(block: Block) -> BlockSchema | AttributeSchema | SubBlockSchema:
    if block.kind == "block":
        if block.name is None:
            raise ValueError("Block name required")
        if block.value:
            raise ValueError("Block value not supported")
        kind = block.name
        aliases = block.attributes["aliases"] if "aliases" in block.attributes else []
        anonymous = block.attributes.get("anonymous", False)
        attribute_schemas = []
        sub_block_schemas = []
        for child in block.children:
            analyzed_child = analyze_schema_block(child)
            if isinstance(analyzed_child, AttributeSchema):
                attribute_schemas.append(analyzed_child)
            elif isinstance(analyzed_child, SubBlockSchema):
                sub_block_schemas.append(analyzed_child)
            else:
                raise ValueError(f"Unexpected child block: {child}")
        return BlockSchema(
            kind=kind,
            aliases=aliases,
            anonymous=anonymous,
            attributes=attribute_schemas,
            sub_blocks=sub_block_schemas,
        )

    elif block.kind == "attribute":
        if block.name is None:
            raise ValueError("Attribute name required")
        if block.value:
            raise ValueError("Attribute value not supported")
        name = block.name
        type_ = block.attributes.get("type")
        required = block.attributes.get("required", False)
        default = block.attributes.get("default")
        return AttributeSchema(
            name=name,
            type=type_,
            required=required,
            default=default,
        )
    elif block.kind == "sub_block":
        if block.name is not None:
            raise ValueError("Sub-block name not supported")
        if block.value:
            raise ValueError("Sub-block value not supported")
        field = block.attributes["field"]
        multiplicity = (
            block.attributes["multiplicity"] if "multiplicity" in block.attributes else "many"
        )
        if not block.children:
            raise ValueError("Sub-block missing block schema")
        child_block = block.children[0]
        if child_block.kind != "block":
            raise ValueError(f"Unexpected child block kind: {child_block.kind}")
        child_block_schema = analyze_schema_block(child_block)
        assert isinstance(child_block_schema, BlockSchema)
        return SubBlockSchema(
            field=field,
            multiplicity=multiplicity,
            block=child_block_schema,
        )
    else:
        raise ValueError(f"Unexpected block kind: {block.kind}")


def analyze_schema_document(doc: Document) -> Schema:
    blocks = [analyze_schema_block(block) for block in doc]
    if not all(isinstance(block, BlockSchema) for block in blocks):
        raise ValueError("Schema document must contain only block schemas at root")
    return Schema(
        blocks=blocks  # type: ignore
    )

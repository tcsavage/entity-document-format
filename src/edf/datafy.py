from dataclasses import dataclass, field
from edf.block import Block, Document
from edf.schema import AttributeSchema, BlockSchema, Schema, SubBlockSchema


@dataclass
class BlockSchemaContext:
    blocks: dict[str, tuple[SubBlockSchema, BlockSchema]]
    attributes: dict[str, AttributeSchema] = field(default_factory=dict)
    required_attributes: set[str] = field(default_factory=set)

    @classmethod
    def from_schema(cls, schema: Schema) -> "BlockSchemaContext":
        blocks = {}
        for block in schema.blocks:
            blocks[block.kind] = (None, block)
            if block.aliases:
                for alias in block.aliases:
                    blocks[alias] = (None, block)
        return cls(blocks=blocks)

    @classmethod
    def from_block_schema(cls, block: BlockSchema) -> "BlockSchemaContext":
        attributes = {}
        required_attributes = set()
        blocks = {}
        for attribute in block.attributes:
            attributes[attribute.name] = attribute
            if attribute.required:
                required_attributes.add(attribute.name)
        for sub_block in block.sub_blocks:
            if callable(sub_block.block):
                block = sub_block.block()
            else:
                block = sub_block.block
            blocks[block.kind] = (sub_block, block)
            if block.aliases:
                for alias in block.aliases:
                    blocks[alias] = (sub_block, block)
        return cls(blocks=blocks, attributes=attributes, required_attributes=required_attributes)


def datafy_block(schema: BlockSchema, block: Block) -> dict:
    assert block.kind == schema.kind or block.kind in schema.aliases
    ctx = BlockSchemaContext.from_block_schema(schema)

    # The output dict we're building.
    data = {}

    # Set ID field.
    if schema.anonymous and block.name:
        raise ValueError("Anonymous block has a name")
    elif not schema.anonymous and not block.name:
        raise ValueError("Named block is missing a name")
    elif block.name:
        data["id"] = block.name

    # Process attributes.
    for k, v in block.attributes.items():
        attribute_schema = ctx.attributes.get(k)
        if attribute_schema is not None:
            if attribute_schema.type:
                if attribute_schema.type == "string":
                    if not isinstance(v, str):
                        raise ValueError(f"Expected string for attribute {k}")
                elif attribute_schema.type == "number":
                    if not isinstance(v, (int, float)):
                        raise ValueError(f"Expected number for attribute {k}")
                elif attribute_schema.type == "boolean":
                    if not isinstance(v, bool):
                        raise ValueError(f"Expected boolean for attribute {k}")
                else:
                    raise ValueError(f"Unexpected attribute type: {attribute_schema.type}")
        else:
            raise ValueError(f"Unexpected attribute: {k}")
        data[k] = v

    # Check required attributes and set defaults.
    for k in ctx.required_attributes:
        if k not in data:
            attribute_schema = ctx.attributes[k]
            if attribute_schema.default is not None:
                data[k] = attribute_schema.default
            else:
                raise ValueError(f"Missing required attribute: {k}")

    # Initialize sub-block fields.
    for sub_block in schema.sub_blocks:
        if sub_block.field in data:
            raise ValueError(f"Duplicate sub-block field: {sub_block.field}")
        if sub_block.multiplicity == "one":
            data[sub_block.field] = None
        elif sub_block.multiplicity == "many":
            data[sub_block.field] = []
        else:
            raise ValueError(f"Unexpected multiplicity: {sub_block.multiplicity}")

    # Process sub-blocks.
    for child in block.children:
        if child.kind not in ctx.blocks:
            raise ValueError(f"Unexpected child block: {child.kind}")
        sub_block_schema, child_schema = ctx.blocks[child.kind]
        k = sub_block_schema.field
        if sub_block_schema.multiplicity == "one" and data[k] is not None:
            raise ValueError(f"Duplicate child with multiplicity of one: {k}")
        child_data = datafy_block(child_schema, child)
        if sub_block_schema.multiplicity == "one":
            data[k] = child_data
        elif sub_block_schema.multiplicity == "many":
            data[k].append(child_data)
        else:
            raise ValueError(f"Unexpected multiplicity: {sub_block_schema.multiplicity}")

    return data


def datafy_document(schema: Schema, document: Document) -> list:
    ctx = BlockSchemaContext.from_schema(schema)
    return [datafy_block(ctx.blocks[block.kind][1], block) for block in document]

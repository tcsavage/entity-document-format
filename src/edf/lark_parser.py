from lark import Lark, Transformer, v_args

from edf.block import Block

# Load grammar from file
parser = Lark.open_from_package(__name__, "grammar.lark", start="document")


class EDFTransformer(Transformer):
    def document(self, children):
        return list(children)
    
    @v_args(inline=True)
    def value_string(self, tok):
        # FIXME: Unsafe parsing of Python-style string
        return eval(tok.value)
    
    @v_args(inline=True)
    def value_number(self, tok):
        if "." in tok.value:
            return float(tok.value)
        return int(tok.value)
    
    def block_head(self, children):
        if len(children) == 1:
            return children[0].value, None
        else:
            return children[0].value, children[1].value
    
    def block_body_single_value(self, children):
        return children[0]
    
    @v_args(inline=True)
    def block_entry_kv(self, key, value):
        return key.value, value
    
    @v_args(inline=True)
    def block_entry_block(self, block):
        return block

    def block_body_entries(self, children):
        kvs = {}
        blocks = []
        for child in children:
            if isinstance(child, tuple):
                kvs[child[0]] = child[1]
            elif isinstance(child, Block):
                blocks.append(child)
            else:
                raise ValueError(f"Unexpected child: {child}")
        return kvs, blocks

    @v_args(inline=True)
    def block(self, head, body):
        kind, name = head
        if isinstance(body, tuple):
            attrs, children = body
            block = Block(kind, name, attributes=attrs, children=children)
        else:
            block = Block(kind, name, value=body)
        return block
    

def parse(source):
    return parser.parse(source)
    

def transform(tree):
    return EDFTransformer().transform(tree)


def read(source):
    return transform(parse(source))


if __name__ == "__main__":
    from pprint import pprint
    import sys
    source = sys.stdin.read()
    parse_tree = parser.parse(source)
    print(parse_tree.pretty())
    doc = transform(parse_tree)
    pprint(doc)

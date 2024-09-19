from collections.abc import Container, MutableSequence, Sequence, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from edf.lex import Token, TokenId


class NodeId(Enum):
    BLOCK_INTRODUCER = "BLOCK_INTRODUCER"
    BLOCK_ID = "BLOCK_ID"
    BLOCK_BODY_START = "BLOCK_BODY_START"
    BLOCK = "BLOCK"
    ATTRIBUTE_INTRODUCER = "ATTRIBUTE_INTRODUCER"
    ATTRIBUTE_ASSIGNMENT = "ATTRIBUTE_ASSIGNMENT"
    ATTRIBUTE = "ATTRIBUTE"
    LIT_STRING = "LIT_STRING"
    LIT_NUMBER = "LIT_NUMBER"


@dataclass
class NodeKind:
    id: NodeId
    fixed_num_children: Optional[int] = 0
    bracket: Optional["NodeKind"] = None

    def __post_init__(self):
        if self.bracket is not None and self.fixed_num_children == 0:
            self.fixed_num_children = None
        if self.fixed_num_children is None and self.bracket is None:
            raise ValueError("Must specify either fixed_num_children or bracket")
        if self.fixed_num_children is not None and self.bracket is not None:
            raise ValueError("Cannot specify both fixed_num_children and bracket")
        

node_block_introducer = NodeKind(NodeId.BLOCK_INTRODUCER)
node_block_id = NodeKind(NodeId.BLOCK_ID)
node_block_body_start = NodeKind(NodeId.BLOCK_BODY_START)
node_block = NodeKind(NodeId.BLOCK, bracket=node_block_introducer)

node_attribute_introducer = NodeKind(NodeId.ATTRIBUTE_INTRODUCER)
node_attribute_assignment = NodeKind(NodeId.ATTRIBUTE_ASSIGNMENT)
node_attribute = NodeKind(NodeId.ATTRIBUTE, bracket=node_attribute_introducer)

node_lit_string = NodeKind(NodeId.LIT_STRING)
node_lit_number = NodeKind(NodeId.LIT_NUMBER)


node_kinds = {
    NodeId.BLOCK_INTRODUCER: node_block_introducer,
    NodeId.BLOCK_ID: node_block_id,
    NodeId.BLOCK_BODY_START: node_block_body_start,
    NodeId.BLOCK: node_block,
    NodeId.ATTRIBUTE_INTRODUCER: node_attribute_introducer,
    NodeId.ATTRIBUTE_ASSIGNMENT: node_attribute_assignment,
    NodeId.ATTRIBUTE: node_attribute,
    NodeId.LIT_STRING: node_lit_string,
    NodeId.LIT_NUMBER: node_lit_number,
}


@dataclass
class Node:
    kind: NodeKind
    token: Token


class StateId(Enum):
    DOC = "DOC"
    BLOCK_INTRODUCER = "BLOCK_INTRODUCER"
    BLOCK_NAMED = "BLOCK_NAMED"
    BLOCK_BODY_UNKNOWN = "BLOCK_BODY_UNKNOWN"
    BLOCK_BODY_VALUE = "BLOCK_BODY_VALUE"
    BLOCK_BODY_AGGREGATE = "BLOCK_BODY_AGGREGATE"
    ATTRIBUTE_INTRODUCER = "ATTRIBUTE_INTRODUCER"
    ATTRIBUTE_ASSIGNMENT = "ATTRIBUTE_ASSIGNMENT"
    ATTRIBUTE_VALUE = "ATTRIBUTE_VALUE"
    VALUE = "VALUE"


@dataclass
class State:
    id: StateId
    start_token_idx: int


class Parser:
    tokens: Sequence[Token]
    tree: MutableSequence[Node]
    state_stack: list[State]
    token_index: int

    def __init__(self, tokens: Sequence[Token]):
        self.tokens = tokens
        self.tree = []
        self.state_stack = [State(StateId.DOC, 0)]
        self.token_index = 0

    def push_state(self, state: State):
        self.state_stack.append(state)

    def pop_state(self, expected_state_ids: Optional[Container[StateId]] = None) -> State:
        state = self.state_stack.pop()
        if expected_state_ids and state.id not in expected_state_ids:
            raise ValueError(f"Unexpected state {state.id}")
        return state
        
    def consume(self, one_of: Optional[Sequence[TokenId]] = None) -> Token:
        """
        Returns the current token and advances the token index.
        If `one_of` is provided, raises an error if the current token's ID is not in the list.
        """
        token = self.tokens[self.token_index]
        if one_of and token.id not in one_of:
            raise ValueError(f"Unexpected token {token.id}")
        self.token_index += 1
        return token
    
    def consume_if(self, token_id: TokenId) -> bool:
        """
        Consumes the current token if it matches the given ID.
        Returns True if the token was consumed, False otherwise.
        """
        if self.tokens[self.token_index].id == token_id:
            self.token_index += 1
            return True
        return False
    
    def consume_discard(self):
        self.token_index += 1

    def _emit_node(self, node: Node):
        self.tree.append(node)

    def emit_node(self, node_kind: NodeKind, token: Token):
        self._emit_node(Node(node_kind, token))

    def step(self):
        if not self.state_stack:
            raise ValueError("Empty stack")
        state = self.state_stack[-1]
        match state.id, self.tokens[self.token_index].id:
            case StateId.DOC, TokenId.ID_NAME:
                # The root level. We encounter a block introducer.
                # So lets push the block introducer state and emit a node, consuming the token.
                token = self.consume()
                self.push_state(State(StateId.BLOCK_INTRODUCER, self.token_index))
                self.emit_node(node_block_introducer, token)
            case StateId.BLOCK_INTRODUCER, TokenId.ID_NAME:
                self.pop_state()
                state.id = StateId.BLOCK_NAMED
                self.push_state(state)
                self.emit_node(node_block_id, self.consume())
            case StateId.BLOCK_INTRODUCER | StateId.BLOCK_NAMED, TokenId.LBRACE:
                token = self.consume()
                self.push_state(State(StateId.BLOCK_BODY_UNKNOWN, self.token_index))
                self.emit_node(node_block_body_start, token)
            case StateId.BLOCK_BODY_UNKNOWN | StateId.BLOCK_BODY_VALUE | StateId.BLOCK_BODY_AGGREGATE, TokenId.RBRACE:
                token = self.consume()
                self.pop_state(expected_state_ids={StateId.BLOCK_BODY_UNKNOWN, StateId.BLOCK_BODY_VALUE, StateId.BLOCK_BODY_AGGREGATE})
                state = self.pop_state(expected_state_ids={StateId.BLOCK_INTRODUCER, StateId.BLOCK_NAMED})
                self.emit_node(node_block, token)
            case StateId.BLOCK_BODY_UNKNOWN | StateId.BLOCK_BODY_AGGREGATE, TokenId.ID_NAME:
                # We're parsing an ID_NAME. This could be an attribute or a block.
                # But we at least know that it's not a value.
                # So we switch to the BLOCK_BODY_AGGREGATE state.
                self.pop_state()
                state.id = StateId.BLOCK_BODY_AGGREGATE
                self.push_state(state)
                # NOTE: At this point we don't know if we're parsing an attribute or a block.
                # We just have an ID_NAME.
                # We'll look-ahead to see if the next token is an equals sign.
                # If it is, we're parsing an attribute. Otherwise we're parsing a block.
                # First we check that we _can_ look ahead.
                if self.token_index + 1 >= len(self.tokens):
                    raise ValueError("Unexpected end of input")
                if self.tokens[self.token_index + 1].id == TokenId.EQUALS:
                    # We're parsing an attribute.
                    token = self.consume()
                    self.push_state(State(StateId.ATTRIBUTE_INTRODUCER, self.token_index))
                    self.emit_node(node_attribute_introducer, token)
                else:
                    # We're parsing a block.
                    token = self.consume()
                    self.push_state(State(StateId.BLOCK_INTRODUCER, self.token_index))
                    self.emit_node(node_block_introducer, token)
            case StateId.BLOCK_BODY_UNKNOWN, _:
                # We're not parsing an ID_NAME, so we must be parsing a value.
                # We switch to the BLOCK_BODY_VALUE state.
                self.pop_state()
                state.id = StateId.BLOCK_BODY_VALUE
                self.push_state(state)
                # We need to parse a value here.
                self.push_state(State(StateId.VALUE, self.token_index))
            case StateId.BLOCK_BODY_VALUE, TokenId.SEMICOLON:
                # Consume the semicolon.
                self.consume_discard()
            case StateId.ATTRIBUTE_INTRODUCER, TokenId.EQUALS:
                self.push_state(State(StateId.ATTRIBUTE_VALUE, self.token_index))
                self.push_state(State(StateId.VALUE, self.token_index))
                self.emit_node(node_attribute_assignment, self.consume())
            case StateId.VALUE, TokenId.LIT_STRING | TokenId.LIT_NUM_DEC:
                token = self.consume()
                match token.id:
                    case TokenId.LIT_STRING:
                        self.emit_node(node_lit_string, token)
                    case TokenId.LIT_NUM_DEC:
                        self.emit_node(node_lit_number, token)
                    case _:
                        raise ValueError(f"Unexpected token {token.id}")
                self.pop_state()
            case StateId.ATTRIBUTE_VALUE, TokenId.SEMICOLON:
                # Close the ATTRIBUTE_VALUE state and emit the ATTRIBUTE_ASSIGNMENT node.
                self.pop_state()
                self.pop_state([StateId.ATTRIBUTE_INTRODUCER])
                self.emit_node(node_attribute, self.consume())
            case _, _:
                raise ValueError(f"Unexpected state {state.id} with token {self.tokens[self.token_index].id}")
    def build_tree(self):
        while self.token_index < len(self.tokens):
            self.step()


def parse(tokens: Sequence[Token]) -> Sequence[Node]:
    parser = Parser(tokens)
    parser.build_tree()
    return parser.tree


@dataclass
class ExplicitTreeNode:
    node: Node
    node_idx: int
    children: Optional[Sequence["ExplicitTreeNode"]] = None

    def build_graphviz(self, graph = None): # -> tuple[graphviz.Digraph, NodeIdStr]:
        import graphviz
        if graph is None:
            graph = graphviz.Digraph()
        
        node_id = f"node_{self.node_idx}"
        label = f"{self.node.kind.id.value} @ {self.node_idx} `{self.node.token.value}`"
        graph.node(node_id, label=label)

        child_node_ids = [child.build_graphviz(graph)[1] for child in self.children] if self.children else []
        for child_node_id in child_node_ids:
            graph.edge(node_id, child_node_id)
        
        return graph, node_id
    
    def render_graphviz(self):
        graph, _ = self.build_graphviz()
        graph.render("parse_tree", format="svg", view=True)


def build_explicit_tree(nodes: Iterable[Node]) -> ExplicitTreeNode:
    stack = []
    for node_idx, node in enumerate(nodes):
        print(f"Processing node {node.kind.id} at index {node_idx}")
        if node.kind.fixed_num_children:
            children = stack[-node.kind.fixed_num_children:]
            stack[-node.kind.fixed_num_children:] = []
            stack.append(ExplicitTreeNode(node, node_idx, children))
        elif node.kind.bracket:
            idx = -1
            try:
                print(f"Looking for bracket {node.kind.bracket.id}")
                while stack[idx].node.kind.id != node.kind.bracket.id:
                    print(f"Inspected {stack[idx].node.kind.id} (looking for {node.kind.bracket.id})")
                    idx -= 1
            except IndexError:
                raise ValueError(f"Could not find bracket for node {node.kind.id} (looking for {node.kind.bracket.id})")
            print(f"Found bracket at {idx}")
            print("Stack before:")
            for i, n in enumerate(stack):
                print(f" - {i} : {n.node.kind.id} @ {n.node_idx}")
            children = stack[idx:]
            print("Children:")
            for i, n in enumerate(stack[idx:]):
                print(f" - {i} : {n.node.kind.id} @ {n.node_idx}")
            stack[idx:] = []
            print("Stack after:")
            for i, n in enumerate(stack):
                print(f" - {i} : {n.node.kind.id} @ {n.node_idx}")
            stack.append(ExplicitTreeNode(node, node_idx, children))
        else:
            stack.append(ExplicitTreeNode(node, node_idx))
    assert len(stack) == 1, f"Expected stack to have 1 element, got {len(stack)}"
    return stack[0]


if __name__ == "__main__":
    import pprint
    import sys
    from edf.lex import tokenize

    text = sys.stdin.read()
    toks = tokenize(text)
    parser = Parser(toks)
    parser.build_tree()

    print("========== TREE ==========")
    for idx, node in enumerate(parser.tree):
        print(node.kind.id.value, idx, "=>", node.token.id.value, node.token.value)

    print("========== EXPLICIT TREE ==========")
    explicit_tree = build_explicit_tree(parser.tree)
    pprint.pprint(explicit_tree)

    explicit_tree.render_graphviz()

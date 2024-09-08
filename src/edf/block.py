from collections.abc import MutableMapping, MutableSequence
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Block:
    kind: str
    name: Optional[str] = None
    value: Optional[Any] = None
    attributes: MutableMapping[str, Any] = field(default_factory=dict)
    children: MutableSequence["Block"] = field(default_factory=list)

    @property
    def is_single_value(self) -> bool:
        return self.value is not None and not self.children
    
    @property
    def is_empty(self) -> bool:
        return not self.value and not self.attributes and not self.children
    
    def __getitem__(self, key: str) -> Any:
        return self.attributes[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def __delitem__(self, key: str) -> None:
        del self.attributes[key]


type Document = MutableSequence[Block]

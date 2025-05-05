from dataclasses import dataclass, field
from typing import List

@dataclass
class Note:
    title: str
    body: str
    tags: List[str] = field(default_factory=list)
from dataclasses import dataclass


@dataclass
class Document:
    content: str
    score: float
    source: str | None = None

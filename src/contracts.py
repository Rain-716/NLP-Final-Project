from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class RetrievalEvidence:
    source_id: str
    title: str
    section: str
    source: str
    start_line: int
    end_line: int
    score: float
    vector_score: float
    bm25_score: float
    text: str

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def citation(self) -> str:
        return f"{self.source}:{self.start_line}-{self.end_line}"


@dataclass
class KnowledgeResponse:
    answer: str
    evidence: list[RetrievalEvidence]
    api_enhanced: bool
    warning: str = ""

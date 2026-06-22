from __future__ import annotations
from .knowledge_service import KnowledgeRetrievalService


class ThresholdKnowledgeRetrievalService(KnowledgeRetrievalService):
    """Reject forced Top-K results when neither lexical nor semantic evidence is strong enough."""

    def __init__(self, *args, min_vector_score: float = 0.30, min_bm25_score: float = 0.50, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_vector_score = min_vector_score
        self.min_bm25_score = min_bm25_score

    def retrieve(self, query: str, top_k: int | None = None):
        evidence = super().retrieve(query, top_k)
        if not evidence:
            return []
        top = evidence[0]
        if top.vector_score < self.min_vector_score and top.bm25_score < self.min_bm25_score:
            return []
        return evidence

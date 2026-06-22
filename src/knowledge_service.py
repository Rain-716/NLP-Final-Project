from __future__ import annotations

import json
import re
from .chatecnu import ChatECNUClient, ChatECNUError
from .contracts import KnowledgeResponse, RetrievalEvidence
from .embeddings import EmbeddingModel
from .terminology import expand_query, term_keywords
from .vector_store import VectorStore


class KnowledgeRetrievalService:
    def __init__(self, embedder: EmbeddingModel, store: VectorStore, *, candidate_k: int = 12,
                 evidence_k: int = 5, vector_weight: float = 0.58, bm25_weight: float = 0.34,
                 term_weight: float = 0.08):
        self.embedder = embedder
        self.store = store
        self.candidate_k = candidate_k
        self.evidence_k = evidence_k
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.term_weight = term_weight

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievalEvidence]:
        query = (query or "").strip()
        if not query:
            return []
        expanded = expand_query(query)
        rows = self.store.query(
            self.embedder.encode(expanded), expanded, top_k or self.candidate_k,
            use_hybrid=True, vector_weight=self.vector_weight, bm25_weight=self.bm25_weight,
            term_weight=self.term_weight, rerank_terms=term_keywords(expanded),
        )
        evidence = []
        for row in rows:
            meta = row.get("metadata") or {}
            evidence.append(RetrievalEvidence(
                source_id=str(meta.get("source_id") or row.get("id")),
                title=str(meta.get("title") or meta.get("document_title") or row.get("id")),
                section=str(meta.get("section") or meta.get("title") or ""),
                source=str(meta.get("source") or "unknown"),
                start_line=int(meta.get("start_line") or 1), end_line=int(meta.get("end_line") or 1),
                score=float(row.get("score") or 0), vector_score=float(row.get("vector_score") or 0),
                bm25_score=float(row.get("bm25_score") or 0), text=str(row.get("text") or ""),
            ))
        return evidence


class ChatECNUKnowledgeService:
    def __init__(self, retrieval: KnowledgeRetrievalService, client: ChatECNUClient):
        self.retrieval = retrieval
        self.client = client

    @staticmethod
    def _evidence_prompt(items: list[RetrievalEvidence]) -> str:
        return "\n\n".join(
            f"[S{i}] 标题={e.title}; 章节={e.section}; 来源={e.citation}\n{e.text[:1800]}"
            for i, e in enumerate(items, 1)
        )

    @staticmethod
    def _degraded(items: list[RetrievalEvidence], reason: str) -> KnowledgeResponse:
        if not items:
            text = "未检索到足够的本地知识证据。"
        else:
            text = "## 本地检索证据\n\n" + "\n".join(
                f"- [S{i}] **{e.title}** — `{e.citation}`：{e.text[:240].replace(chr(10), ' ')}"
                for i, e in enumerate(items[:5], 1)
            )
        warning = f"未完成 ChatECNU 增强：{reason}"
        return KnowledgeResponse(f"> {warning}\n\n{text}", items[:5], False, warning)

    def _rerank(self, query: str, candidates: list[RetrievalEvidence]) -> list[RetrievalEvidence]:
        if len(candidates) <= self.retrieval.evidence_k:
            return candidates
        compact = "\n".join(f"S{i}: {e.title} | {e.text[:350]}" for i, e in enumerate(candidates, 1))
        messages = [
            {"role": "system", "content": "你是证据重排器。只输出 JSON 数组，例如 [3,1,5]，不得输出解释。"},
            {"role": "user", "content": f"问题：{query}\n候选：\n{compact}\n选择最相关的 {self.retrieval.evidence_k} 项。"},
        ]
        raw = self.client.complete(messages, max_tokens=120)
        match = re.search(r"\[[\d,\s]+\]", raw)
        if not match:
            return candidates[:self.retrieval.evidence_k]
        order = json.loads(match.group(0))
        chosen, seen = [], set()
        for value in order:
            idx = int(value) - 1
            if 0 <= idx < len(candidates) and idx not in seen:
                chosen.append(candidates[idx]); seen.add(idx)
            if len(chosen) >= self.retrieval.evidence_k:
                break
        return chosen or candidates[:self.retrieval.evidence_k]

    @staticmethod
    def _validate_citations(answer: str, count: int) -> tuple[str, str]:
        cited = {int(x) for x in re.findall(r"\[S(\d+)\]", answer)}
        invalid = sorted(x for x in cited if x < 1 or x > count)
        if invalid:
            answer += "\n\n> 引用校验：模型生成了不存在的引用，已标记为不可验证：" + ", ".join(f"S{x}" for x in invalid)
        warning = ""
        if count and not any(1 <= x <= count for x in cited):
            warning = "回答未包含有效证据引用；以下内容应视为模型补充，而不是知识库结论。"
            answer = f"> {warning}\n\n" + answer
        return answer, warning

    def answer(self, query: str) -> KnowledgeResponse:
        candidates = self.retrieval.retrieve(query)
        if not candidates:
            return self._degraded([], "本地知识库没有相关证据")
        try:
            evidence = self._rerank(query, candidates)
            messages = [
                {"role": "system", "content": (
                    "你是 ChatECNU 驱动的底层系统知识助手。只能依据提供的证据回答。"
                    "每个事实结论必须使用 [S1] 形式引用；证据不足时明确说明，不得编造来源。"
                )},
                {"role": "user", "content": f"问题：{query}\n\n证据：\n{self._evidence_prompt(evidence)}\n\n"
                                              "请按‘直接回答、原理说明、证据与边界’组织中文答案。"},
            ]
            answer = self.client.complete(messages)
            answer, warning = self._validate_citations(answer, len(evidence))
            return KnowledgeResponse(answer, evidence, True, warning)
        except ChatECNUError as exc:
            return self._degraded(candidates, str(exc))

    def explain_terms(self, text: str) -> KnowledgeResponse:
        candidates = self.retrieval.retrieve(text)
        if not candidates:
            return self._degraded([], "未找到可支持术语解释的本地证据")
        evidence = candidates[:self.retrieval.evidence_k]
        try:
            messages = [
                {"role": "system", "content": (
                    "你是 ChatECNU 术语解释助手。识别输入中的底层系统术语，依据证据解释。"
                    "每个术语包含：定义、作用、简短代码示例、相关概念、易混淆点，并使用 [S编号] 引用。"
                )},
                {"role": "user", "content": f"输入：{text}\n\n证据：\n{self._evidence_prompt(evidence)}"},
            ]
            answer = self.client.complete(messages)
            answer, warning = self._validate_citations(answer, len(evidence))
            return KnowledgeResponse(answer, evidence, True, warning)
        except ChatECNUError as exc:
            return self._degraded(evidence, str(exc))

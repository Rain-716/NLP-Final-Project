from __future__ import annotations

import json
from pathlib import Path
from .chatecnu import ChatECNUClient
from .config import AppConfig
from .embeddings import EmbeddingModel
from .generator import LocalCodeModel
from .ingestion import ingest_documents, index_version
from .knowledge_service import ChatECNUKnowledgeService
from .relevance import ThresholdKnowledgeRetrievalService
from .vector_store import VectorStore


class LocalCodeService:
    def __init__(self, model: LocalCodeModel):
        self.model = model

    def explain(self, code: str) -> str:
        return self.model.explain_code(code)

    def answer(self, question: str, code: str) -> str:
        return self.model.answer_question(question, code)

    def comments(self, code: str) -> str:
        return self.model.generate_comments(code)


class CodeAssistantPipeline:
    """Composition root. Code and knowledge services have disjoint model dependencies."""

    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig.load()
        local_model = LocalCodeModel(
            self.config.local_model, self.config.device, local_files_only=self.config.local_files_only,
            max_input_tokens=self.config.max_input_tokens, max_new_tokens=self.config.max_new_tokens,
            temperature=self.config.temperature,
        )
        self.code_service = LocalCodeService(local_model)
        self.embedder = EmbeddingModel(
            self.config.embedding_model, self.config.device,
            local_files_only=self.config.embedding_local_files_only,
        )
        self.store = VectorStore(self.config.vector_db_dir, self.config.collection_name, self.config.use_chromadb)
        self.retrieval_service = ThresholdKnowledgeRetrievalService(
            self.embedder, self.store, candidate_k=self.config.top_k_candidates,
            evidence_k=self.config.top_k_evidence, vector_weight=self.config.vector_weight,
            bm25_weight=self.config.bm25_weight, term_weight=self.config.term_weight,
        )
        client = ChatECNUClient(
            self.config.chatecnu_base_url, self.config.chatecnu_model, self.config.chatecnu_api_key,
            timeout=self.config.chatecnu_timeout_seconds, retries=self.config.chatecnu_retries,
            temperature=self.config.chatecnu_temperature, cache_dir=self.config.chatecnu_cache_dir,
        )
        self.knowledge_service = ChatECNUKnowledgeService(self.retrieval_service, client)

    def build_index(self, data_dir: str | Path = "data", reset: bool = False) -> dict:
        chunks, report = ingest_documents(
            data_dir, self.config.source_manifest, self.config.max_chunk_chars, self.config.chunk_overlap
        )
        if reset:
            self.store.reset()
        if chunks:
            ids = [c.chunk_id for c in chunks]
            texts = [c.text for c in chunks]
            embeddings = self.embedder.encode(texts)
            metadatas = []
            for c in chunks:
                source_meta = c.symbols.get("source_meta", {})
                metadatas.append({
                    "source": c.source, "source_id": source_meta.get("source_id", c.source),
                    "document_title": source_meta.get("document_title", Path(c.source).stem),
                    "version": source_meta.get("version", "local"), "url": source_meta.get("url", ""),
                    "license": source_meta.get("license", "unspecified"),
                    "content_hash": source_meta.get("content_hash", ""), "language": c.language,
                    "start_line": c.start_line, "end_line": c.end_line, "kind": c.kind,
                    "title": c.title, "section": c.title, "symbols": c.symbols,
                    "keywords": c.keywords,
                })
            self.store.add(ids, texts, embeddings, metadatas)
        result = report.to_dict()
        result["index_version"] = index_version(chunks)
        result["embedding_backend"] = self.embedder.backend
        manifest_path = Path(self.config.index_manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    @staticmethod
    def _run_code(action, *args) -> str:
        try:
            return action(*args)
        except Exception as exc:
            return f"## 本地模型未完成请求\n\n{exc}"

    def explain_code(self, code: str) -> str:
        return self._run_code(self.code_service.explain, code)

    def answer_question(self, question: str, code: str) -> str:
        return self._run_code(self.code_service.answer, question, code)

    def generate_comments(self, code: str) -> str:
        return self._run_code(self.code_service.comments, code)

    @staticmethod
    def _format_knowledge(response) -> tuple[str, str]:
        evidence_lines = []
        for i, item in enumerate(response.evidence, 1):
            evidence_lines += [
                f"### S{i}. {item.title}",
                f"- 来源：`{item.citation}`；章节：{item.section or '-'}",
                f"- 综合得分：{item.score:.4f}；向量：{item.vector_score:.4f}；BM25：{item.bm25_score:.4f}",
                "```text", item.text[:900], "```", "",
            ]
        return response.answer, "\n".join(evidence_lines) or "没有可展示的本地证据。"

    def search_knowledge(self, query: str) -> tuple[str, str]:
        return self._format_knowledge(self.knowledge_service.answer(query))

    def term_explain(self, text: str) -> tuple[str, str]:
        return self._format_knowledge(self.knowledge_service.explain_terms(text))

    def status_markdown(self) -> str:
        model = self.code_service.model.status(load=False)
        index_path = Path(self.config.index_manifest)
        index = {}
        if index_path.exists():
            try: index = json.loads(index_path.read_text(encoding="utf-8"))
            except Exception: pass
        api_ok = self.knowledge_service.client.configured
        return "\n".join([
            "### 服务状态",
            f"- 本地代码模型：`{model.model}`（{'已加载' if model.loaded else '按需加载'}）",
            f"- 向量模型：`{self.config.embedding_model}`（后端：{self.embedder.backend}）",
            f"- 知识库版本：`{index.get('index_version', '未构建')}`，片段数：{index.get('chunks_created', 0)}",
            f"- ChatECNU：{'已配置' if api_ok else '未配置'}（密钥环境变量：`{self.config.chatecnu_api_key_env}`）",
        ])

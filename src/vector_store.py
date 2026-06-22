from __future__ import annotations
import json, math, shutil
from pathlib import Path
from collections import Counter
import numpy as np
from .preprocessing import tokenize

class VectorStore:
    """ChromaDB + JSON sidecar 本地向量库。

    ChromaDB 只保存扁平 metadata，完整 metadata 和文本另存 JSON，
    这样能兼容不同版本 Chroma 的 metadata 类型限制，也方便 BM25 与证据展示。
    """
    def __init__(self, persist_dir: str = 'vector_db', collection_name: str = 'syscode_knowledge_base', use_chromadb: bool = True):
        self.persist_dir = Path(persist_dir); self.collection_name = collection_name
        self.backend = 'json'; self.client = None; self.collection = None
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.persist_dir / f'{collection_name}.json'
        self.sidecar_path = self.persist_dir / f'{collection_name}_sidecar.json'
        if use_chromadb:
            try:
                import chromadb
                self.client = chromadb.PersistentClient(path=str(self.persist_dir))
                self.collection = self.client.get_or_create_collection(name=collection_name)
                self.backend = 'chromadb+json'
            except Exception as e:
                print(f'[VectorStore] ChromaDB 不可用，启用 JSON fallback: {e}')
        self._docs_cache: list[dict] | None = None

    def reset(self):
        if self.client is not None:
            try:
                self.client.delete_collection(self.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        self.json_path.write_text('[]', encoding='utf-8')
        self.sidecar_path.write_text('[]', encoding='utf-8')
        self._docs_cache = []

    @staticmethod
    def _sanitize_metadata_for_chroma(meta: dict) -> dict:
        safe = {}
        for k, v in (meta or {}).items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                safe[k] = v
            elif isinstance(v, (list, tuple, set)):
                safe[k] = ', '.join(map(str, v))
            else:
                safe[k] = json.dumps(v, ensure_ascii=False)
        return safe

    @staticmethod
    def _merge_unique_by_id(rows: list[dict]) -> list[dict]:
        seen = {}
        for r in rows:
            seen[r['id']] = r
        return list(seen.values())

    def add(self, ids: list[str], texts: list[str], embeddings, metadatas: list[dict] | None = None):
        metadatas = metadatas or [{} for _ in ids]
        embeddings = np.asarray(embeddings).astype(float).tolist()
        rows = [{'id': i, 'text': t, 'embedding': e, 'metadata': m} for i, t, e, m in zip(ids, texts, embeddings, metadatas)]
        if self.collection is not None:
            chroma_metadatas = [self._sanitize_metadata_for_chroma(m) for m in metadatas]
            try:
                # upsert 避免重复构建索引时因 id 已存在而失败
                if hasattr(self.collection, 'upsert'):
                    self.collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=chroma_metadatas)
                else:
                    self.collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=chroma_metadatas)
            except Exception as e:
                print(f'[VectorStore] Chroma 写入失败，JSON sidecar 仍可使用: {e}')
        existing: list[dict] = []
        if self.json_path.exists():
            try:
                existing = json.loads(self.json_path.read_text(encoding='utf-8') or '[]')
            except Exception:
                existing = []
        existing = self._merge_unique_by_id(existing + rows)
        self.json_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
        side = [{'id': r['id'], 'text': r['text'], 'metadata': r['metadata']} for r in existing]
        self.sidecar_path.write_text(json.dumps(side, ensure_ascii=False, indent=2), encoding='utf-8')
        self._docs_cache = existing

    def _load_rows(self) -> list[dict]:
        if self._docs_cache is not None:
            return self._docs_cache
        if not self.json_path.exists():
            self._docs_cache = []
        else:
            self._docs_cache = json.loads(self.json_path.read_text(encoding='utf-8') or '[]')
        return self._docs_cache

    @staticmethod
    def _cosine(a, b) -> float:
        a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(a.dot(b) / denom) if denom else 0.0

    @staticmethod
    def _meta_keywords(meta: dict) -> str:
        kws = meta.get('keywords', []) if meta else []
        if isinstance(kws, str):
            kw_text = kws
        elif isinstance(kws, (list, tuple, set)):
            kw_text = ' '.join(map(str, kws))
        else:
            kw_text = str(kws)
        return ' '.join(str(x) for x in [meta.get('title',''), meta.get('kind',''), meta.get('source',''), kw_text])

    def _bm25_scores(self, query_text: str, rows: list[dict]) -> dict[str, float]:
        q_tokens = tokenize(query_text or '')
        if not q_tokens or not rows:
            return {r['id']: 0.0 for r in rows}
        docs_tokens, df = [], Counter()
        for r in rows:
            meta = r.get('metadata') or {}
            toks = tokenize(r.get('text','') + '\n' + self._meta_keywords(meta))
            docs_tokens.append(toks); df.update(set(toks))
        N = len(rows); avgdl = sum(len(t) for t in docs_tokens) / max(1, N); k1, b = 1.5, 0.75
        scores, q_count = {}, Counter(q_tokens)
        for r, toks in zip(rows, docs_tokens):
            tf = Counter(toks); dl = len(toks); score = 0.0
            for term in q_count:
                if term not in tf:
                    continue
                idf = math.log(1 + (N - df[term] + 0.5) / (df[term] + 0.5))
                denom = tf[term] + k1 * (1 - b + b * dl / max(avgdl, 1e-9))
                score += idf * (tf[term] * (k1 + 1) / max(denom, 1e-9))
            scores[r['id']] = float(score)
        return scores

    @staticmethod
    def _normalize(scores: dict[str, float]) -> dict[str, float]:
        vals = list(scores.values())
        if not vals:
            return {}
        lo, hi = min(vals), max(vals)
        if abs(hi-lo) < 1e-12:
            return {k: 0.0 for k in scores}
        return {k: (v-lo)/(hi-lo) for k, v in scores.items()}

    def query(self, query_embedding, query_text: str = '', top_k: int = 5, *, use_hybrid: bool = True,
              vector_weight: float = 0.62, bm25_weight: float = 0.30, term_weight: float = 0.08,
              rerank_terms: list[str] | None = None) -> list[dict]:
        rows = self._load_rows()
        if not rows:
            return []
        q_emb = np.asarray(query_embedding).astype(float)
        vector_scores = {r['id']: self._cosine(r.get('embedding', []), q_emb) for r in rows}
        bm25_scores = self._bm25_scores(query_text, rows) if use_hybrid else {r['id']:0.0 for r in rows}
        vector_norm, bm25_norm = self._normalize(vector_scores), self._normalize(bm25_scores)
        rerank_terms = [t.lower() for t in (rerank_terms or [])]
        scored = []
        for r in rows:
            rid = r['id']; text = (r.get('text') or '').lower(); meta = r.get('metadata') or {}
            meta_blob = self._meta_keywords(meta).lower()
            term_hits = sum(1 for t in rerank_terms if t and (t in text or t in meta_blob))
            term_score = min(1.0, term_hits / max(1, min(len(rerank_terms), 8)))
            hybrid = vector_weight * vector_norm.get(rid,0.0) + bm25_weight * bm25_norm.get(rid,0.0) + term_weight * term_score
            scored.append((hybrid, vector_scores.get(rid,0), bm25_scores.get(rid,0), term_score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for hybrid, vs, bs, ts, r in scored[:top_k]:
            out.append({'id': r['id'], 'text': r['text'], 'metadata': r.get('metadata') or {},
                        'score': round(float(hybrid),4), 'vector_score': round(float(vs),4),
                        'bm25_score': round(float(bs),4), 'term_score': round(float(ts),4),
                        'distance': round(1-float(vs),4)})
        return out

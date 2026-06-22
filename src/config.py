from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import yaml


@dataclass
class AppConfig:
    project_name: str = "syscode_nlp_assistant_v4"
    language: str = "zh"
    local_model: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    local_files_only: bool = True
    device: str = "auto"
    max_input_tokens: int = 6144
    max_new_tokens: int = 1200
    temperature: float = 0.15
    embedding_model: str = "microsoft/codebert-base"
    embedding_local_files_only: bool = True
    use_chromadb: bool = True
    vector_db_dir: str = "vector_db"
    collection_name: str = "syscode_knowledge_base_v4"
    source_manifest: str = "data/sources.yaml"
    index_manifest: str = "vector_db/index_manifest.json"
    max_chunk_chars: int = 1200
    chunk_overlap: int = 160
    top_k_candidates: int = 12
    top_k_evidence: int = 5
    vector_weight: float = 0.58
    bm25_weight: float = 0.34
    term_weight: float = 0.08
    chatecnu_base_url: str = ""
    chatecnu_model: str = ""
    chatecnu_api_key_env: str = "CHATECNU_API_KEY"
    chatecnu_timeout_seconds: float = 45.0
    chatecnu_retries: int = 2
    chatecnu_temperature: float = 0.15
    chatecnu_cache_dir: str = ".cache/chatecnu"

    @property
    def chatecnu_api_key(self) -> str:
        return os.getenv(self.chatecnu_api_key_env, "").strip()

    @classmethod
    def load(cls, path: str | Path = "config.yaml") -> "AppConfig":
        path = Path(path)
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        merged: dict = {}
        groups = {"local_code", "knowledge_base", "chatecnu", "generation"}
        for key, value in data.items():
            if isinstance(value, dict) and key in groups:
                merged.update(value)
            else:
                merged[key] = value
        if "generator_model" in merged and "local_model" not in merged:
            merged["local_model"] = merged["generator_model"]
        return cls(**{k: v for k, v in merged.items() if k in cls.__dataclass_fields__})

    def public_status(self) -> dict:
        return {"local_model": self.local_model, "embedding_model": self.embedding_model,
                "chat_ecnu_configured": bool(self.chatecnu_base_url and self.chatecnu_model and self.chatecnu_api_key),
                "api_key_env": self.chatecnu_api_key_env}

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.chatecnu import ChatECNUClient
from src.config import AppConfig
from src.rag_pipeline import CodeAssistantPipeline


class _Response:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({"choices":[{"message":{"content":"ok"}}]}).encode()


class ResilienceTests(unittest.TestCase):
    def test_api_retries_once_after_network_error(self):
        calls = []
        def fake_open(req, timeout):
            calls.append(req)
            if len(calls) == 1: raise URLError("temporary")
            return _Response()
        with tempfile.TemporaryDirectory() as td, patch("src.chatecnu.urlopen", fake_open), patch("src.chatecnu.time.sleep"):
            client = ChatECNUClient("https://example/v1", "model", "key", retries=1, cache_dir=td)
            self.assertEqual(client.complete([{"role":"user","content":"x"}]), "ok")
        self.assertEqual(len(calls), 2)

    def test_incremental_index_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); data = root / "data"; (data / "docs").mkdir(parents=True)
            (data / "docs" / "cache.md").write_text("# Cache\n\nCache 使用 tag、index 和 offset 完成地址映射。", encoding="utf-8")
            (data / "sources.yaml").write_text("sources:\n  - id: cache\n    path: docs/cache.md\n    title: Cache\n", encoding="utf-8")
            cfg = AppConfig(embedding_model="hash", use_chromadb=False,
                            vector_db_dir=str(root / "db"), collection_name="test",
                            source_manifest=str(data / "sources.yaml"), index_manifest=str(root / "db" / "manifest.json"))
            pipeline = CodeAssistantPipeline(cfg)
            first = pipeline.build_index(data, reset=True)
            second = pipeline.build_index(data, reset=False)
            rows = json.loads((root / "db" / "test.json").read_text(encoding="utf-8"))
            self.assertEqual(first["chunks_created"], second["chunks_created"])
            self.assertEqual(len(rows), first["chunks_created"])
            self.assertTrue((root / "db" / "manifest.json").exists())


if __name__ == "__main__": unittest.main()

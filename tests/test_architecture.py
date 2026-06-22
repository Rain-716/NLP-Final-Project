import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.chatecnu import ChatECNUClient
from src.config import AppConfig
from src.contracts import RetrievalEvidence
from src.generator import LocalCodeModel, LocalModelUnavailable
from src.knowledge_service import ChatECNUKnowledgeService


class _Response:
    def __init__(self, content): self.content = content
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self):
        return json.dumps({"choices": [{"message": {"content": self.content}}]}).encode()


class _Retrieval:
    evidence_k = 2
    def retrieve(self, query):
        return [
            RetrievalEvidence("cache", "Cache 地址", "地址拆分", "docs/cache.md", 3, 8,
                              0.9, 0.8, 0.7, "地址由 tag、index 和 offset 组成。"),
            RetrievalEvidence("pipeline", "流水线", "数据冒险", "docs/pipeline.md", 4, 9,
                              0.7, 0.6, 0.5, "RAW 冒险可通过 forwarding 或 stall 处理。"),
        ]


class ArchitectureTests(unittest.TestCase):
    def test_grouped_config_and_secret_from_environment(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.yaml"
            path.write_text("local_code:\n  local_model: cached-model\nchatecnu:\n  chatecnu_api_key_env: TEST_KEY\n", encoding="utf-8")
            with patch.dict(os.environ, {"TEST_KEY": "secret"}):
                cfg = AppConfig.load(path)
                self.assertEqual(cfg.local_model, "cached-model")
                self.assertEqual(cfg.chatecnu_api_key, "secret")
                self.assertNotIn("secret", path.read_text(encoding="utf-8"))

    def test_local_model_is_offline_and_has_no_rule_fallback(self):
        model = LocalCodeModel("definitely-not-cached", local_files_only=True)
        with self.assertRaises(LocalModelUnavailable):
            model._ensure_loaded()
        self.assertFalse(hasattr(model, "fallback"))

    def test_openai_compatible_request_shape(self):
        captured = {}
        def fake_open(req, timeout):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data.decode())
            captured["auth"] = req.headers["Authorization"]
            return _Response("ok")
        with tempfile.TemporaryDirectory() as td, patch("src.chatecnu.urlopen", fake_open):
            client = ChatECNUClient("https://example.edu/v1", "ecnu-model", "key", cache_dir=td)
            self.assertEqual(client.complete([{"role": "user", "content": "hi"}]), "ok")
        self.assertEqual(captured["url"], "https://example.edu/v1/chat/completions")
        self.assertEqual(captured["body"]["model"], "ecnu-model")
        self.assertEqual(captured["auth"], "Bearer key")

    def test_citation_validation_and_api_answer(self):
        class Client:
            configured = True
            def complete(self, messages, **kwargs): return "结论来自证据 [S1]。"
        response = ChatECNUKnowledgeService(_Retrieval(), Client()).answer("Cache 怎么拆分")
        self.assertTrue(response.api_enhanced)
        self.assertIn("[S1]", response.answer)

    def test_api_failure_returns_evidence_not_fake_answer(self):
        class Client:
            configured = False
            def complete(self, messages, **kwargs):
                from src.chatecnu import ChatECNUError
                raise ChatECNUError("offline")
        response = ChatECNUKnowledgeService(_Retrieval(), Client()).answer("Cache")
        self.assertFalse(response.api_enhanced)
        self.assertIn("未完成 ChatECNU 增强", response.answer)
        self.assertIn("docs/cache.md", response.answer)

    def test_risk_module_removed_from_public_architecture(self):
        root = Path(__file__).resolve().parents[1]
        self.assertFalse((root / "src" / "risk_analyzer.py").exists())
        self.assertFalse((root / "data" / "docs" / "risk_diagnosis_cases.md").exists())
        self.assertNotIn("diagnose_code", (root / "src" / "rag_pipeline.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

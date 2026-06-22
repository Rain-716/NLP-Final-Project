from __future__ import annotations
import numpy as np


class EmbeddingModel:
    def __init__(self, model_name: str = "microsoft/codebert-base", device: str = "auto",
                 local_files_only: bool = True):
        self.model_name = model_name
        self.device = device
        self.local_files_only = local_files_only
        self.backend = "hash"
        self.model = None
        self.tokenizer = None
        self.load_error = ""
        if model_name.lower() not in {"hash", "fallback", "none"}:
            self._init_model()

    def _init_model(self):
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=self.local_files_only)
            self.model = AutoModel.from_pretrained(self.model_name, local_files_only=self.local_files_only)
            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device); self.model.eval(); self.backend = "transformers"
        except Exception as exc:
            self.load_error = str(exc)
            self.backend = "hash"

    def encode(self, texts: list[str] | str) -> np.ndarray:
        single = isinstance(texts, str)
        if single: texts = [texts]
        arr = self._encode_transformers(texts) if self.backend == "transformers" else self._encode_hash(texts)
        return arr[0] if single else arr

    def _encode_transformers(self, texts: list[str]) -> np.ndarray:
        import torch
        outs = []
        with torch.inference_mode():
            for start in range(0, len(texts), 8):
                batch = self.tokenizer(texts[start:start + 8], padding=True, truncation=True,
                                       max_length=512, return_tensors="pt")
                batch = {k: v.to(self.device) for k, v in batch.items()}
                output = self.model(**batch)
                mask = batch["attention_mask"].unsqueeze(-1)
                emb = (output.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1)
                outs.append(torch.nn.functional.normalize(emb, p=2, dim=1).cpu().numpy())
        return np.vstack(outs)

    @staticmethod
    def _encode_hash(texts: list[str], dim: int = 384) -> np.ndarray:
        import hashlib, re
        arr = np.zeros((len(texts), dim), dtype=np.float32)
        for i, text in enumerate(texts):
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff]|\d+", text.lower())
            for token in tokens:
                h = int(hashlib.md5(token.encode()).hexdigest(), 16)
                arr[i, h % dim] += 1
            norm = np.linalg.norm(arr[i])
            if norm: arr[i] /= norm
        return arr

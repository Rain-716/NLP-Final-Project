from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ChatECNUError(RuntimeError):
    pass


class ChatECNUClient:
    """Small OpenAI-compatible client with retries and exact-request caching."""

    def __init__(self, base_url: str, model: str, api_key: str, *, timeout: float = 45,
                 retries: int = 2, temperature: float = 0.15, cache_dir: str = ".cache/chatecnu"):
        self.base_url = (base_url or "").rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.retries = max(0, retries)
        self.temperature = temperature
        self.cache_dir = Path(cache_dir)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model and self.api_key)

    @property
    def endpoint(self) -> str:
        return self.base_url if self.base_url.endswith("/chat/completions") else f"{self.base_url}/chat/completions"

    def _cache_path(self, payload: dict) -> Path:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return self.cache_dir / f"{hashlib.sha256(raw).hexdigest()}.json"

    def complete(self, messages: list[dict], *, max_tokens: int = 1400, use_cache: bool = True) -> str:
        if not self.configured:
            raise ChatECNUError("ChatECNU 未配置。请填写 Base URL、模型名并设置 API Key 环境变量。")
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature,
                   "max_tokens": max_tokens}
        cache_path = self._cache_path(payload)
        if use_cache and cache_path.exists():
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))["content"]
            except Exception:
                pass
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        last_error = ""
        for attempt in range(self.retries + 1):
            req = Request(self.endpoint, data=body,
                          headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                          method="POST")
            try:
                with urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"].strip()
                if not content:
                    raise ChatECNUError("ChatECNU 返回空内容。")
                if use_cache:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(json.dumps({"content": content}, ensure_ascii=False), encoding="utf-8")
                return content
            except HTTPError as exc:
                last_error = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')[:500]}"
                if exc.code < 500 and exc.code != 429:
                    break
            except (URLError, TimeoutError, OSError, KeyError, ValueError, ChatECNUError) as exc:
                last_error = str(exc)
            if attempt < self.retries:
                time.sleep(min(0.5 * (2 ** attempt), 2.0))
        raise ChatECNUError(f"ChatECNU 请求失败：{last_error}")

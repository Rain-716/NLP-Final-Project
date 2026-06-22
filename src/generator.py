from __future__ import annotations

from dataclasses import dataclass
from .preprocessing import extract_symbols, split_code_to_chunks


class LocalModelUnavailable(RuntimeError):
    pass


@dataclass
class ModelStatus:
    loaded: bool
    model: str
    device: str
    detail: str


class LocalCodeModel:
    """Local-only generator for code tasks. It never calls a remote service."""

    def __init__(self, model_name: str, device: str = "auto", *, local_files_only: bool = True,
                 max_input_tokens: int = 6144, max_new_tokens: int = 1200, temperature: float = 0.15):
        self.model_name = model_name
        self.device = device
        self.local_files_only = local_files_only
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.tokenizer = None
        self.model = None
        self._load_error = "尚未加载"

    def _ensure_loaded(self) -> None:
        if self.model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, trust_remote_code=True, local_files_only=self.local_files_only
            )
            kwargs = {"trust_remote_code": True, "local_files_only": self.local_files_only}
            kwargs["device_map"] = "auto" if self.device == "auto" else {"": self.device}
            if torch.cuda.is_available():
                kwargs["torch_dtype"] = torch.float16
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **kwargs)
            self._load_error = ""
        except Exception as exc:
            self.model = None
            self.tokenizer = None
            self._load_error = str(exc)
            raise LocalModelUnavailable(
                "本地代码模型加载失败。请确认模型已存在于 Hugging Face 缓存、配置名称正确，"
                "并检查显存/内存。系统不会下载模型，也不会用规则模板伪装模型输出。"
                f"\n\n技术信息：{exc}"
            ) from exc

    def status(self, load: bool = False) -> ModelStatus:
        if load:
            try:
                self._ensure_loaded()
            except LocalModelUnavailable:
                pass
        loaded = self.model is not None
        current_device = str(getattr(self.model, "device", self.device)) if loaded else self.device
        return ModelStatus(loaded, self.model_name, current_device, "可用" if loaded else self._load_error)

    @staticmethod
    def _validate_code(code: str) -> str:
        code = (code or "").strip()
        if not code:
            raise ValueError("请输入待分析的代码。")
        if len(code) > 120_000:
            raise ValueError("代码超过 120,000 字符，请按文件或模块拆分后分析。")
        return code

    def _generate(self, system: str, user: str) -> str:
        self._ensure_loaded()
        import torch
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([prompt], return_tensors="pt", truncation=True,
                                max_length=self.max_input_tokens).to(self.model.device)
        kwargs = {"max_new_tokens": self.max_new_tokens, "do_sample": self.temperature > 0,
                  "pad_token_id": self.tokenizer.eos_token_id}
        if self.temperature > 0:
            kwargs["temperature"] = self.temperature
        try:
            with torch.inference_mode():
                output = self.model.generate(**inputs, **kwargs)
        except torch.cuda.OutOfMemoryError as exc:
            raise LocalModelUnavailable(
                "本地模型推理显存不足。请缩短代码、降低 max_input_tokens，或切换到 CPU/更小模型。"
            ) from exc
        answer = self.tokenizer.decode(output[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True).strip()
        if not answer:
            raise RuntimeError("本地模型返回了空结果。")
        return answer

    @staticmethod
    def _code_digest(code: str) -> str:
        symbols = extract_symbols(code)
        return (f"函数: {', '.join(symbols['functions']) or '未识别'}\n"
                f"类/结构体: {', '.join(symbols['classes']) or '未识别'}\n"
                f"变量: {', '.join(symbols['variables'][:40]) or '未识别'}")

    @staticmethod
    def _prepare_code(code: str) -> str:
        chunks = split_code_to_chunks(code, "user_input.cpp", max_chars=7000, overlap=200)
        if len(chunks) <= 1:
            return code
        return "\n\n".join(
            f"// ---- 代码片段 {i}/{len(chunks)}: {c.title or c.kind} ----\n{c.text}"
            for i, c in enumerate(chunks[:8], 1)
        )

    def explain_code(self, code: str) -> str:
        code = self._validate_code(code)
        system = ("你是面向 C/C++、RISC-V、流水线、Cache 与系统编程代码的中文代码理解助手。"
                  "只能依据用户代码推断；没有证据时明确写‘代码中无法确定’。不要进行漏洞或风险诊断。")
        user = f"""请解释以下代码。严格使用五个标题：
## 功能概述
## 关键符号
## 执行流程
## 底层机制
## 代码依据
每个结论引用具体函数名、变量名或表达式，不要输出无关的通用教程。

[静态提取摘要]
{self._code_digest(code)}

[代码]
```cpp
{self._prepare_code(code)}
```"""
        return self._generate(system, user)

    def answer_question(self, question: str, code: str) -> str:
        code = self._validate_code(code)
        question = (question or "").strip()
        if not question:
            raise ValueError("请输入关于代码的问题。")
        system = ("你是本地运行的代码问答助手。回答只能来自给定代码，不使用外部知识库。"
                  "先给直接结论，再给代码证据；信息不足时明确边界。不要进行风险诊断。")
        user = f"""[问题]
{question}

[静态提取摘要]
{self._code_digest(code)}

[代码]
```cpp
{self._prepare_code(code)}
```

使用“回答、代码依据、不确定性”三个标题。"""
        return self._generate(system, user)

    def generate_comments(self, code: str) -> str:
        code = self._validate_code(code)
        system = ("你是本地中文代码注释生成器。保持代码语义和格式，不修改语句，"
                  "只增加解释设计意图、状态含义和执行阶段的简洁中文注释。不要输出风险诊断。")
        user = f"""为以下代码生成注释。输出且仅输出一个 cpp 代码块；不要逐行机械翻译，
优先注释函数职责、关键状态、位字段、流水线阶段和 Cache 字段。

```cpp
{self._prepare_code(code)}
```"""
        return self._generate(system, user)

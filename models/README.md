# 模型权重目录

默认不随压缩包附带大模型权重。运行时会根据 config.yaml 中的模型名称自动从 HuggingFace 加载，也可以把本地模型目录放在此处，然后将 config.yaml 改为本地路径，例如：

```yaml
generator_model: models/Qwen2.5-Coder-1.5B-Instruct
embedding_model: models/codebert-base
```

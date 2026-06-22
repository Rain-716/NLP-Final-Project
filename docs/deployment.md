# 部署说明

1. 创建 Python 3.10 环境并安装与硬件匹配的 PyTorch。
2. 安装 `requirements.txt`，确认 Qwen2.5-Coder 和 CodeBERT 已位于本机缓存或本地目录。
3. 在 `config.yaml` 填写 ChatECNU Base URL 与模型名，在进程环境中设置 `CHATECNU_API_KEY`。
4. 运行 `python scripts/build_index.py --config config.yaml --reset` 构建首版索引。
5. 运行 `python -m unittest discover -s tests -p "test_*.py" -v` 验证隔离、API 协议和降级。
6. 运行 `python app.py` 启动界面。

生产演示前应检查界面顶部状态。若 ChatECNU 未配置，知识功能会显示本地证据但不会伪造 API 答案；若本地模型不存在，代码功能会给出明确错误。

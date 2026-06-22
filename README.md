# 面向底层系统代码的智能问答与注释生成助手 v4

这是一个面向 C/C++、RISC-V、处理器流水线和 Cache 学习场景的双模型 NLP 系统。它把代码理解与知识问答明确分开，避免所有功能共用一个小模型造成的幻觉和职责混乱。

## 架构

* **本地代码链路**：本机 Hugging Face 缓存中的 Qwen2.5-Coder 负责代码解析、代码问答和中文注释生成。启用 `local_files_only`，不会联网下载，也不会静默退回规则模板。
* **知识链路**：本地 CodeBERT/哈希向量 + BM25 + 术语扩展召回候选证据，ChatECNU 通过 OpenAI 兼容接口完成重排、带引用回答和术语解释。
* **可信降级**：ChatECNU 未配置、超时或失败时，只展示本地检索证据并明确标注未完成 API 增强。
* **可追溯知识库**：片段记录来源、版本、章节、行号、许可和内容哈希；索引由脚本显式构建，应用启动时不重建。

## 功能

1. 代码解析：功能、符号、流程、底层机制与代码依据。
2. 代码问答：仅依据输入代码回答，信息不足时说明边界。
3. 中文注释：由本地代码模型生成，不改变代码语义。
4. 知识问答：本地召回、ChatECNU 重排和带 `[S1]` 引用的答案。
5. 术语解释：给出定义、作用、示例、相关概念和易混淆点。

## 安装

建议 Python 3.10。先按显卡环境安装 PyTorch，再安装其余依赖：

```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

CPU 环境可改装官方 CPU 版 PyTorch。项目不会自动下载生成模型和向量模型；请先将模型放入 Hugging Face 缓存，或把 `config.yaml` 中模型名改为本地目录。

## ChatECNU 配置

在 `config.yaml` 中填写开放平台提供的 OpenAI 兼容 Base URL 和模型名：

```yaml
chatecnu:
  chatecnu_base_url: https://your-platform.example/v1
  chatecnu_model: your-model-id
  chatecnu_api_key_env: CHATECNU_API_KEY
```

密钥只通过环境变量提供：

```cmd
set CHATECNU_API_KEY=你的密钥
```

不要把真实密钥写入 YAML、`.env.example`、测试结果或截图。

## 构建知识库

`data/sources.yaml` 是来源登记表。允许导入 Markdown、TXT、PDF、C/C++ 文件；PDF 依赖 `pypdf`。

```cmd
REM 首次全量构建
python scripts/build_index.py --config config.yaml --reset

REM 内容增加后的增量 upsert
python scripts/build_index.py --config config.yaml
```

构建结果写入 `vector_db_v4/index_manifest.json`，包含索引版本、文件数、去重数、失败文件和来源覆盖。

## 启动

```cmd
python app.py
```

本地模型首次点击代码功能时才加载。界面顶部会显示本地模型、向量后端、知识库版本和 ChatECNU 配置状态。

## 测试与评测

```cmd
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/evaluate_retrieval.py --config config_eval.yaml
python run_tests.py --config config_eval.yaml
```

自动化测试使用 Mock API 验证请求结构、引用、降级和模型隔离，不需要真实密钥。真实 ChatECNU 联调应在设置密钥后进行。检索报告给出 Recall@5、MRR、nDCG@5 和领域外误召回，不再以“出现任一关键词”冒充完整正确。

## 目录

```text
app.py                    Gradio 界面
src/generator.py          严格离线的本地代码模型
src/chatecnu.py           OpenAI 兼容 API 客户端
src/knowledge_service.py  检索、重排、引用与降级
src/ingestion.py          多格式采集、去重和来源治理
scripts/build_index.py    显式/增量索引构建
tests/                    架构和接口测试
data/sources.yaml         知识来源登记表
```

## 已知边界

* 1.5B 参数模型适合课程项目和中短代码，复杂跨文件推理建议配置更强的本地代码模型。
* 当前代码结构提取主要基于轻量解析；大型工程可继续接入 Tree-sitter 或编译数据库。
* API 生成质量取决于 ChatECNU 开放平台所选模型；本系统通过证据引用和失败降级降低不可验证输出。
* 仓库不分发大模型权重或受限版权资料全文，只保存项目自编内容、来源元数据和构建方式。

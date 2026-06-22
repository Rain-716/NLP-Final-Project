import argparse, math, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config import AppConfig
from src.rag_pipeline import CodeAssistantPipeline

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="config_eval.yaml")
parser.add_argument("--output", default="results/retrieval_eval.md")
args = parser.parse_args()
queries = [
    ("流水线 RAW 冒险如何通过 forwarding 或 stall 处理", {"local-pipeline-notes", "local-system-terms"}),
    ("load-use 为什么需要插入 bubble", {"local-pipeline-notes", "local-architecture-notes"}),
    ("Cache 地址如何拆分 tag index offset", {"local-cache-notes", "local-system-terms"}),
    ("RISC-V opcode funct3 funct7 如何译码", {"local-riscv-notes", "local-system-terms"}),
    ("std::bitset 如何表示寄存器状态位", {"local-cpp-notes", "local-system-terms"}),
]
irrelevant = ["法国大革命发生在哪一年", "如何烘焙巧克力蛋糕"]
p = CodeAssistantPipeline(AppConfig.load(args.config))
if not Path(p.config.index_manifest).exists(): p.build_index("data", reset=True)
recall_hits = 0; reciprocal = []; ndcgs = []; rejection_hits = 0
lines = ["# 检索评测结果", ""]
for i, (query, relevant) in enumerate(queries, 1):
    rows = p.retrieval_service.retrieve(query, top_k=5)
    labels = [row.source_id for row in rows]
    ranks = [idx + 1 for idx, value in enumerate(labels) if value in relevant]
    recall_hits += int(bool(ranks)); reciprocal.append(1 / min(ranks) if ranks else 0)
    seen = set(); gains = []
    for value in labels:
        gain = int(value in relevant and value not in seen); gains.append(gain); seen.add(value)
    dcg = sum(g / math.log2(rank + 1) for rank, g in enumerate(gains, 1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant), 5) + 1))
    ndcgs.append(dcg / ideal if ideal else 0)
    lines += [f"## Query {i}: {query}", f"- Top5 来源：{', '.join(labels)}",
              f"- 首个相关排名：{min(ranks) if ranks else '未命中'}", ""]
for query in irrelevant:
    rows = p.retrieval_service.retrieve(query, top_k=3)
    rejected = not rows; rejection_hits += int(rejected)
    lines += [f"## 领域外查询：{query}", f"- 已拒绝无依据检索：{rejected}", ""]
summary = ["## 汇总", f"- Recall@5：{recall_hits/len(queries):.3f}",
           f"- MRR：{sum(reciprocal)/len(reciprocal):.3f}", f"- nDCG@5：{sum(ndcgs)/len(ndcgs):.3f}",
           f"- 领域外拒答率：{rejection_hits/len(irrelevant):.3f}", ""]
Path(args.output).parent.mkdir(parents=True, exist_ok=True)
Path(args.output).write_text("\n".join(lines[:2] + summary + lines[2:]), encoding="utf-8")
print("\n".join(summary))

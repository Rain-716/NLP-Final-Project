import argparse, json, sys, time
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from src.config import AppConfig
from src.rag_pipeline import CodeAssistantPipeline

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="config_eval.yaml")
parser.add_argument("--test_file", default="tests/test_cases.json")
args = parser.parse_args()
pipeline = CodeAssistantPipeline(AppConfig.load(args.config))
cases = json.loads(Path(args.test_file).read_text(encoding="utf-8"))
results = []
for case in cases:
    start = time.time(); kind = case["type"]
    if kind == "explain": output = pipeline.explain_code(case["code"])
    elif kind == "qa": output = pipeline.answer_question(case["question"], case["code"])
    elif kind == "comment": output = pipeline.generate_comments(case["code"])
    elif kind == "knowledge": output = pipeline.search_knowledge(case["question"])[0]
    elif kind == "term": output = pipeline.term_explain(case["question"])[0]
    else: output = "未知测试类型"
    results.append({"name": case["name"], "type": kind, "elapsed": round(time.time()-start, 3),
                    "completed": "未完成请求" not in output, "output": output[:1800]})
Path("results").mkdir(exist_ok=True)
lines = ["# 功能验收结果", "", "> 本文件记录真实执行状态；本地模型或API未配置时不会计为通过。", ""]
for result in results:
    lines += [f"## {result['name']}", f"- 类型：{result['type']}", f"- 完成：{result['completed']}",
              f"- 耗时：{result['elapsed']} 秒", "", result["output"], ""]
Path("results/test_results.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps([{k:v for k,v in r.items() if k != "output"} for r in results], ensure_ascii=False, indent=2))

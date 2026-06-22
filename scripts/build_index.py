import argparse, json, sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.config import AppConfig
from src.rag_pipeline import CodeAssistantPipeline

parser = argparse.ArgumentParser(description="构建或增量更新本地知识索引")
parser.add_argument("--data_dir", default="data")
parser.add_argument("--config", default="config.yaml")
parser.add_argument("--reset", action="store_true", help="清空旧索引后全量重建")
args = parser.parse_args()

pipeline = CodeAssistantPipeline(AppConfig.load(args.config))
report = pipeline.build_index(args.data_dir, reset=args.reset)
print(json.dumps(report, ensure_ascii=False, indent=2))
if report["failures"]:
    print("\n以下文件未能入库：")
    for failure in report["failures"]:
        print("-", failure)

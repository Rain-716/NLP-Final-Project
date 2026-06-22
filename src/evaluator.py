from pathlib import Path
KEYWORDS = ['功能概述', '关键', '流程', '风险', '注释', '回答', '检索', '术语']
def score_output(text: str) -> dict:
    hit = sum(1 for k in KEYWORDS if k in text)
    return {'structure_score': round(hit / len(KEYWORDS), 2), 'length': len(text), 'passed': hit >= 3 and len(text) >= 120}
def save_markdown_results(results: list[dict], path: str | Path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    total = len(results); passed = sum(1 for r in results if r['score']['passed']); avg = sum(r['score']['structure_score'] for r in results) / max(1,total)
    lines = ['# 测试用例运行结果','',f'- 用例总数：{total}',f'- 通过数量：{passed}',f'- 平均结构化得分：{avg:.2f}','']
    for i, r in enumerate(results, 1):
        lines += [f'## 用例 {i}：{r["name"]}', '', f'- 类型：{r["type"]}', f'- 是否通过：{r["score"]["passed"]}', f'- 结构化得分：{r["score"]["structure_score"]}', f'- 响应时间：{r.get("elapsed", "-")} 秒', '', '### 输出节选', '', r['output'][:1600], '']
    path.write_text('\n'.join(lines), encoding='utf-8')

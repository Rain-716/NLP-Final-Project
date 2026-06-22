from pathlib import Path
import gradio as gr
from src.config import AppConfig
from src.rag_pipeline import CodeAssistantPipeline


cfg = AppConfig.load("config.yaml")
pipeline = CodeAssistantPipeline(cfg)

DEFAULT_CODE = r'''#include <bitset>
#include <cstdint>
struct RegisterFile {
    std::bitset<32> status;
    void setZeroFlag(bool value) { status[0] = value; }
    bool hasException() const { return status[3] == 1; }
};'''

PIPELINE_CODE = r'''struct PipeReg { int rd; bool regWrite; bool valid; };
bool hasRAW(const PipeReg& ex, int rs1, int rs2) {
    if (!ex.valid || !ex.regWrite) return false;
    return ex.rd != 0 && (ex.rd == rs1 || ex.rd == rs2);
}'''

with gr.Blocks(title="底层系统代码智能问答助手 v4", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 面向底层系统代码的智能问答与注释生成助手 v4")
    gr.Markdown("本地 Qwen 负责代码任务；本地知识库 + ChatECNU 负责知识问答与术语解释。")
    gr.Markdown(pipeline.status_markdown())

    with gr.Tab("代码解析"):
        with gr.Row():
            code_in = gr.Code(value=DEFAULT_CODE, language="cpp", label="C/C++ 代码", lines=24)
            explain_out = gr.Markdown(label="解析结果")
        with gr.Row():
            explain_btn = gr.Button("使用本地模型解析", variant="primary")
            comment_btn = gr.Button("使用本地模型生成注释")
        explain_btn.click(pipeline.explain_code, code_in, explain_out)
        comment_btn.click(pipeline.generate_comments, code_in, explain_out)

    with gr.Tab("代码问答"):
        with gr.Row():
            qa_code = gr.Code(value=PIPELINE_CODE, language="cpp", label="代码片段", lines=24)
            with gr.Column():
                question = gr.Textbox(label="问题", value="这段代码如何判断 RAW 相关性？")
                answer_btn = gr.Button("使用本地模型回答", variant="primary")
                answer = gr.Markdown(label="回答")
        answer_btn.click(pipeline.answer_question, [question, qa_code], answer)

    with gr.Tab("知识问答"):
        gr.Markdown("本地混合检索提供证据，ChatECNU 负责重排和带引用回答。")
        knowledge_q = gr.Textbox(label="知识问题", value="Cache 地址如何拆分 tag、index 和 offset？")
        knowledge_btn = gr.Button("检索并回答", variant="primary")
        knowledge_answer = gr.Markdown(label="知识回答")
        with gr.Accordion("查看本地检索证据", open=False):
            knowledge_evidence = gr.Markdown()
        knowledge_btn.click(pipeline.search_knowledge, knowledge_q, [knowledge_answer, knowledge_evidence])

    with gr.Tab("术语解释"):
        term_text = gr.Textbox(label="问题、代码或术语", value="pipeline hazard stall forwarding cache miss dirty bit")
        term_btn = gr.Button("调用 ChatECNU 解释", variant="primary")
        term_answer = gr.Markdown(label="术语解释")
        with gr.Accordion("查看解释依据", open=False):
            term_evidence = gr.Markdown()
        term_btn.click(pipeline.term_explain, term_text, [term_answer, term_evidence])

    with gr.Tab("项目说明"):
        readme = Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else ""
        gr.Markdown(readme[:12000])

if __name__ == "__main__":
    demo.launch()

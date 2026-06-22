# 检索评测结果

## 汇总
- Recall@5：1.000
- MRR：1.000
- nDCG@5：0.968
- 领域外拒答率：1.000

## Query 1: 流水线 RAW 冒险如何通过 forwarding 或 stall 处理
- Top5 来源：local-system-terms, local-architecture-notes, local-pipeline-notes, docs/rag_design.md, local-system-terms
- 首个相关排名：1

## Query 2: load-use 为什么需要插入 bubble
- Top5 来源：local-pipeline-notes, local-architecture-notes, local-system-terms, local-pipeline-notes, docs/rag_design.md
- 首个相关排名：1

## Query 3: Cache 地址如何拆分 tag index offset
- Top5 来源：local-system-terms, docs/cache_manual.md, local-cache-notes, code_examples/cache_sim.cpp, local-cache-notes
- 首个相关排名：1

## Query 4: RISC-V opcode funct3 funct7 如何译码
- Top5 来源：local-riscv-notes, local-system-terms, local-architecture-notes, local-riscv-notes, local-riscv-notes
- 首个相关排名：1

## Query 5: std::bitset 如何表示寄存器状态位
- Top5 来源：local-system-terms, local-cpp-notes, docs/system_cpp_notes.md, code_examples/bitset_register.cpp, local-system-terms
- 首个相关排名：1

## 领域外查询：法国大革命发生在哪一年
- 已拒绝无依据检索：True

## 领域外查询：如何烘焙巧克力蛋糕
- 已拒绝无依据检索：True

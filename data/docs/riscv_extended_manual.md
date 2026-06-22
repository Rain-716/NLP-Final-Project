# riscv_extended_manual

## 1. RISC-V R 型指令译码

R 型指令主要用于寄存器到寄存器运算，字段包括 opcode、rd、funct3、rs1、rs2、funct7。阅读译码代码时应关注每个字段的移位和 mask 是否正确，例如 opcode 使用 inst & 0x7f，rd 使用 (inst >> 7) & 0x1f。funct3 和 funct7 通常共同区分 ADD/SUB、SRL/SRA 等指令。

关键词：RISC、V、R、型指令译码

## 2. RISC-V I 型指令立即数

I 型指令包含 12 位立即数，通常位于 inst[31:20]。代码中如果直接右移得到 imm，需要注意符号扩展，否则负数偏移、加载地址和 jalr 目标地址可能解释错误。问答系统检索到该片段时应提示“位段拼接 + sign extension”。

关键词：RISC、V、I、型指令立即数

## 3. RISC-V S 型指令立即数拼接

S 型指令用于 store，立即数被拆成 imm[11:5] 和 imm[4:0] 两段，分别位于 inst[31:25] 与 inst[11:7]。代码阅读重点是两段是否正确左移并按位或，最后是否进行 12 位符号扩展。

关键词：RISC、V、S、型指令立即数拼接

## 4. RISC-V B 型分支偏移

B 型分支立即数的编码不是连续字段，需要从 inst[31]、inst[7]、inst[30:25]、inst[11:8] 拼接，并且最低位隐含为 0。分支目标地址通常为 pc + imm，控制冒险需要 flush 或预测恢复。

关键词：RISC、V、B、型分支偏移

## 5. RISC-V U 型高位立即数

LUI/AUIPC 使用 U 型格式，立即数位于 inst[31:12] 并左移 12 位。AUIPC 会将该立即数与 PC 相加，常用于位置无关寻址。代码中应区分 LUI 直接写 rd 和 AUIPC 使用 pc。

关键词：RISC、V、U、型高位立即数

## 6. RISC-V J 型跳转偏移

JAL 使用 J 型立即数，字段分散在 inst[31]、inst[19:12]、inst[20]、inst[30:21]，最低位隐含为 0。解析代码需要检查拼接顺序和符号扩展，错误会导致跳转目标偏移异常。

关键词：RISC、V、J、型跳转偏移

## 7. 指令控制信号生成

译码阶段通常根据 opcode/funct3/funct7 生成 RegWrite、MemRead、MemWrite、Branch、ALUSrc、MemToReg 等控制信号。代码问答时需要说明这些布尔变量不是普通业务标志，而是硬件数据通路控制线。

关键词：指令控制信号生成

## 8. ALU 控制译码

ALU 控制逻辑把高层 ALUOp 与 funct 字段转换为具体运算，如 add、sub、and、or、slt、sll、srl。阅读代码时应检查默认分支是否安全，未知指令是否产生非法指令异常。

关键词：ALU、控制译码

## 9. 寄存器堆读写时序

寄存器堆通常在 ID 阶段读 rs1/rs2，在 WB 阶段写 rd。若同一周期既读又写同一寄存器，模拟器需要定义先写后读还是先读后写。RAG 回答应提示该行为依赖实验约定。

关键词：寄存器堆读写时序

## 10. x0 零寄存器保护

RISC-V 的 x0 始终为 0，代码中即使 rd==0 也不应该真正写入。冒险检测也常排除 rd==0，因为写 x0 不产生有效数据相关。

关键词：x0、零寄存器保护

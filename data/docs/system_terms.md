# 底层系统代码术语库（扩展版）

本知识库面向计算机组成原理、体系结构、操作系统和系统级 C++ 代码阅读场景。系统在检索前会识别用户问题中的中文/英文术语，并将其扩展为别名集合。

## 流水线基础
pipeline 流水线通常包含 IF、ID、EX、MEM、WB 五个阶段。IF 负责取指，ID 负责译码和读寄存器，EX 负责 ALU 运算或地址计算，MEM 负责访存，WB 负责写回寄存器。阅读流水线代码时应关注每个阶段寄存器在当前周期和下一周期如何更新。

## 数据冒险
hazard 冒险指流水线中指令之间存在依赖或资源冲突。RAW 是最常见的数据冒险，后一条指令需要读取前一条指令尚未写回的结果。常见解决方式包括 forwarding 旁路转发和 stall 停顿。

## 停顿和气泡
stall 表示冻结某些流水线阶段，使其暂时不推进。bubble 气泡表示向后续阶段插入一条无效操作，避免错误指令修改状态。代码中常见 valid=false、nop=true、enable=false 等写法。

## 旁路转发
forwarding 或 bypass 是将 EX/MEM/WB 阶段的结果直接转给需要它的后续指令。典型判断条件是前序指令 regWrite==true，且 rd != 0，并且 rd == rs1 || rd == rs2。

## 控制冒险
branch 分支指令会改变 PC，导致已经取出的后续指令可能无效。简单流水线可能使用 flush 清空错误路径指令，也可能使用 branch prediction 预测分支方向。

## Cache 地址拆分
Cache 访问通常将地址拆分为 tag、index 和 offset。offset 定位块内字节，index 选择 cache line 或 set，tag 用于判断该行是否对应目标内存块。直接映射 Cache 中 index 决定唯一位置，组相联 Cache 中 index 决定组，组内再比较多个 tag。

## Cache 状态位
valid 位表示 cache line 是否包含有效数据，dirty 位表示该行是否被修改但尚未写回内存。write back 策略在替换 dirty line 时需要写回；write through 策略每次写入同时更新内存。

## RISC-V 指令字段
RISC-V 指令常见字段包括 opcode、funct3、funct7、rs1、rs2、rd、imm。opcode 决定大类，funct3/funct7 进一步区分 ADD、SUB、AND、OR、SLL 等操作，rd 表示目的寄存器，rs1 和 rs2 表示源寄存器。

## C++ bitset 与寄存器位域
std::bitset<N> 是固定宽度位集合，经常用于模拟寄存器状态位、valid/dirty 数组、控制信号集合。注意 bitset 下标从 0 开始，bits[0] 表示最低位。生成注释时应解释每一位的硬件含义，而不只是说明“访问数组”。

## 静态风险检查
底层系统代码常见风险包括：数组下标越界、bitset 位宽不匹配、current/next 状态混淆、Cache dirty 位未写回、流水线 stall 和 flush 优先级冲突、指针释放不完整、异常路径没有恢复状态。

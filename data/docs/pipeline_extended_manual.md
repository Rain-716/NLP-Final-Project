# pipeline_extended_manual

## 1. 五级流水线阶段职责

经典五级流水线包括 IF 取指、ID 译码/读寄存器、EX 执行/地址计算、MEM 访存、WB 写回。代码中 IFID、IDEX、EXMEM、MEMWB 等结构体通常对应阶段寄存器。

关键词：五级流水线阶段职责

## 2. 流水线寄存器 current/next 设计

为了模拟时钟边沿，推荐使用 current 与 next 两套状态：先基于 current 计算所有组合逻辑，再统一提交 next。若在同一函数中直接覆盖 current，可能把本周期后半段结果错误提供给前半段。

关键词：流水线寄存器、current/next、设计

## 3. RAW 数据冒险检测

RAW 冒险检测通常比较 ID 阶段 rs1/rs2 与 EX/MEM/WB 阶段 rd，并要求上游指令 valid 且 regWrite 为真。rd==0 应排除。

关键词：RAW、数据冒险检测

## 4. load-use 冒险

load 指令的数据通常到 MEM 结束后才可用，紧随其后的消费者即使用 forwarding 也可能来不及，需要 stall 一个周期并向 EX 阶段插入 bubble。

关键词：load、use、冒险

## 5. forwarding 选择优先级

若 EX/MEM 和 MEM/WB 都能向同一源操作数转发，通常 EX/MEM 更新，优先级更高。代码中 forwardA/forwardB 的判断顺序会直接影响结果。

关键词：forwarding、选择优先级

## 6. stall 控制信号

典型 stall 会冻结 PC 和 IF/ID 寄存器，同时向 ID/EX 插入 bubble。代码变量常见为 pcWrite=false、ifidWrite=false、idexFlush=true。

关键词：stall、控制信号

## 7. flush 控制信号

分支跳转或异常发生后，需要清空错误路径上的流水线寄存器。flush 与 stall 同时发生时要定义优先级，否则可能保留了错误指令。

关键词：flush、控制信号

## 8. 分支预测与恢复

如果系统采用静态不跳预测，分支在 EX 阶段确定后若实际跳转，需要将 IF/ID、ID/EX 中错误路径指令 flush，并更新 PC。

关键词：分支预测与恢复

## 9. 结构冒险

结构冒险来自硬件资源冲突，例如指令存储器和数据存储器共用单端口存储器。模拟代码若分离 ICache/DCache，则通常不会出现该冲突。

关键词：结构冒险

## 10. 异常与精确提交

底层模拟器中异常处理需要保证之前指令提交、之后指令不提交。流水线代码中要关注 valid、exception、commit 等标志位是否在 flush 时正确传播。

关键词：异常与精确提交

## 11. 流水线 valid 位

valid 位表示阶段寄存器中的指令是否真实有效。bubble 通常就是 valid=false 的阶段寄存器。解释代码时应把 valid 与普通布尔变量区分开。

关键词：流水线、valid、位

## 12. 多周期功能单元

乘除法或访存可能占用多个周期，流水线需要通过 busy/stall 控制阻塞后续阶段。若代码忽略 busy，可能只适合单周期执行单元。

关键词：多周期功能单元

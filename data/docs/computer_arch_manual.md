# 计算机组成原理实验手册知识片段

## 五级流水线寄存器
五级流水线常用 IF/ID、ID/EX、EX/MEM、MEM/WB 四组流水线寄存器保存阶段之间的状态。每组寄存器通常包含 PC、instruction、rs1、rs2、rd、imm、control signals 和 valid 位。

## RAW 冒险检测
RAW 冒险检测通常比较 ID 阶段源寄存器 rs1、rs2 与 EX/MEM/WB 阶段目的寄存器 rd。如果前序指令将写寄存器，并且 rd 非零，同时 rd 等于当前指令源寄存器，则存在数据相关。

## load-use 冒险
load-use 冒险是特殊 RAW 冒险。load 指令的数据在 MEM 阶段末尾才可用，紧随其后的指令即使使用 forwarding 也可能来不及，需要至少 stall 一个周期。

## flush 优先级
当分支预测错误或异常发生时，flush 的优先级通常高于普通 stall。否则错误路径上的指令可能继续向后流动并修改寄存器或内存状态。

## current 和 next 状态
模拟器中常用 current 表示当前周期状态，用 next 表示下一周期状态。一个周期内应先基于 current 计算所有 next，最后统一提交。若边计算边修改 current，会造成时序不符合真实硬件。

## 寄存器 x0
RISC-V 的 x0 恒为 0，不能被真正写入。冒险检测和写回逻辑通常需要判断 rd != 0，避免把 x0 当成普通寄存器产生伪相关。

## ALU 控制信号
译码阶段根据 opcode、funct3、funct7 生成 ALU 控制信号。R-type 指令中 ADD 和 SUB 可能 opcode/funct3 相同，需要通过 funct7 区分。

## 访存控制信号
load/store 指令需要生成 memRead、memWrite、memToReg、byteEnable 等控制信号。访存地址通常由 rs1 + imm 计算，低位决定字节偏移。

## 异常和中断
异常处理会保存异常 PC 和原因，更新 CSR，并跳转到 trap handler。流水线需要阻止异常之后的错误指令提交。

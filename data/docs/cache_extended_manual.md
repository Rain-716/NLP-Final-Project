# cache_extended_manual

## 1. 直接映射 Cache

直接映射 Cache 每个内存块只能映射到一个 cache line，index 直接选择行，tag 判断是否命中。优点是实现简单，缺点是冲突未命中较多。

关键词：直接映射、Cache

## 2. 组相联 Cache

组相联 Cache 使用 index 选择 set，在 set 内遍历多个 way 比较 tag。代码中二维数组 cache[set][way] 很常见，替换策略只在同一 set 内选择 victim。

关键词：组相联、Cache

## 3. 全相联 Cache

全相联 Cache 没有传统 index，任意内存块可放入任意 line，需要比较所有 tag。检索到该知识时应提示硬件代价高但冲突少。

关键词：全相联、Cache

## 4. tag index offset 位段

地址拆分通常依据 block size、set 数和地址位宽计算 offsetBits、indexBits、tagBits。错误的 mask 或位移会导致命中判断错乱。

关键词：tag、index、offset、位段

## 5. valid 位冷启动

Cache 初始化时所有 line valid=false。若代码不检查 valid 而只比较 tag，空行默认 tag=0 时可能把地址 0 误判为命中。

关键词：valid、位冷启动

## 6. dirty 位与写回

写回策略下 store 命中只修改 Cache 并置 dirty，替换脏行前必须写回内存。实现时应结合替换路径检查 dirty 行是否先写回内存。

关键词：dirty、位与写回

## 7. write through 策略

写直达策略每次写 Cache 同时写内存，可以不依赖 dirty 位，但写流量更大，常配合 write buffer 减少阻塞。

关键词：write、through、策略

## 8. write allocate 策略

写未命中时若采用 write allocate，会先把块加载进 Cache 再写；若 no-write-allocate，则直接写内存。代码问答应说明策略差异会影响 miss 处理流程。

关键词：write、allocate、策略

## 9. LRU 替换策略

LRU 用 lastUse 时间戳或队列记录访问新旧，替换时选择最久未使用的 way。代码应在命中和装入时都更新 lastUse。

关键词：LRU、替换策略

## 10. FIFO 替换策略

FIFO 按进入 Cache 的先后顺序替换，不考虑近期访问。相比 LRU 实现简单，但可能替换掉热点数据。

关键词：FIFO、替换策略

## 11. 随机替换策略

随机替换不维护复杂状态，适合简单模拟器或近似硬件；实验报告中应说明结果具有随机性，评测时固定随机种子。

关键词：随机替换策略

## 12. Cache 性能指标

常见指标包括 hit rate、miss rate、AMAT。AMAT = hit time + miss rate × miss penalty，可用于分析 Cache 参数变化对性能的影响。

关键词：Cache、性能指标

## 13. 块大小影响

增大 block size 可利用空间局部性，但也会减少 line 数量并可能增加冲突未命中。代码中 blockSize 需要是 2 的幂以简化 offset 计算。

关键词：块大小影响

## 14. 多级 Cache

L1/L2 Cache 模拟需要定义 inclusive/exclusive 策略以及 L1 miss 后访问 L2 的流程。回答时应区分单级 Cache 与多级 Cache。

关键词：多级、Cache

## 15. Cache 一致性

多核系统中多个 cache 可能保存同一内存块，写操作需要一致性协议维护共享状态。简单单核课程实验通常可忽略该问题。

关键词：Cache、一致性

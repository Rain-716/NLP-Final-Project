# Cache 模拟器知识片段

## 直接映射 Cache
直接映射 Cache 中，每个内存块只能放入唯一 cache line。index 从地址中取出，用于定位行；tag 与行中保存的 tag 比较；valid 位为真且 tag 相等时命中。

## 组相联 Cache
组相联 Cache 中，一个 index 对应一个 set，set 内有多个 way。访问时需要并行比较所有 way 的 tag。替换策略可以是 LRU、FIFO、随机或 PLRU。

## LRU 替换策略
LRU 使用最近访问时间或计数器判断哪一行最久未使用。每次命中或填充都要更新该行的时间戳。实现时常见错误是只在 miss 时更新，而忘记 hit 时更新。

## write back 和 dirty 位
write back 策略中，写命中只修改 Cache 并设置 dirty 位。若 dirty line 被替换，需要先把旧数据写回内存。若忘记写回，模拟器可能在测试中表现为偶发数据错误。

## write allocate
write allocate 表示写 miss 时先把内存块加载到 Cache，再执行写入。no-write-allocate 则写 miss 时直接写内存，不分配 Cache 行。

## 地址位宽计算
若块大小为 block_size，则 offset 位数为 log2(block_size)。若 set 数为 num_sets，则 index 位数为 log2(num_sets)。tag 是剩余高位。实现时应确认 block_size 和 num_sets 为 2 的幂。

## Cache 代码常见风险
Cache 模拟代码中常见风险包括 index 计算没有 mask、tag 位移错误、valid 初始值未设置、dirty 替换不写回、LRU 更新时间遗漏、块大小不是 2 的幂却使用移位计算。

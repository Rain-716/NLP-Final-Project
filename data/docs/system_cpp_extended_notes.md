# system_cpp_extended_notes

## 1. std::bitset 固定位宽

std::bitset<N> 的位宽在编译期确定，适合寄存器位、控制信号、valid/dirty 集合。下标从 0 开始，访问 flags[N] 属于越界风险。

关键词：std::bitset、固定位宽

## 2. 位运算提取字段

底层代码常用 >> 和 & 提取地址或指令字段。应优先定义常量 mask，例如 OPCODE_MASK=0x7f，避免魔法数字影响可读性。

关键词：位运算提取字段

## 3. 无符号整数与溢出

地址、指令字和寄存器内容通常使用 uint32_t/uint64_t。无符号溢出按模运算定义，而有符号溢出在 C++ 中可能是未定义行为。

关键词：无符号整数与溢出

## 4. 指针下标风险

a[idx] 在语法上等价于 *(a+idx)，若没有边界检查就可能越界。阅读代码时应结合 size 或范围条件确认下标有效。

关键词：指针下标风险

## 5. 引用与常量引用

const T& 常用于避免拷贝且保证不修改对象。底层模拟器中阶段寄存器传参若需要修改，不能使用 const 引用。

关键词：引用与常量引用

## 6. 结构体默认初始化

struct StageReg { int rd=0; bool valid=false; } 可避免未初始化状态造成随机冒险检测结果。课程代码中建议显式给控制信号默认值。

关键词：结构体默认初始化

## 7. enum class 表示状态

流水线阶段、Cache 状态或指令类型可用 enum class 表示，提升可读性并避免普通 int 魔法值。

关键词：enum、class、表示状态

## 8. vector 二维表

Cache set/way 或寄存器文件可用 vector 嵌套表示。访问 vector 前应确认 set index 和 way index 在合法范围内。

关键词：vector、二维表

## 9. 智能指针

若项目手动 new/delete 管理模拟器部件，容易遗漏释放。现代 C++ 推荐 unique_ptr/shared_ptr 表达所有权关系。

关键词：智能指针

## 10. RAII 资源管理

RAII 通过对象生命周期管理文件、内存或锁，异常路径也能自动释放资源。底层项目中可用于日志文件和内存缓冲区。

关键词：RAII、资源管理

## 11. const correctness

不会修改对象的成员函数应标记 const，例如 bool hit(...) const。这样有助于区分查询逻辑和状态更新逻辑。

关键词：const、correctness

## 12. 断言与边界检查

assert 可用于检查不变量，例如 index < sets.size()、rd < 32。发布版本仍需保留必要运行时检查。

关键词：断言与边界检查

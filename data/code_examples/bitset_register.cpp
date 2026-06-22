#include <bitset>
#include <cstdint>
class CSRRegister {
public:
    std::bitset<32> value;
    void setInterruptEnable(bool enable) { value[3] = enable; }
    bool interruptEnabled() const { return value[3]; }
    uint32_t toUInt() const { return static_cast<uint32_t>(value.to_ulong()); }
};

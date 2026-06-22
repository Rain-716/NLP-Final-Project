#include <cstdint>
struct DecodedInst {
    uint32_t opcode;
    uint32_t rd;
    uint32_t funct3;
    uint32_t rs1;
    uint32_t rs2;
    uint32_t funct7;
};
DecodedInst decodeRType(uint32_t inst) {
    DecodedInst d{};
    d.opcode = inst & 0x7f;
    d.rd = (inst >> 7) & 0x1f;
    d.funct3 = (inst >> 12) & 0x7;
    d.rs1 = (inst >> 15) & 0x1f;
    d.rs2 = (inst >> 20) & 0x1f;
    d.funct7 = (inst >> 25) & 0x7f;
    return d;
}
bool isSub(const DecodedInst& d) {
    return d.opcode == 0x33 && d.funct3 == 0x0 && d.funct7 == 0x20;
}

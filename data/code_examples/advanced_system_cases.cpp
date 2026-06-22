
#include <cstdint>
#include <vector>
#include <bitset>
using std::uint32_t;
using std::uint64_t;

struct ControlSignals {
    bool regWrite = false;
    bool memRead = false;
    bool memWrite = false;
    bool branch = false;
    bool aluSrc = false;
};

ControlSignals decodeOpcode(uint32_t opcode) {
    ControlSignals c;
    if (opcode == 0x33) { c.regWrite = true; }
    else if (opcode == 0x03) { c.regWrite = true; c.memRead = true; c.aluSrc = true; }
    else if (opcode == 0x23) { c.memWrite = true; c.aluSrc = true; }
    else if (opcode == 0x63) { c.branch = true; }
    return c;
}

int signExtend12(uint32_t imm) {
    if (imm & 0x800) return (int)(imm | 0xfffff000);
    return (int)imm;
}

uint32_t decodeSTypeImm(uint32_t inst) {
    uint32_t imm11_5 = (inst >> 25) & 0x7f;
    uint32_t imm4_0 = (inst >> 7) & 0x1f;
    return (imm11_5 << 5) | imm4_0;
}

uint32_t decodeBTypeImm(uint32_t inst) {
    uint32_t bit12 = (inst >> 31) & 0x1;
    uint32_t bit11 = (inst >> 7) & 0x1;
    uint32_t bits10_5 = (inst >> 25) & 0x3f;
    uint32_t bits4_1 = (inst >> 8) & 0xf;
    return (bit12 << 12) | (bit11 << 11) | (bits10_5 << 5) | (bits4_1 << 1);
}

struct PipelineReg {
    int rd = 0;
    bool valid = false;
    bool regWrite = false;
    bool memRead = false;
};

bool needForwardFromEXMEM(const PipelineReg& exmem, int rs) {
    return exmem.valid && exmem.regWrite && exmem.rd != 0 && exmem.rd == rs;
}

bool needForwardFromMEMWB(const PipelineReg& memwb, int rs) {
    return memwb.valid && memwb.regWrite && memwb.rd != 0 && memwb.rd == rs;
}

int selectForwarding(bool exHit, bool memHit) {
    if (exHit) return 2;
    if (memHit) return 1;
    return 0;
}

bool detectLoadUse(const PipelineReg& idex, int rs1, int rs2) {
    return idex.valid && idex.memRead && idex.rd != 0 && (idex.rd == rs1 || idex.rd == rs2);
}

struct CacheAddress {
    uint64_t tag;
    uint64_t index;
    uint64_t offset;
};

CacheAddress splitAddress(uint64_t addr, int offsetBits, int indexBits) {
    uint64_t offsetMask = (1ULL << offsetBits) - 1;
    uint64_t indexMask = (1ULL << indexBits) - 1;
    CacheAddress a;
    a.offset = addr & offsetMask;
    a.index = (addr >> offsetBits) & indexMask;
    a.tag = addr >> (offsetBits + indexBits);
    return a;
}

struct CacheLineV3 {
    bool valid = false;
    bool dirty = false;
    uint64_t tag = 0;
    int lastUse = 0;
};

int findInvalidWay(const std::vector<CacheLineV3>& set) {
    for (int i = 0; i < (int)set.size(); ++i) if (!set[i].valid) return i;
    return -1;
}

int chooseLRUVictim(const std::vector<CacheLineV3>& set) {
    int victim = 0;
    for (int i = 1; i < (int)set.size(); ++i) if (set[i].lastUse < set[victim].lastUse) victim = i;
    return victim;
}

void markStoreHit(CacheLineV3& line, int now) {
    line.dirty = true;
    line.lastUse = now;
}

struct CSRFlags {
    std::bitset<32> mstatus;
    void setInterruptEnable(bool enable) { mstatus[3] = enable; }
    bool interruptEnable() const { return mstatus[3]; }
};

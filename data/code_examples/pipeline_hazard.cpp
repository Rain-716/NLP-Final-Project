struct StageReg {
    int rd;
    bool regWrite;
    bool memRead;
    bool valid;
};
bool rawHazard(const StageReg& ex, int rs1, int rs2) {
    if (!ex.valid || !ex.regWrite) return false;
    if (ex.rd == 0) return false;
    return ex.rd == rs1 || ex.rd == rs2;
}
bool loadUseHazard(const StageReg& ex, int rs1, int rs2) {
    return ex.valid && ex.memRead && ex.rd != 0 && (ex.rd == rs1 || ex.rd == rs2);
}
void applyStall(bool hazard, bool& pcWrite, bool& ifidWrite, bool& idexBubble) {
    pcWrite = !hazard;
    ifidWrite = !hazard;
    idexBubble = hazard;
}

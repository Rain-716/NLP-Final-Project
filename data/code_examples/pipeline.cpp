struct StageReg {
    int rd = 0;
    int rs1 = 0;
    int rs2 = 0;
    bool regWrite = false;
    bool memRead = false;
};
bool hasLoadUseHazard(const StageReg& id, const StageReg& ex) {
    if (!ex.memRead) return false;
    return ex.rd != 0 && (ex.rd == id.rs1 || ex.rd == id.rs2);
}
void updatePipeline(bool hazard, bool& stall, bool& insertBubble) {
    if (hazard) { stall = true; insertBubble = true; }
    else { stall = false; insertBubble = false; }
}

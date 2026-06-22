#include <vector>
#include <cstdint>
struct Line {
    bool valid = false;
    bool dirty = false;
    uint64_t tag = 0;
    int lastUse = 0;
};
int findWay(std::vector<Line>& set, uint64_t tag, int now) {
    for (int i = 0; i < (int)set.size(); ++i) {
        if (set[i].valid && set[i].tag == tag) {
            set[i].lastUse = now;
            return i;
        }
    }
    return -1;
}
int chooseVictim(const std::vector<Line>& set) {
    int victim = 0;
    for (int i = 1; i < (int)set.size(); ++i) {
        if (!set[i].valid) return i;
        if (set[i].lastUse < set[victim].lastUse) victim = i;
    }
    return victim;
}

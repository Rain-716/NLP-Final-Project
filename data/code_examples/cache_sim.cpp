#include <vector>
#include <cstdint>
struct CacheLine { bool valid = false; uint32_t tag = 0; };
bool accessCache(std::vector<CacheLine>& cache, uint32_t addr) {
    uint32_t index = (addr >> 4) % cache.size();
    uint32_t tag = addr >> 10;
    if (cache[index].valid && cache[index].tag == tag) {
        return true;
    }
    cache[index].valid = true;
    cache[index].tag = tag;
    return false;
}

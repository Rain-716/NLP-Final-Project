from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TermInfo:
    name: str
    zh: str
    desc: str
    aliases: tuple[str, ...]
    category: str = '系统术语'

TERMS: dict[str, TermInfo] = {
    'pipeline': TermInfo('pipeline', '流水线', '将指令执行拆分为 IF/ID/EX/MEM/WB 等阶段，通过并行重叠提高吞吐率。', ('流水线','IF','ID','EX','MEM','WB','stage','pipeline register'), '体系结构'),
    'hazard': TermInfo('hazard', '流水线冒险', '数据、控制或结构资源冲突导致下一条指令无法按理想周期推进。', ('冒险','冲突','RAW','WAR','WAW','control hazard','data hazard','structural hazard'), '体系结构'),
    'raw hazard': TermInfo('raw hazard', '读后写冒险', '后一条指令读取前一条尚未写回的结果，可能需要 forwarding 或 stall。', ('RAW','read after write','数据相关','load-use'), '体系结构'),
    'stall': TermInfo('stall', '停顿/气泡', '为了等待数据或资源而冻结某些流水线寄存器，常伴随插入 bubble。', ('暂停','停顿','气泡','bubble','freeze','pcWrite','ifidWrite'), '体系结构'),
    'forwarding': TermInfo('forwarding', '旁路/转发', '将 EX/MEM/WB 阶段产生的结果提前送给后续指令，减少数据冒险。', ('旁路','转发','bypass','forward','forwardA','forwardB'), '体系结构'),
    'flush': TermInfo('flush', '流水线刷新', '在分支预测错误或异常时清空错误路径上的指令，避免错误提交状态。', ('刷新','清空','kill','squash'), '体系结构'),
    'branch': TermInfo('branch', '分支', '根据条件改变 PC，可能造成控制冒险和错误取指。', ('分支','jump','跳转','branch prediction','control hazard'), '体系结构'),
    'pc': TermInfo('pc', '程序计数器', '保存当前或下一条指令地址，分支、跳转和异常会改变其更新路径。', ('程序计数器','next_pc','npc','pcWrite'), '体系结构'),
    'risc-v': TermInfo('risc-v', 'RISC-V', '开源精简指令集架构，常见字段包括 opcode、funct3、funct7、rs1、rs2、rd、imm。', ('riscv','opcode','funct3','funct7','rs1','rs2','rd','imm','RV32I'), '指令集'),
    'opcode': TermInfo('opcode', '操作码', '指令中表示操作类型的字段，决定译码后的控制信号。', ('操作码','op','instruction decode','decode'), '指令集'),
    'funct3': TermInfo('funct3', '三位功能码', 'RISC-V 指令字段之一，常与 opcode、funct7 共同确定具体运算。', ('功能码','function3'), '指令集'),
    'funct7': TermInfo('funct7', '七位功能码', 'R 型指令字段之一，用于区分 add/sub、srl/sra 等同 opcode/funct3 下的不同操作。', ('function7','sub bit'), '指令集'),
    'imm': TermInfo('imm', '立即数', '编码在指令中的常量，需要按指令格式拼接并符号扩展。', ('立即数','sign extend','sext','offset'), '指令集'),
    'alu': TermInfo('alu', '算术逻辑单元', '执行加减、与或、比较、移位等运算，是 EX 阶段的核心部件。', ('算术逻辑单元','add','sub','and','or','shift','compare'), '硬件部件'),
    'register': TermInfo('register', '寄存器', 'CPU 内部高速存储单元，用于保存操作数、地址、状态或控制信号。', ('寄存器','reg','register file','rf','rd','rs1','rs2'), '硬件部件'),
    'csr': TermInfo('csr', '控制状态寄存器', 'RISC-V 中保存异常、中断、权限级和机器状态的特殊寄存器。', ('控制状态寄存器','mstatus','mtvec','mepc','mcause','mie','mip'), '指令集'),
    'bitset': TermInfo('bitset', '位集合/位域', 'C++ STL 中固定长度位集合，常用于模拟寄存器位、valid/dirty 标志或控制信号。', ('std::bitset','位集合','位域','flag','mask','status bit'), 'C++'),
    'mask': TermInfo('mask', '位掩码', '通过与、或、移位等操作提取或设置特定位段。', ('掩码','bit mask','&','|','<<','>>'), 'C++'),
    'cache': TermInfo('cache', '高速缓存', '利用局部性保存近期访问的数据，典型字段包括 tag、index、offset、valid、dirty。', ('缓存','cache line','tag','index','offset','valid','dirty','set associative'), '存储系统'),
    'cache miss': TermInfo('cache miss', '缓存未命中', '访问的数据不在 Cache 中，需要从低层存储加载，带来额外延迟。', ('miss','未命中','compulsory miss','capacity miss','conflict miss'), '存储系统'),
    'cache hit': TermInfo('cache hit', '缓存命中', '目标块已经在 Cache 中，访问延迟较低。', ('hit','命中','hit rate'), '存储系统'),
    'tag': TermInfo('tag', '标记字段', '地址高位字段，用于判断 cache 行保存的是哪一个内存块。', ('标记','标签','tag match'), '存储系统'),
    'index': TermInfo('index', '索引字段', '地址中的组/行选择字段，用于定位 cache set 或 line。', ('索引','set index'), '存储系统'),
    'offset': TermInfo('offset', '块内偏移', '地址低位字段，用于选择 cache line 内的字节或字。', ('偏移','block offset','byte offset'), '存储系统'),
    'valid bit': TermInfo('valid bit', '有效位', '标识 cache 行或流水线寄存器是否保存有效内容。', ('valid','有效位','valid flag'), '存储系统'),
    'dirty bit': TermInfo('dirty bit', '脏位', '标识 cache 行是否被修改，写回策略下替换前需要写回内存。', ('dirty','脏位','modified'), '存储系统'),
    'write back': TermInfo('write back', '写回策略', '修改数据先写 Cache 并置 dirty，替换时再写回内存。', ('写回','dirty bit','writeback','write-back'), '存储系统'),
    'write through': TermInfo('write through', '写直达策略', '写 Cache 同时写内存，简单但写流量更大。', ('写直达','write-through'), '存储系统'),
    'lru': TermInfo('lru', '最近最少使用替换', '优先替换最近最久未被访问的 cache 行。', ('最近最少使用','least recently used','lastUse','victim'), '存储系统'),
    'tlb': TermInfo('tlb', '快表', '缓存虚拟页号到物理页号的地址转换结果，减少页表访问开销。', ('快表','translation lookaside buffer','vpn','ppn'), '操作系统'),
    'dma': TermInfo('dma', '直接内存访问', '外设绕过 CPU 直接与内存交换数据，常涉及缓存一致性问题。', ('直接内存访问','cache coherence'), '操作系统'),
    'mutex': TermInfo('mutex', '互斥锁', '保证共享数据在同一时刻只被一个线程访问，避免竞态条件。', ('互斥','lock','unlock','race condition'), '并发'),
    'interrupt': TermInfo('interrupt', '中断', '外部或内部事件打断正常执行流，保存现场后跳转到处理程序。', ('中断','exception','trap','handler','interrupt enable'), '操作系统'),
    'endianness': TermInfo('endianness', '字节序', '多字节数据在内存中的排列顺序，常见小端和大端。', ('大小端','little endian','big endian'), '系统编程'),
    'alignment': TermInfo('alignment', '内存对齐', '数据地址按类型大小或体系结构约束对齐，可影响性能或导致异常。', ('对齐','align','aligned','misaligned'), '系统编程'),
}

_ALIAS_TO_KEY: dict[str, str] = {}
for key, info in TERMS.items():
    _ALIAS_TO_KEY[key.lower()] = key
    _ALIAS_TO_KEY[info.zh.lower()] = key
    for alias in info.aliases:
        _ALIAS_TO_KEY[alias.lower()] = key

def extract_terms(text: str) -> list[TermInfo]:
    import re
    raw = text or ''
    low = raw.lower()
    hit_keys: list[str] = []
    ambiguous = {'if', 'id', 'ex', 'mem', 'wb', 'add', 'sub', 'and', 'or'}
    # 先查长别名，避免 branch 被 branch prediction 片段干扰；
    # 对短英文缩写使用词边界，并跳过 if/and/or 等与编程语法冲突的词。
    for alias, key in sorted(_ALIAS_TO_KEY.items(), key=lambda x: len(x[0]), reverse=True):
        if not alias or key in hit_keys:
            continue
        if alias in {'&', '|', '<<', '>>'}:
            continue
        a = alias.lower()
        if a in ambiguous:
            continue
        if re.fullmatch(r'[a-z0-9_\-]+', a):
            if re.search(r'(?<![a-z0-9_])' + re.escape(a) + r'(?![a-z0-9_])', low):
                hit_keys.append(key)
        elif a in low:
            hit_keys.append(key)
    return [TERMS[k] for k in hit_keys]

def expand_query(query: str, max_terms: int = 10) -> str:
    terms = extract_terms(query)
    extras: list[str] = []
    for t in terms[:max_terms]:
        extras.extend([t.name, t.zh, *list(t.aliases[:5]), t.category])
    if not extras:
        rules = {
            '停顿':'stall bubble hazard pipeline pcWrite ifidWrite',
            '冒险':'hazard RAW forwarding stall bubble load-use',
            '缓存':'cache tag index offset valid dirty miss write back LRU',
            '寄存器':'register bitset flag mask CSR status bit',
            '指令':'RISC-V opcode funct3 funct7 rs1 rs2 rd imm decode',
            '分支':'branch pc flush stall control hazard prediction',
            '写回':'write back dirty bit victim replacement memory',
        }
        for k, v in rules.items():
            if k in query:
                extras.extend(v.split())
    return (query + '\n' + ' '.join(dict.fromkeys(extras))).strip()

def term_keywords(text: str) -> list[str]:
    kws: list[str] = []
    for t in extract_terms(text):
        kws.extend([t.name, t.zh, t.category, *t.aliases])
    return list(dict.fromkeys(str(k) for k in kws if k))

def format_term_cards(text: str, limit: int = 10) -> str:
    terms = extract_terms(text)[:limit]
    if not terms:
        return '- 未命中明显的底层系统术语。'
    return '\n'.join(f'- **{t.zh}（{t.name}）**：{t.desc}' for t in terms)

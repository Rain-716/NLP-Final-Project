from __future__ import annotations
import re, hashlib
from dataclasses import dataclass, field
from pathlib import Path
from .terminology import term_keywords

@dataclass
class CodeChunk:
    chunk_id: str
    text: str
    source: str
    language: str = 'cpp'
    start_line: int = 1
    end_line: int = 1
    kind: str = 'code'
    title: str = ''
    symbols: dict = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)

CPP_FUNC_HEADER_RE = re.compile(r'(?P<prefix>(?:template\s*<[^>]+>\s*)?(?:[\w:<>,~*&\s]+?)\s+)(?P<name>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:const\s*)?(?:noexcept\s*)?\{', re.M)
CLASS_RE = re.compile(r'\b(class|struct)\s+([A-Za-z_]\w*)')
VAR_RE = re.compile(r'\b(?:int|long|float|double|bool|char|size_t|uint32_t|uint64_t|uint16_t|uint8_t|auto|std::\w+(?:<[^>]+>)?|vector<[^>]+>|string)\s+([A-Za-z_]\w*)')
TOKEN_RE = re.compile(r'[A-Za-z_][A-Za-z_0-9]*|0x[0-9A-Fa-f]+|\d+|[\u4e00-\u9fff]{1,4}')

def clean_text(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+$', '', text, flags=re.M)
    return text.strip('\n')

def detect_language(path_or_text: str) -> str:
    suffix = Path(str(path_or_text)).suffix.lower()
    if suffix in ['.cpp', '.cc', '.hpp', '.h', '.cxx', '.c']: return 'cpp'
    if suffix == '.py': return 'python'
    if suffix in ['.md', '.txt']: return 'markdown'
    return 'cpp'

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text.replace('::', ' ')) if t.strip()]

def extract_symbols(code: str) -> dict:
    funcs = sorted(set(m.group('name') for m in CPP_FUNC_HEADER_RE.finditer(code)))
    classes = sorted(set(m.group(2) for m in CLASS_RE.finditer(code)))
    variables = sorted(set(m.group(1) for m in VAR_RE.finditer(code)))
    return {'functions': funcs, 'classes': classes, 'variables': variables}

def _line_no(text: str, idx: int) -> int:
    return text.count('\n', 0, idx) + 1

def _find_matching_brace(text: str, open_idx: int) -> int:
    depth = 0; i = open_idx; in_str = False; quote = ''; escape = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == quote: in_str = False
        else:
            if ch in ('"', "'"): in_str = True; quote = ch
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0: return i + 1
        i += 1
    return len(text)

def _code_spans(text: str) -> list[tuple[int, int, str, str]]:
    spans, used = [], []
    for m in CPP_FUNC_HEADER_RE.finditer(text):
        open_idx = text.find('{', m.start(), m.end())
        if open_idx < 0: continue
        end = _find_matching_brace(text, open_idx)
        if any(m.start() >= s and m.start() < e for s, e in used): continue
        used.append((m.start(), end)); spans.append((m.start(), end, 'function', m.group('name')))
    if not spans:
        for m in CLASS_RE.finditer(text):
            open_idx = text.find('{', m.end())
            if open_idx >= 0:
                end = _find_matching_brace(text, open_idx)
                spans.append((m.start(), min(len(text), end + 1), 'class', m.group(2)))
    spans.sort(key=lambda x: x[0])
    return spans

def _make_chunk(source: str, text: str, idx: int, sl: int, el: int, kind: str, title: str = '') -> CodeChunk:
    symbols = extract_symbols(text)
    keywords = list(dict.fromkeys(tokenize(text)[:80] + term_keywords(text)))
    digest = hashlib.md5(f'{source}:{idx}:{sl}:{el}:{title}'.encode('utf-8')).hexdigest()[:8]
    return CodeChunk(f'{Path(source).stem}_{idx}_{digest}', text.strip(), source, detect_language(source), sl, el, kind, title, symbols, keywords)

def split_markdown_to_chunks(text: str, source: str, max_chars: int = 1000, overlap: int = 180) -> list[CodeChunk]:
    text = clean_text(text)
    if not text: return []
    parts, current_title, buf, start_idx, cursor = [], Path(source).stem, [], 0, 0
    for line in text.splitlines(True):
        if line.lstrip().startswith('#') and buf:
            block = ''.join(buf).strip(); end_idx = cursor
            if block: parts.append((block, start_idx, end_idx, 'doc', current_title))
            buf = []; start_idx = cursor
        if line.lstrip().startswith('#'): current_title = line.strip('# \n') or current_title
        buf.append(line); cursor += len(line)
    if buf:
        block = ''.join(buf).strip(); parts.append((block, start_idx, len(text), 'doc', current_title))
    chunks, idx = [], 0
    for block, s, e, kind, title in parts:
        start = 0
        while start < len(block):
            end = min(len(block), start + max_chars)
            chunks.append(_make_chunk(source, block[start:end], idx, _line_no(text, s+start), _line_no(text, s+end), kind, title)); idx += 1
            if end == len(block): break
            start = max(0, end - overlap)
    return chunks

def split_code_to_chunks(text: str, source: str = 'input', max_chars: int = 1000, overlap: int = 180) -> list[CodeChunk]:
    text = clean_text(text)
    if not text: return []
    if detect_language(source) == 'markdown': return split_markdown_to_chunks(text, source, max_chars, overlap)
    spans = _code_spans(text); candidates = []
    if spans:
        for s, e, kind, title in spans:
            block = text[s:e].strip()
            if block: candidates.append((block, _line_no(text, s), _line_no(text, e), kind, title))
        prefix_end = spans[0][0]
        if prefix_end > 20:
            prefix = text[:prefix_end].strip()
            if prefix: candidates.insert(0, (prefix, 1, _line_no(text, prefix_end), 'context', 'file_context'))
    else:
        paragraphs = re.split(r'\n\s*\n', text); cursor = 0
        for p in paragraphs:
            s = text.find(p, cursor); e = s + len(p); cursor = e
            if p.strip(): candidates.append((p.strip(), _line_no(text, s), _line_no(text, e), 'block', 'code_block'))
    chunks, idx = [], 0
    for block, sl, el, kind, title in candidates:
        start = 0
        while start < len(block):
            end = min(len(block), start + max_chars)
            chunks.append(_make_chunk(source, block[start:end], idx, sl, el, kind, title)); idx += 1
            if end == len(block): break
            start = max(0, end - overlap)
    return chunks or [_make_chunk(source, text[:max_chars], 0, 1, text.count('\n')+1, 'block', 'fallback')]

def load_documents(data_dir: str | Path, max_chars: int = 1000, overlap: int = 180) -> list[CodeChunk]:
    data_dir = Path(data_dir); chunks: list[CodeChunk] = []
    for path in sorted(data_dir.rglob('*')):
        if path.suffix.lower() not in ['.cpp','.cc','.hpp','.h','.c','.md','.txt']: continue
        try: text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError: text = path.read_text(encoding='gbk', errors='ignore')
        chunks.extend(split_code_to_chunks(text, str(path), max_chars=max_chars, overlap=overlap))
    return chunks

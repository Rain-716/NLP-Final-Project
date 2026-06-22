from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import yaml
from .preprocessing import CodeChunk, split_code_to_chunks, split_markdown_to_chunks


@dataclass
class IngestionReport:
    files_seen: int = 0
    files_indexed: int = 0
    chunks_created: int = 0
    duplicates_removed: int = 0
    failures: list[str] = field(default_factory=list)
    sources: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def load_source_manifest(path: str | Path) -> dict[str, dict]:
    path = Path(path)
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = data.get("sources", data if isinstance(data, list) else [])
    result = {}
    for row in rows:
        if isinstance(row, dict) and row.get("path"):
            result[Path(row["path"]).as_posix()] = row
    return result


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("读取 PDF 需要安装 pypdf") from exc
    return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)


def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _read_pdf(path)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="gbk", errors="ignore")


def ingest_documents(data_dir: str | Path, manifest_path: str | Path, max_chars: int,
                     overlap: int) -> tuple[list[CodeChunk], IngestionReport]:
    data_dir = Path(data_dir)
    manifest = load_source_manifest(manifest_path)
    report = IngestionReport()
    chunks: list[CodeChunk] = []
    seen_text: set[str] = set()
    allowed = {".cpp", ".cc", ".hpp", ".h", ".c", ".cxx", ".md", ".txt", ".pdf"}
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        report.files_seen += 1
        rel = path.relative_to(data_dir).as_posix()
        meta = manifest.get(rel, {})
        if meta.get("enabled") is False:
            continue
        try:
            text = _read_text(path).strip()
            if len(text) < 40:
                raise ValueError("内容过短")
            if path.suffix.lower() in {".md", ".txt", ".pdf"}:
                file_chunks = split_markdown_to_chunks(text, str(path), max_chars, overlap)
            else:
                file_chunks = split_code_to_chunks(text, str(path), max_chars, overlap)
            accepted = []
            for chunk in file_chunks:
                normalized = " ".join(chunk.text.split()).lower()
                digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                if digest in seen_text or len(normalized) < 40:
                    report.duplicates_removed += 1
                    continue
                seen_text.add(digest)
                chunk.symbols["source_meta"] = {
                    "source_id": meta.get("id", rel), "document_title": meta.get("title", path.stem),
                    "version": meta.get("version", "local"), "url": meta.get("url", ""),
                    "license": meta.get("license", "unspecified"), "updated_at": meta.get("updated_at", ""),
                    "content_hash": digest,
                }
                accepted.append(chunk)
            chunks.extend(accepted)
            report.files_indexed += 1
            report.sources[meta.get("id", rel)] = len(accepted)
        except Exception as exc:
            report.failures.append(f"{rel}: {exc}")
    report.chunks_created = len(chunks)
    return chunks, report


def index_version(chunks: list[CodeChunk]) -> str:
    joined = "|".join(sorted(c.symbols.get("source_meta", {}).get("content_hash", "") for c in chunks))
    stamp = hashlib.sha256(joined.encode()).hexdigest()[:12]
    return f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{stamp}"

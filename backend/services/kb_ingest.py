import json
from pathlib import Path

from pypdf import PdfReader

from services.embedding import embed_text


def _extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    return "\n".join(pages).strip()


def extract_text(path: Path, mime_type: str | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf" or (mime_type and "pdf" in mime_type.lower()):
        return _extract_text_from_pdf(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[dict]:
    cleaned = (text or "").replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    chunks: list[dict] = []
    start = 0
    idx = 0
    n = len(cleaned)
    while start < n:
        end = min(start + chunk_size, n)
        content = cleaned[start:end].strip()
        if content:
            chunks.append(
                {
                    "chunk_index": idx,
                    "content": content,
                    "token_count": max(1, len(content) // 4),
                    "metadata_json": json.dumps({"start": start, "end": end}, ensure_ascii=False),
                }
            )
            idx += 1
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


def enrich_chunks_with_embeddings(chunks: list[dict]) -> list[dict]:
    out = []
    for c in chunks:
        emb, emb_pg = embed_text(c["content"])
        c2 = dict(c)
        c2["embedding"] = emb
        c2["embedding_vector"] = emb_pg
        out.append(c2)
    return out

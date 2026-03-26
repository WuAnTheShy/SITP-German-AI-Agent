import json
from pathlib import Path

from pypdf import PdfReader

from services.embedding import embed_texts

# 与管理员界面展示一致：抽不到文本时的说明
KB_EMPTY_TEXT_HINT = (
    "未能从该文件提取到可索引文本。"
    "若为扫描件/图片型 PDF，请先 OCR 或导出为可复制文字的 PDF 后再上传；"
    "也可尝试将内容另存为 .txt / .md。"
)


def _extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for p in reader.pages:
        pages.append(p.extract_text() or "")
    text = "\n".join(pages).strip()
    if text:
        return text
    # 部分 PDF 用 pypdf 抽不到字，PyMuPDF 有时能抽到（仍非 OCR，纯图片页仍为空）
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        try:
            parts = [(page.get_text() or "") for page in doc]
        finally:
            doc.close()
        return "\n".join(parts).strip()
    except Exception:
        return ""


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
    texts = [c["content"] for c in chunks]
    embeddings, pg_literals = embed_texts(texts)
    out = []
    for i, c in enumerate(chunks):
        c2 = dict(c)
        c2["embedding"] = embeddings[i]
        c2["embedding_vector"] = pg_literals[i]
        out.append(c2)
    return out

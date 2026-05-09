"""
kb_ingest.py - 文档提取+切块+入库
"""
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

# 1.文本提取
#   先用 pypdf 提取 -> 失败再用 PyMuPDF 兜底
#   得到一长串纯文本
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


# 新增函数，用以识别pdf的索引页/页码列表
def _looks_like_index_page(content: str) -> tuple[bool, dict]:
    """检测一段文本是否像 PDF 的索引页/页码列表。
    
    判定特征（基于词典类 PDF 的真实数据）：
      1. 短行密集（>= 70% 的行长度 < 40 字符）
      2. 行尾大量是数字（>= 50% 的行以数字结尾）
      3. 至少有 8 行可解析内容
    
    返回 (是否是索引页, 调试信息字典)
    """
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    
    debug = {
        "total_lines": len(lines),
        "short_ratio": 0.0,
        "ends_with_num_ratio": 0.0,
    }
    
    # 行数太少不判定（避免误伤词条小段）
    if len(lines) < 8:
        return False, debug
    
    short_lines = sum(1 for l in lines if len(l) < 40)
    debug["short_ratio"] = short_lines / len(lines)
    
    # 行尾是数字：取每行最后一个 token
    ends_with_num = 0
    for l in lines:
        tokens = l.split()
        if tokens and tokens[-1].rstrip(",.;:").isdigit():
            ends_with_num += 1
    debug["ends_with_num_ratio"] = ends_with_num / len(lines)
    
    is_index = (
        debug["short_ratio"] > 0.7
        and debug["ends_with_num_ratio"] > 0.5
    )
    return is_index, debug



# 2.切块
#   按 700字符 固定长度切，相邻 chunk 重叠 100 字符
def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[dict]:
    """将文本切成 chunks。
    
    在原始字符切分基础上，主动识别并丢弃索引页/页码列表噪音。
    """
    cleaned = (text or "").replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    chunks: list[dict] = []
    start = 0
    idx = 0
    n = len(cleaned)
    skipped_count = 0
    
    while start < n:
        end = min(start + chunk_size, n)
        content = cleaned[start:end].strip()
        if content:
            # 检测是否是索引页噪音
            is_index, debug = _looks_like_index_page(content)
            if is_index:
                skipped_count += 1
                preview = content[:60].replace("\n", " ")
                print(
                    f"[INGEST] skip index page chunk: "
                    f"lines={debug['total_lines']}, "
                    f"short_ratio={debug['short_ratio']:.2f}, "
                    f"num_ratio={debug['ends_with_num_ratio']:.2f} | {preview}",
                    flush=True,
                )
            else:
                chunks.append(
                    {
                        "chunk_index": idx,
                        "content": content,
                        "token_count": max(1, len(content) // 4),
                        "metadata_json": json.dumps(
                            {"start": start, "end": end}, ensure_ascii=False
                        ),
                    }
                )
                idx += 1
        if end >= n:
            break
        start = max(0, end - overlap)
    
    if skipped_count:
        print(
            f"[INGEST] chunked {idx} content chunks, skipped {skipped_count} index pages",
            flush=True,
        )
    return chunks


# 3.向量化
#   把每个 chunk 调一次阿里云 text-embedding-v3 API
#   每个 chunk -> 一个 1024 维向量(1024个浮点数)
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

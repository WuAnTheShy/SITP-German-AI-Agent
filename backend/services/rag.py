import os

from sqlalchemy.orm import Session

from crud.repositories import KnowledgeBaseCRUD
from services.embedding import embed_text
from services.rerank import rerank


RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"

# 召回阶段（embedding）：宽松，多召回让 rerank 有空间精排
RAG_RECALL_TOP_K = int(os.getenv("RAG_RECALL_TOP_K", "20"))
RAG_RECALL_THRESHOLD = float(os.getenv("RAG_RECALL_THRESHOLD", "0.2"))

# 精排阶段（rerank）：严格,只保留真正相关的
RAG_RERANK_TOP_N = int(os.getenv("RAG_RERANK_TOP_N", "3"))
RAG_RERANK_THRESHOLD = float(os.getenv("RAG_RERANK_THRESHOLD", "0.3"))

# 用于"是否对用户显示参考资料"的最终守门阈值（基于 rerank 分数）
RAG_STRONG_HIT_THRESHOLD = float(os.getenv("RAG_STRONG_HIT_THRESHOLD", "0.4"))


def search_knowledge(
    db: Session,
    query: str,
    viewer_user_id: int | None = None,
    viewer_session_key: str | None = None,
) -> list[dict]:
    """两阶段检索：embedding 粗排召回 + rerank 精排过滤。

    返回的每条 chunk dict 中：
      - "score" 字段被替换为 rerank 后的相关性分数（如果 rerank 成功）
      - 如果 rerank 失败，回退到 embedding 分数（保持系统可用性）
    """
    print(
        f"[RAG-DEBUG] search_knowledge called: query={query!r}, "
        f"viewer_user_id={viewer_user_id}, viewer_session_key={viewer_session_key}",
        flush=True,
    )
    if not RAG_ENABLED:
        print("[RAG-DEBUG] RAG_ENABLED=False, skip", flush=True)
        return []
    q = (query or "").strip()
    if not q:
        return []

    # ─── 阶段 1：召回 (embedding) ───
    try:
        _, q_vec = embed_text(q)
        print(f"[RAG-DEBUG] embed_text OK, vec len={len(q_vec) if q_vec else 0}", flush=True)
    except Exception as e:
        print(f"[RAG-DEBUG] embed_text FAILED: {type(e).__name__}: {e}", flush=True)
        return []

    candidates = KnowledgeBaseCRUD.search_chunks_by_embedding(
        db,
        q_vec,
        top_k=RAG_RECALL_TOP_K,
        score_threshold=RAG_RECALL_THRESHOLD,
        viewer_user_id=viewer_user_id,
        viewer_session_key=viewer_session_key,
    )
    print(f"[RAG-DEBUG] recall returned {len(candidates)} candidates", flush=True)
    # 临时调试：打印召回阶段前 5 个 chunk 的预览
    for i, c in enumerate(candidates[:5]):
        preview = (c.get("content") or "")[:80].replace("\n", " ")
        print(f"[RAG-DEBUG]   recall #{i+1} score={c.get('score', 0):.3f} | {preview}", flush=True)
    if not candidates:
        return []

    # ─── 阶段 2：精排 (rerank) ───
    documents = [c.get("content", "") for c in candidates]
    rerank_results = rerank(q, documents, top_n=RAG_RERANK_TOP_N)

    if rerank_results is None:
        # Rerank 失败 - 回退到 embedding 召回的 Top-N（保持系统可用）
        print("[RAG-DEBUG] rerank unavailable, fallback to embedding top-N", flush=True)
        return candidates[:RAG_RERANK_TOP_N]

    # 用 rerank 分数过滤 + 重排
    final = []
    for r in rerank_results:
        idx = r["index"]
        score = r["score"]
        if score < RAG_RERANK_THRESHOLD:
            continue  # 低于精排阈值的丢弃
        if idx < 0 or idx >= len(candidates):
            continue
        chunk = dict(candidates[idx])  # 浅拷贝，避免污染原 list
        chunk["score"] = score          # 用 rerank 分数覆盖原 embedding 分数
        chunk["_recall_score"] = candidates[idx].get("score", 0.0)  # 保留原召回分数用于调试
        final.append(chunk)

    print(
        f"[RAG-DEBUG] rerank returned {len(rerank_results)} results, "
        f"after threshold {RAG_RERANK_THRESHOLD} kept {len(final)}",
        flush=True,
    )
    for i, c in enumerate(final[:3]):
        title = c.get("title", "")
        preview = (c.get("content") or "")[:60]
        print(
            f"[RAG-DEBUG]   #{i+1} rerank={c['score']:.3f} recall={c.get('_recall_score', 0):.3f} title={title} | {preview}",
            flush=True,
        )
    return final


def build_rag_context(
    db: Session,
    query: str,
    viewer_user_id: int | None = None,
    viewer_session_key: str | None = None,
) -> tuple[str, list[str], float]:
    """构建 RAG 上下文。

    返回三元组：(context, sources_to_show, top_score)
    其中 top_score 是经过 rerank 的相关性分数（如果可用），
    优于 embedding 余弦相似度，更适合做"是否显示参考资料"的判断。
    """
    rows = search_knowledge(
        db,
        query,
        viewer_user_id=viewer_user_id,
        viewer_session_key=viewer_session_key,
    )
    if not rows:
        return "", [], 0.0

    top_score = float(rows[0].get("score", 0.0))

    parts = []
    sources_all = []
    for i, r in enumerate(rows, start=1):
        scope = "私有" if r.get("owner_user_id") else "公共"
        src = f"[{scope}] {r.get('title','未命名文档')}#chunk{r.get('chunk_index', 0)}"
        sources_all.append(src)
        parts.append(f"[{i}] 来源: {src}\n内容: {r.get('content','')}")
    context = (
        "以下是知识库检索到的参考内容，请优先基于这些内容回答；若不足请明确说明"
        "知识库未命中，以下为通用回答。\n\n"
        + "\n\n".join(parts)
    )

    sources_to_show = sources_all if top_score >= RAG_STRONG_HIT_THRESHOLD else []

    print(
        f"[RAG-CONTEXT] {len(rows)} chunks, top_score={top_score:.3f}, "
        f"strong_hit={top_score >= RAG_STRONG_HIT_THRESHOLD}, "
        f"sources_shown={len(sources_to_show)}, total {len(context)} chars",
        flush=True,
    )
    return context, sources_to_show, top_score
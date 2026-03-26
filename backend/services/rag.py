import os

from sqlalchemy.orm import Session

from crud.repositories import KnowledgeBaseCRUD
from services.embedding import embed_text


RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.25"))


def search_knowledge(
    db: Session,
    query: str,
    viewer_user_id: int | None = None,
    viewer_session_key: str | None = None,
) -> list[dict]:
    if not RAG_ENABLED:
        return []
    q = (query or "").strip()
    if not q:
        return []
    _, q_vec = embed_text(q)
    return KnowledgeBaseCRUD.search_chunks_by_embedding(
        db,
        q_vec,
        top_k=RAG_TOP_K,
        score_threshold=RAG_SCORE_THRESHOLD,
        viewer_user_id=viewer_user_id,
        viewer_session_key=viewer_session_key,
    )


def build_rag_context(
    db: Session,
    query: str,
    viewer_user_id: int | None = None,
    viewer_session_key: str | None = None,
) -> tuple[str, list[str]]:
    rows = search_knowledge(
        db,
        query,
        viewer_user_id=viewer_user_id,
        viewer_session_key=viewer_session_key,
    )
    if not rows:
        return "", []
    sources = []
    parts = []
    for i, r in enumerate(rows, start=1):
        scope = "私有" if r.get("owner_user_id") else "公共"
        src = f"[{scope}] {r.get('title','未命名文档')}#chunk{r.get('chunk_index', 0)}"
        sources.append(src)
        parts.append(f"[{i}] 来源: {src}\n内容: {r.get('content','')}")
    context = (
        "以下是知识库检索到的参考内容，请优先基于这些内容回答；若不足请明确说明“知识库未命中，以下为通用回答”。\n\n"
        + "\n\n".join(parts)
    )
    return context, sources

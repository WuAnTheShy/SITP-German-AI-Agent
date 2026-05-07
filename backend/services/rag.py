import os
import logging
from typing import Any

from sqlalchemy.orm import Session

from crud.repositories import KnowledgeBaseCRUD
from services.embedding import embed_text
from services.rerank import rerank


logger = logging.getLogger(__name__)


RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"

# 召回阶段:embedding + 关键词,各取 top_k
RAG_RECALL_TOP_K = int(os.getenv("RAG_RECALL_TOP_K", "20"))
RAG_RECALL_THRESHOLD = float(os.getenv("RAG_RECALL_THRESHOLD", "0.2"))

# 关键词检索:阈值更宽松,因为 ts_rank_cd 分数范围小
RAG_KEYWORD_TOP_K = int(os.getenv("RAG_KEYWORD_TOP_K", "20"))
RAG_KEYWORD_THRESHOLD = float(os.getenv("RAG_KEYWORD_THRESHOLD", "0.01"))

# RRF 融合参数(标准值 60)
RRF_K = int(os.getenv("RAG_RRF_K", "60"))

# 精排阶段:严格,只保留真正相关的
RAG_RERANK_TOP_N = int(os.getenv("RAG_RERANK_TOP_N", "3"))
RAG_RERANK_THRESHOLD = float(os.getenv("RAG_RERANK_THRESHOLD", "0.3"))

# 用于"是否对用户显示参考资料"的最终守门阈值
RAG_STRONG_HIT_THRESHOLD = float(os.getenv("RAG_STRONG_HIT_THRESHOLD", "0.4"))

# 是否启用混合检索(可关闭做对比测试)
HYBRID_SEARCH_ENABLED = os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true"


def _reciprocal_rank_fusion(
    rankings: list[list[dict]],
    k: int = RRF_K,
) -> list[dict]:
    """RRF (Reciprocal Rank Fusion) 融合多路检索结果。
    
    论文: Cormack et al. "Reciprocal rank fusion outperforms condorcet 
    and individual rank learning methods" (2009).
    
    公式: rrf_score(d) = Σ 1/(k + rank_i(d))
    
    优点:
    - 不依赖各路 score 的具体数值(BM25 与 cosine 是不同 scale)
    - 只看排名,天然鲁棒
    - 60 是经验值(论文推荐)
    
    Args:
        rankings: 多路检索结果列表,每路是 [chunk_dict, ...]
        k: RRF 平滑参数,默认 60
        
    Returns:
        融合后的去重结果列表(按 rrf_score 降序)
    """
    chunk_scores: dict[int, dict] = {}  # chunk_id → {chunk, rrf_score, sources}
    
    for source_idx, ranking in enumerate(rankings):
        for rank, chunk in enumerate(ranking):
            chunk_id = chunk["id"]
            rrf_contribution = 1.0 / (k + rank + 1)  # rank 从 0 开始,故 +1
            
            if chunk_id in chunk_scores:
                chunk_scores[chunk_id]["rrf_score"] += rrf_contribution
                chunk_scores[chunk_id]["sources"].append(source_idx)
            else:
                chunk_scores[chunk_id] = {
                    "chunk": chunk,
                    "rrf_score": rrf_contribution,
                    "sources": [source_idx],
                }
    
    # 按 rrf_score 排序
    sorted_items = sorted(
        chunk_scores.values(),
        key=lambda x: x["rrf_score"],
        reverse=True,
    )
    
    # 把 rrf_score 和 source 信息附加到每个 chunk dict
    fused = []
    for item in sorted_items:
        c = dict(item["chunk"])
        c["_rrf_score"] = item["rrf_score"]
        c["_retrieval_sources"] = item["sources"]  # 0=向量, 1=关键词
        fused.append(c)
    
    return fused


def search_knowledge(
    db: Session,
    query: str,
    viewer_user_id: int | None = None,
    viewer_session_key: str | None = None,
) -> list[dict]:
    """混合检索: embedding(语义) + keyword(BM25 风格) → RRF 融合 → rerank 精排。
    
    返回的每条 chunk dict 中:
      - "score" 字段是 rerank 后的相关性分数(rerank 失败时降级到 embedding 分数)
      - "_recall_score": 原向量召回分数(用于调试)
      - "_keyword_score": 原关键词召回分数(用于调试)
      - "_rrf_score":    RRF 融合分数
      - "_retrieval_sources": 命中来源 [0=向量, 1=关键词],可推断为何被检索到
    """
    logger.info(f"search_knowledge called: query={query!r}, hybrid={HYBRID_SEARCH_ENABLED}")
    
    if not RAG_ENABLED:
        logger.info("RAG_ENABLED=False, skip")
        return []
    
    q = (query or "").strip()
    if not q:
        return []
    
    # ─── 阶段 1a: 向量召回 ───
    try:
        _, q_vec = embed_text(q)
        logger.debug(f"embed_text OK, vec len={len(q_vec) if q_vec else 0}")
    except Exception as e:
        logger.warning(f"embed_text FAILED: {type(e).__name__}: {e}")
        q_vec = None
    
    vector_candidates: list[dict] = []
    if q_vec:
        vector_candidates = KnowledgeBaseCRUD.search_chunks_by_embedding(
            db, q_vec,
            top_k=RAG_RECALL_TOP_K,
            score_threshold=RAG_RECALL_THRESHOLD,
            viewer_user_id=viewer_user_id,
            viewer_session_key=viewer_session_key,
        )
        logger.info(f"vector recall: {len(vector_candidates)} candidates")
    
    # ─── 阶段 1b: 关键词召回(BM25 风格) ───
    keyword_candidates: list[dict] = []
    if HYBRID_SEARCH_ENABLED:
        try:
            keyword_candidates = KnowledgeBaseCRUD.search_chunks_by_keyword(
                db, q,
                top_k=RAG_KEYWORD_TOP_K,
                score_threshold=RAG_KEYWORD_THRESHOLD,
                viewer_user_id=viewer_user_id,
                viewer_session_key=viewer_session_key,
            )
            logger.info(f"keyword recall: {len(keyword_candidates)} candidates")
        except Exception as e:
            logger.warning(f"keyword search FAILED: {type(e).__name__}: {e}")
    
    # 没有任何召回结果
    if not vector_candidates and not keyword_candidates:
        logger.info("both recall paths returned empty")
        return []
    
    # ─── 阶段 1c: RRF 融合 ───
    if HYBRID_SEARCH_ENABLED and vector_candidates and keyword_candidates:
        # 把每条 chunk 的原始分数另存,以便后续调试
        for c in vector_candidates:
            c["_recall_score"] = c.get("score", 0.0)
        for c in keyword_candidates:
            c["_keyword_score"] = c.get("score", 0.0)
        
        candidates = _reciprocal_rank_fusion(
            [vector_candidates, keyword_candidates],
            k=RRF_K,
        )
        logger.info(
            f"RRF fused: {len(candidates)} unique chunks "
            f"(vector={len(vector_candidates)}, keyword={len(keyword_candidates)})"
        )
    else:
        # 退化到单路(没启用 hybrid 或只有一路有结果)
        candidates = vector_candidates or keyword_candidates
        for c in candidates:
            c["_recall_score"] = c.get("score", 0.0)
    
    if not candidates:
        return []
    
    # ─── 阶段 2: rerank 精排 ───
    documents = [c.get("content", "") for c in candidates]
    rerank_results = rerank(q, documents, top_n=RAG_RERANK_TOP_N)
    
    if rerank_results is None:
        # Rerank 失败 - 回退到融合 Top-N
        logger.warning("rerank unavailable, fallback to fused top-N")
        return candidates[:RAG_RERANK_TOP_N]
    
    final = []
    for r in rerank_results:
        idx = r["index"]
        score = r["score"]
        if score < RAG_RERANK_THRESHOLD:
            continue
        if idx < 0 or idx >= len(candidates):
            continue
        chunk = dict(candidates[idx])
        chunk["score"] = score  # 用 rerank 分数覆盖
        final.append(chunk)
    
    logger.info(
        f"rerank done: {len(rerank_results)} reranked, "
        f"after threshold {RAG_RERANK_THRESHOLD} kept {len(final)}"
    )
    for i, c in enumerate(final[:3]):
        sources_label = "+".join(["V" if s == 0 else "K" for s in c.get("_retrieval_sources", [0])])
        title = c.get("title", "")
        preview = (c.get("content") or "")[:60]
        logger.debug(
            f"  #{i+1} rerank={c['score']:.3f} "
            f"sources={sources_label} title={title} | {preview}"
        )
    return final


def build_rag_context(
    db: Session,
    query: str,
    viewer_user_id: int | None = None,
    viewer_session_key: str | None = None,
) -> tuple[str, list[str], float]:
    """构建 RAG 上下文。返回三元组:(context, sources_to_show, top_score)。"""
    rows = search_knowledge(
        db, query,
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
        "以下是知识库检索到的参考内容,请优先基于这些内容回答;若不足请明确说明"
        "知识库未命中,以下为通用回答。\n\n"
        + "\n\n".join(parts)
    )
    
    sources_to_show = sources_all if top_score >= RAG_STRONG_HIT_THRESHOLD else []
    
    logger.info(
        f"RAG context: {len(rows)} chunks, top_score={top_score:.3f}, "
        f"strong_hit={top_score >= RAG_STRONG_HIT_THRESHOLD}, "
        f"sources_shown={len(sources_to_show)}"
    )
    return context, sources_to_show, top_score
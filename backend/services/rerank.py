"""DashScope gte-rerank 集成。

提供两阶段检索的精排（Rerank）能力：在 embedding 召回 Top-K 之后，
用一个专门训练的相关性模型对候选 chunk 重新打分，过滤掉"主题相关
但答不了问题"的伪相关结果。
"""

import os
from typing import Optional

import requests


RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "true").lower() == "true"
RERANK_MODEL = os.getenv("RAG_RERANK_MODEL", "gte-rerank") #阿里云专门的rerank模型
RERANK_API_URL = os.getenv(
    "RAG_RERANK_API_URL",
    "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
)
RERANK_TIMEOUT = float(os.getenv("RAG_RERANK_TIMEOUT", "30"))
RERANK_API_KEY = os.getenv("QWEN_API_KEY", "")


def rerank(
    query: str,
    documents: list[str],
    top_n: int = 5,
) -> Optional[list[dict]]:
    """对候选文档做相关性重排。

    Args:
        query: 用户查询
        documents: 候选文档文本列表（embedding 召回的 chunk 内容）
        top_n: 返回前 N 个

    Returns:
        成功时返回 list[dict]，每项包含 {"index": 原始序号, "score": 相关性分数}
        失败时返回 None（让上层走 fallback 逻辑，不要让整个对话挂掉）
    """
    if not RERANK_ENABLED:
        return None
    if not query or not documents:
        return None
    if not RERANK_API_KEY:
        print("[RERANK] No API key, skip rerank", flush=True)
        return None

    payload = {
        "model": RERANK_MODEL,
        "input": {
            "query": query,
            "documents": documents,
        },
        "parameters": {
            "return_documents": False,  # 不需要回传文档，省带宽
            "top_n": min(top_n, len(documents)),
        },
    }
    headers = {
        "Authorization": f"Bearer {RERANK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            RERANK_API_URL, json=payload, headers=headers, timeout=RERANK_TIMEOUT
        )
        if resp.status_code != 200:
            print(
                f"[RERANK] API returned {resp.status_code}: {resp.text[:200]}",
                flush=True,
            )
            return None
        data = resp.json()
        results = data.get("output", {}).get("results", [])
        if not results:
            print("[RERANK] empty results from API", flush=True)
            return None
        # 标准化输出：[{"index": 0, "score": 0.85}, ...]
        normalized = [
            {"index": int(r["index"]), "score": float(r["relevance_score"])}
            for r in results
        ]
        usage = data.get("usage", {})
        print(
            f"[RERANK] reranked {len(documents)} -> top {len(normalized)}, "
            f"top_score={normalized[0]['score']:.3f}, "
            f"tokens={usage.get('total_tokens', '?')}",
            flush=True,
        )
        return normalized
    except requests.RequestException as e:
        print(f"[RERANK] request failed: {type(e).__name__}: {e}", flush=True)
        return None
    except (KeyError, ValueError) as e:
        print(f"[RERANK] parse failed: {type(e).__name__}: {e}", flush=True)
        return None
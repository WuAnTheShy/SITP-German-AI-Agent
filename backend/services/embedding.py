import os
from typing import Any

import requests


EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "dashscope")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
EMBEDDING_API_URL = os.getenv(
    "EMBEDDING_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
)


def _vector_to_pg_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def embed_text(text: str) -> tuple[list[float], str]:
    """
    返回 (embedding_list, pgvector_literal)
    pgvector_literal 形如: [0.1,0.2,...]
    """
    if not QWEN_API_KEY:
        raise RuntimeError("QWEN_API_KEY 未配置，无法生成 embedding")
    if EMBEDDING_PROVIDER != "dashscope":
        raise RuntimeError(f"不支持的 EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")

    payload: dict[str, Any] = {"model": EMBEDDING_MODEL, "input": text}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QWEN_API_KEY.strip()}",
    }
    resp = requests.post(EMBEDDING_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    emb = (
        data.get("data", [{}])[0].get("embedding")
        or data.get("output", {}).get("embeddings", [{}])[0].get("embedding")
    )
    if not emb or not isinstance(emb, list):
        raise RuntimeError(f"Embedding 返回格式异常: {str(data)[:300]}")
    return emb, _vector_to_pg_literal(emb)

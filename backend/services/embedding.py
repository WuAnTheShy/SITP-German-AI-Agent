"""
embedding.py - 调嵌入API把文本变为向量
"""
import os
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "dashscope")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
EMBEDDING_API_URL = os.getenv(
    "EMBEDDING_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
)
EMBEDDING_TIMEOUT = float(os.getenv("EMBEDDING_TIMEOUT", "120"))
EMBEDDING_BATCH_SIZE = max(1, int(os.getenv("EMBEDDING_BATCH_SIZE", "16")))


def _session() -> requests.Session:
    retry = Retry(
        total=4,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("POST",),
    )
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


_SESSION: requests.Session | None = None


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = _session()
    return _SESSION


def _vector_to_pg_literal(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def _parse_embedding_response(data: dict[str, Any], expected: int) -> list[list[float]]:
    items = data.get("data")
    if isinstance(items, list) and items:
        items = sorted(items, key=lambda x: x.get("index", 0))
        vecs: list[list[float]] = []
        for it in items[:expected]:
            emb = it.get("embedding")
            if isinstance(emb, list):
                vecs.append(emb)
        if len(vecs) == expected:
            return vecs
    out = data.get("output") or {}
    emb_list = out.get("embeddings")
    if isinstance(emb_list, list) and emb_list:
        vecs = []
        for it in emb_list[:expected]:
            if isinstance(it, dict) and isinstance(it.get("embedding"), list):
                vecs.append(it["embedding"])
            elif isinstance(it, list):
                vecs.append(it)
        if len(vecs) == expected:
            return vecs
    if expected == 1:
        emb = (
            (data.get("data") or [{}])[0].get("embedding")
            if isinstance(data.get("data"), list)
            else None
        ) or (out.get("embeddings") or [{}])[0].get("embedding")
        if isinstance(emb, list):
            return [emb]
    raise RuntimeError(f"Embedding 返回格式异常: {str(data)[:500]}")


def _post_embeddings(payload: dict[str, Any]) -> dict[str, Any]:
    if not QWEN_API_KEY.strip():
        raise RuntimeError("QWEN_API_KEY 未配置，无法生成 embedding")
    if EMBEDDING_PROVIDER != "dashscope":
        raise RuntimeError(f"不支持的 EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QWEN_API_KEY.strip()}",
    }
    try:
        resp = _get_session().post(
            EMBEDDING_API_URL,
            json=payload,
            headers=headers,
            timeout=(20, EMBEDDING_TIMEOUT),
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        body = ""
        if e.response is not None:
            try:
                body = e.response.text[:400]
            except Exception:
                pass
        raise RuntimeError(
            f"embedding HTTP 错误 {e.response.status_code if e.response else '?'}: {body or e!s}"
        ) from e
    except requests.exceptions.RequestException as e:
        hint = (
            "请确认本机/服务器能访问 dashscope.aliyuncs.com（公司网络或防火墙可能拦截 HTTPS），"
            "核对 QWEN_API_KEY 是否有效；可稍后点击「重建索引」重试。"
        )
        raise RuntimeError(f"embedding 网络请求失败: {e!s}。{hint}") from e


def _embed_one_batch(batch: list[str]) -> list[list[float]]:
    payload: dict[str, Any] = {"model": EMBEDDING_MODEL, "input": batch}
    data = _post_embeddings(payload)
    return _parse_embedding_response(data, len(batch))


def embed_texts(texts: list[str]) -> tuple[list[list[float]], list[str]]:
    """
    批量调用 embedding API，减少 HTTP 往返，降低 Connection aborted 概率。
    返回 (embedding_list, pgvector_literal 列表)
    """
    if not texts:
        return [], []
    all_emb: list[list[float]] = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        try:
            all_emb.extend(_embed_one_batch(batch))
        except RuntimeError:
            if len(batch) <= 1:
                raise
            for t in batch:
                all_emb.extend(_embed_one_batch([t]))
    literals = [_vector_to_pg_literal(e) for e in all_emb]
    return all_emb, literals


def embed_text(text: str) -> tuple[list[float], str]:
    """
    返回 (embedding_list, pgvector_literal)
    """
    embs, literals = embed_texts([text])
    return embs[0], literals[0]

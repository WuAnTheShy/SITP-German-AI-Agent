"""
检测本机能否访问 DashScope 兼容模式的 Embedding API（与知识库/RAG 使用同一套配置）。
用法（在项目根目录）:
  python backend/scripts/check_qwen_embedding.py
或在 backend 目录:
  python scripts/check_qwen_embedding.py
"""
from __future__ import annotations

import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
repo_root = backend_root.parent
sys.path.insert(0, str(backend_root))

from dotenv import load_dotenv

load_dotenv(repo_root / ".env")
load_dotenv(backend_root / ".env")

import os

import requests


def main() -> None:
    url = os.getenv(
        "EMBEDDING_API_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
    )
    key = (os.getenv("QWEN_API_KEY") or "").strip()
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

    print("=== Qwen / DashScope Embedding 连通性检测 ===\n")
    print(f"EMBEDDING_API_URL = {url}")
    print(f"EMBEDDING_MODEL   = {model}")
    print(f"QWEN_API_KEY      = {'已设置 (' + str(len(key)) + ' 字符)' if key else '【未设置】'}\n")

    # 1) 仅 TLS + DNS：访问同域名根路径（可能返回 403/404，但能区分「连不上」与「能连上」）
    try:
        r = requests.get("https://dashscope.aliyuncs.com/", timeout=15)
        print(f"[1] HTTPS 访问 dashscope 根路径: HTTP {r.status_code}（能建立 TLS 即说明 DNS/代理基本可用）")
    except requests.exceptions.RequestException as e:
        print(f"[1] HTTPS 访问 dashscope 根路径失败: {e!s}")
        print("    → 优先排查：代理/VPN、公司防火墙、DNS。\n")

    if not key:
        print("[2] 跳过 Embedding 调用：请先在 .env 中配置 QWEN_API_KEY。")
        sys.exit(2)

    # 2) 真实调用与知识库相同的 embedding 接口
    try:
        from services.embedding import embed_text

        vec, pg = embed_text("Hallo")
        dim = len(vec)
        print(f"[2] Embedding API 调用成功: 向量维度={dim}, pg 字面量前缀={pg[:48]}...")
        print("\n结论：当前环境可以正常调用 Qwen Embedding，知识库失败请查 PDF 解析、库表或其它后端日志。")
        sys.exit(0)
    except Exception as e:
        print(f"[2] Embedding API 调用失败: {e!s}")
        print("\n结论：网络或密钥/额度导致无法调用 DashScope。请核对阿里云百炼 API Key、账户额度与出口网络。")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""SSE (Server-Sent Events) 工具函数。

把 Python dict 转为符合 SSE 规范的字节流。
"""
import json
import logging


logger = logging.getLogger(__name__)


def sse_format(event: str, data: dict | str) -> bytes:
    """把单个事件 + 数据格式化为 SSE 字节流。
    
    SSE 规范:每条消息以两个换行结尾。
    """
    if isinstance(data, dict):
        data_str = json.dumps(data, ensure_ascii=False)
    else:
        data_str = str(data)
    
    # 处理多行 data:每行前缀 "data: "
    data_lines = data_str.split("\n")
    data_block = "\n".join(f"data: {line}" for line in data_lines)
    
    msg = f"event: {event}\n{data_block}\n\n"
    return msg.encode("utf-8")


def sse_keep_alive() -> bytes:
    """SSE 心跳消息(保持长连接不被代理 kill)。
    
    用 SSE 注释行(以 ':' 开头)实现,客户端会忽略但保持连接。
    """
    return b": keep-alive\n\n"
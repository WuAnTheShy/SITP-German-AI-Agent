"""Agent 可观测性模块。

提供 ExecutionTrace + Span 的轻量 trace 系统,
用于记录每次请求的完整调用链,服务于性能分析和 debug。

使用示例:
    from services.observability import ExecutionTrace
    
    trace = ExecutionTrace(
        role="student",
        user_id=1,
        session_id=27,
        user_message="我哪里弱?",
    )
    
    # 记录 span
    with trace.span("llm_call", "qwen_completion") as span:
        result = call_llm(...)
        span.set_tokens(in_tokens=120, out_tokens=380)
    
    # 完成 + 持久化
    trace.finalize(reply_text="...", success=True)
    trace.persist(db)
"""
from .trace import ExecutionTrace, Span

__all__ = ["ExecutionTrace", "Span"]
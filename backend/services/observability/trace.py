"""ExecutionTrace 核心实现。

设计原则:
- 显式传 trace 对象,不用全局变量(便于测试 + 代码清晰)
- Span 用 contextmanager,自动记录耗时
- 失败时不影响主业务(fail-safe)
"""
import time
import uuid
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

from sqlalchemy import text
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


# Qwen 计价(参考 DashScope 公开价格,大概值)
# qwen-plus: 输入 0.0008 元/1k tokens, 输出 0.002 元/1k tokens
COST_INPUT_PER_1K_YUAN = 0.0008
COST_OUTPUT_PER_1K_YUAN = 0.002


@dataclass
class Span:
    """单个子操作的 trace span。"""
    span_type: str            # 'llm_call' | 'tool_call' | 'rag_retrieval' | 'memory_inject'
    span_name: str            # 工具名 / 'qwen_completion' / 'embedding+rerank'
    sequence: int             # trace 内顺序
    
    # 时间(内部用)
    _start_time: float = field(default_factory=time.time)
    duration_ms: int = 0
    
    # 数据
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    
    # LLM 专用
    input_tokens: int = 0
    output_tokens: int = 0
    
    # RAG 专用
    rag_recall_count: int = 0
    rag_rerank_score: float = 0.0
    
    # 状态
    success: bool = True
    error_message: str | None = None
    
    def finalize(self) -> None:
        """计算 duration。"""
        self.duration_ms = int((time.time() - self._start_time) * 1000)
    
    def set_input(self, data: dict) -> None:
        """记录输入数据(自动截断长字段)。"""
        self.input_data = _truncate_dict(data, max_str_len=500)
    
    def set_output(self, data: dict) -> None:
        """记录输出数据(自动截断长字段)。"""
        self.output_data = _truncate_dict(data, max_str_len=500)
    
    def set_tokens(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """记录 LLM token 用量。"""
        self.input_tokens = int(input_tokens or 0)
        self.output_tokens = int(output_tokens or 0)
    
    def set_rag_stats(self, recall_count: int = 0, rerank_score: float = 0.0) -> None:
        """记录 RAG 检索统计。"""
        self.rag_recall_count = int(recall_count or 0)
        self.rag_rerank_score = float(rerank_score or 0.0)
    
    def mark_failed(self, error_message: str) -> None:
        """标记失败。"""
        self.success = False
        self.error_message = str(error_message)[:500]


class ExecutionTrace:
    """单次请求的完整 trace。"""
    
    def __init__(
        self,
        role: str,
        user_id: int | None,
        session_id: int | None,
        user_message: str,
    ):
        self.trace_id = f"trc_{uuid.uuid4().hex[:16]}"
        self.role = role
        self.user_id = user_id
        self.session_id = session_id
        self.user_message = user_message[:5000]  # 防超长
        
        self._start_time = time.time()
        self.total_duration_ms = 0
        
        self.spans: list[Span] = []
        self._sequence_counter = 0
        
        # 最终聚合数据
        self.reply_text: str | None = None
        self.success = True
        self.error_type: str | None = None
        self.error_message: str | None = None
        
        # Agent 行为标签
        self.rag_used = False
        self.rag_top_score = 0.0
        self.iterations_used = 0
    
    @contextmanager
    def span(self, span_type: str, span_name: str) -> Iterator[Span]:
        """用 with 块自动创建 + 完成 span。
        
        使用:
            with trace.span("tool_call", "query_my_abilities") as span:
                span.set_input({"args": args})
                result = ...
                span.set_output({"keys": list(result.keys())})
        """
        self._sequence_counter += 1
        span_obj = Span(
            span_type=span_type,
            span_name=span_name,
            sequence=self._sequence_counter,
        )
        try:
            yield span_obj
        except Exception as e:
            span_obj.mark_failed(f"{type(e).__name__}: {e}")
            raise
        finally:
            span_obj.finalize()
            self.spans.append(span_obj)
    
    def finalize(
        self,
        reply_text: str | None = None,
        success: bool = True,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """请求结束时调用,计算总耗时 + 聚合数据。"""
        self.total_duration_ms = int((time.time() - self._start_time) * 1000)
        self.reply_text = (reply_text or "")[:5000]
        self.success = success
        self.error_type = error_type
        self.error_message = (error_message or "")[:500] if error_message else None
    
    def get_aggregates(self) -> dict[str, Any]:
        """聚合各种指标。"""
        llm_spans = [s for s in self.spans if s.span_type == "llm_call"]
        tool_spans = [s for s in self.spans if s.span_type == "tool_call"]
        
        total_input_tokens = sum(s.input_tokens for s in llm_spans)
        total_output_tokens = sum(s.output_tokens for s in llm_spans)
        
        cost = (
            total_input_tokens * COST_INPUT_PER_1K_YUAN / 1000
            + total_output_tokens * COST_OUTPUT_PER_1K_YUAN / 1000
        )
        
        # 工具调用名(去重)
        tool_names = list({s.span_name for s in tool_spans})
        
        return {
            "total_llm_calls": len(llm_spans),
            "total_tool_calls": len(tool_spans),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "estimated_cost_yuan": round(cost, 4),
            "tools_called": tool_names,
        }
    
    def persist(self, db: Session) -> None:
        """持久化到数据库。失败时只 log 不抛(fail-safe)。"""
        try:
            agg = self.get_aggregates()
            
            # 写 trace 主表
            db.execute(text("""
                INSERT INTO agent_traces (
                    trace_id, role, user_id, session_id,
                    user_message, user_message_length,
                    reply_text, reply_length,
                    success, error_type, error_message,
                    total_duration_ms,
                    total_llm_calls, total_tool_calls,
                    total_input_tokens, total_output_tokens, estimated_cost_yuan,
                    rag_used, rag_top_score, iterations_used,
                    tools_called
                ) VALUES (
                    :trace_id, :role, :user_id, :session_id,
                    :user_message, :user_message_length,
                    :reply_text, :reply_length,
                    :success, :error_type, :error_message,
                    :total_duration_ms,
                    :total_llm_calls, :total_tool_calls,
                    :total_input_tokens, :total_output_tokens, :estimated_cost_yuan,
                    :rag_used, :rag_top_score, :iterations_used,
                    CAST(:tools_called AS JSONB)
                )
            """), {
                "trace_id": self.trace_id,
                "role": self.role,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "user_message": self.user_message,
                "user_message_length": len(self.user_message),
                "reply_text": self.reply_text,
                "reply_length": len(self.reply_text or ""),
                "success": self.success,
                "error_type": self.error_type,
                "error_message": self.error_message,
                "total_duration_ms": self.total_duration_ms,
                "total_llm_calls": agg["total_llm_calls"],
                "total_tool_calls": agg["total_tool_calls"],
                "total_input_tokens": agg["total_input_tokens"],
                "total_output_tokens": agg["total_output_tokens"],
                "estimated_cost_yuan": agg["estimated_cost_yuan"],
                "rag_used": self.rag_used,
                "rag_top_score": self.rag_top_score if self.rag_top_score else None,
                "iterations_used": self.iterations_used,
                "tools_called": _json_dumps(agg["tools_called"]),
            })
            
            # 写 spans
            for span in self.spans:
                db.execute(text("""
                    INSERT INTO agent_spans (
                        trace_id, span_type, span_name, sequence,
                        duration_ms,
                        input_data, output_data,
                        input_tokens, output_tokens,
                        rag_recall_count, rag_rerank_score,
                        success, error_message
                    ) VALUES (
                        :trace_id, :span_type, :span_name, :sequence,
                        :duration_ms,
                        CAST(:input_data AS JSONB), CAST(:output_data AS JSONB),
                        :input_tokens, :output_tokens,
                        :rag_recall_count, :rag_rerank_score,
                        :success, :error_message
                    )
                """), {
                    "trace_id": self.trace_id,
                    "span_type": span.span_type,
                    "span_name": span.span_name,
                    "sequence": span.sequence,
                    "duration_ms": span.duration_ms,
                    "input_data": _json_dumps(span.input_data) if span.input_data else None,
                    "output_data": _json_dumps(span.output_data) if span.output_data else None,
                    "input_tokens": span.input_tokens or None,
                    "output_tokens": span.output_tokens or None,
                    "rag_recall_count": span.rag_recall_count or None,
                    "rag_rerank_score": span.rag_rerank_score if span.rag_rerank_score else None,
                    "success": span.success,
                    "error_message": span.error_message,
                })
            
            db.commit()
            logger.info(f"Trace persisted: {self.trace_id} ({len(self.spans)} spans, {self.total_duration_ms}ms)")
        
        except Exception as e:
            logger.error(f"Trace persist 失败: {type(e).__name__}: {e}", exc_info=True)
            try:
                db.rollback()
            except Exception:
                pass
            # fail-safe: 不抛出,trace 失败不影响业务


# ─── 内部辅助 ───

def _json_dumps(obj: Any) -> str:
    """安全 JSON 序列化。"""
    import json
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"_serialize_error": str(obj)[:200]})


def _truncate_dict(d: dict, max_str_len: int = 500) -> dict:
    """递归截断 dict 内的长字符串。"""
    if not isinstance(d, dict):
        return {}
    
    result = {}
    for k, v in d.items():
        if isinstance(v, str) and len(v) > max_str_len:
            result[k] = v[:max_str_len] + f"... (truncated, total {len(v)} chars)"
        elif isinstance(v, dict):
            result[k] = _truncate_dict(v, max_str_len)
        elif isinstance(v, list):
            # 只保留前 5 个元素,避免列表爆炸
            result[k] = v[:5] if len(v) > 5 else v
        else:
            result[k] = v
    return result
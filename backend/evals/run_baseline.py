"""跑学生端 Agent 评测集,产出 baseline 指标 JSON。

用法:
    cd backend
    python -m evals.run_baseline
    
输出: evals/results_<timestamp>.json
"""
import sys
import io
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# Windows 中文输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 静默 logger,避免 stdout 太乱
logging.basicConfig(level=logging.WARNING)

# load_dotenv
from dotenv import load_dotenv
load_dotenv()

from db.session import SessionLocal
from services.llm import generate_response_with_tools
from evals.student_eval_set import EVAL_CASES


SYSTEM_PROMPT = (
    "你是德语学习助教小智。可调用工具查询学生真实数据。"
    "当用户询问个人学情时主动调用 query_my_*;查词典或语法时调用 search_knowledge_base;"
    "推荐题目时调用 recommend_grammar_exercises。"
    "不需要工具时直接回答,不要硬塞工具调用。"
)


def run_one_case(case: dict, student_id: int = 1) -> dict:
    """跑单个评测 case,返回结果 dict。"""
    db = SessionLocal()
    try:
        context = {"db": db, "student_id": student_id}
        messages = [{"role": "user", "content": case["query"]}]

        t_start = time.time()
        try:
            reply, tool_calls_used = generate_response_with_tools(
                messages=messages,
                system_instruction=SYSTEM_PROMPT,
                context=context,
            )
            success = True
            error = None
        except Exception as e:
            reply = ""
            tool_calls_used = []
            success = False
            error = f"{type(e).__name__}: {e}"
        elapsed = time.time() - t_start

        actual_tools = {tc["name"] for tc in tool_calls_used}
        expected = set(case["expected_tools"])

        # 召回率: 期望被调的中实际有多少被调
        recall = (
            len(actual_tools & expected) / len(expected) if expected else 1.0
        )
        # 精确率: 实际调的中有多少在期望内
        # (空查询时若没调工具,精确率算 1.0;若不该调却调了,算 0)
        if not actual_tools:
            precision = 1.0 if not expected else 0.0
        else:
            precision = len(actual_tools & expected) / len(actual_tools)

        return {
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "expected_tools": sorted(expected),
            "actual_tools": sorted(actual_tools),
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "iterations_used": max(
                (tc["iteration"] for tc in tool_calls_used), default=0
            ),
            "tool_call_count": len(tool_calls_used),
            "elapsed_sec": round(elapsed, 2),
            "success": success,
            "error": error,
            "reply_preview": (reply or "")[:120],
        }
    finally:
        db.close()


def aggregate_metrics(results: list[dict]) -> dict:
    """聚合所有 case 的指标。"""
    n = len(results)
    success_count = sum(1 for r in results if r["success"])

    # 只对成功的 case 算指标
    successful = [r for r in results if r["success"]]
    if not successful:
        return {"total": n, "success_count": 0, "error": "全部失败"}

    avg_recall = sum(r["recall"] for r in successful) / len(successful)
    avg_precision = sum(r["precision"] for r in successful) / len(successful)
    avg_iterations = sum(r["iterations_used"] for r in successful) / len(successful)
    avg_tool_calls = sum(r["tool_call_count"] for r in successful) / len(successful)
    avg_elapsed = sum(r["elapsed_sec"] for r in successful) / len(successful)

    # 按 category 分组
    by_category = {}
    for r in successful:
        cat = r["category"]
        by_category.setdefault(cat, []).append(r)
    
    category_metrics = {}
    for cat, items in by_category.items():
        category_metrics[cat] = {
            "count": len(items),
            "avg_recall": round(sum(i["recall"] for i in items) / len(items), 3),
            "avg_precision": round(sum(i["precision"] for i in items) / len(items), 3),
            "avg_elapsed": round(sum(i["elapsed_sec"] for i in items) / len(items), 2),
        }

    return {
        "total": n,
        "success_count": success_count,
        "success_rate": round(success_count / n, 3),
        "overall_recall": round(avg_recall, 3),
        "overall_precision": round(avg_precision, 3),
        "avg_iterations_per_query": round(avg_iterations, 2),
        "avg_tool_calls_per_query": round(avg_tool_calls, 2),
        "avg_elapsed_sec": round(avg_elapsed, 2),
        "by_category": category_metrics,
    }


def main():
    print("=" * 70)
    print(f"Agent Baseline 评测开始: {len(EVAL_CASES)} cases")
    print(f"开始时间: {datetime.now().isoformat()}")
    print("=" * 70)

    results = []
    for i, case in enumerate(EVAL_CASES, 1):
        print(f"\n[{i}/{len(EVAL_CASES)}] {case['id']} ({case['category']})")
        print(f"  Query: {case['query']}")
        result = run_one_case(case)
        results.append(result)
        
        marker = "✓" if result["success"] else "✗"
        print(
            f"  {marker} recall={result['recall']} precision={result['precision']} "
            f"tools={result['actual_tools']} elapsed={result['elapsed_sec']}s"
        )
        if not result["success"]:
            print(f"  ERROR: {result['error']}")

    # 聚合
    metrics = aggregate_metrics(results)

    # 写文件
    output = {
        "run_at": datetime.now().isoformat(),
        "version": "baseline_v1_pre_refactor",  # 重构前的标记
        "system_prompt": SYSTEM_PROMPT,
        "metrics": metrics,
        "details": results,
    }
    
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"baseline_pre_{timestamp}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print("评测完成")
    print("=" * 70)
    print(f"总 case 数: {metrics['total']}")
    print(f"成功率: {metrics['success_rate']}")
    print(f"工具召回率: {metrics['overall_recall']}")
    print(f"工具精确率: {metrics['overall_precision']}")
    print(f"平均 ReAct 轮数: {metrics['avg_iterations_per_query']}")
    print(f"平均工具调用数: {metrics['avg_tool_calls_per_query']}")
    print(f"平均响应耗时: {metrics['avg_elapsed_sec']}s")
    print(f"\n按类型分组:")
    for cat, m in metrics["by_category"].items():
        print(f"  {cat}: recall={m['avg_recall']} precision={m['avg_precision']} elapsed={m['avg_elapsed']}s ({m['count']} cases)")
    print(f"\n结果已写入: {out_path}")


if __name__ == "__main__":
    main()
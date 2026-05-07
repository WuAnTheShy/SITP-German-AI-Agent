"""跑学生 + 教师双端 Agent 评测集 v2,产出指标 JSON。

用法:
    cd backend
    python -m evals.run_baseline
    
环境变量:
    HYBRID_SEARCH_ENABLED=true|false  控制混合检索开关(对比测试用)
    
输出: evals/results/baseline_<student|teacher>_<timestamp>.json
"""
import sys
import io
import os
import logging
import json
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
logging.basicConfig(level=logging.WARNING)

from dotenv import load_dotenv
load_dotenv()

from db.session import SessionLocal
from services.llm import generate_response_with_tools
from evals.student_eval_set import STUDENT_EVAL_CASES, TEACHER_EVAL_CASES


STUDENT_PROMPT = (
    "你是德语学习助教小智。可调用工具查询学生真实数据。"
    "当用户询问个人学情时主动调用 query_my_*;查词典或语法时调用 search_knowledge_base;"
    "推荐题目时调用 recommend_grammar_exercises。"
    "不需要工具时直接回答,不要硬塞工具调用。"
)

TEACHER_PROMPT = (
    "你是德语教研助手小研。可调用工具查询所教班级和学生数据辅助教学决策。"
    "班务问题用 query_class_overview/find_struggling_students,"
    "学生分析用 query_student_by_uid,考试规划用 recommend_exam_focus,"
    "查词典用 search_knowledge_base。"
    "教学法/教研咨询不需要工具,直接给建议。"
)


def run_one_case(case: dict, role: str) -> dict:
    """跑单个评测 case。"""
    db = SessionLocal()
    try:
        if role == "student":
            context = {"db": db, "student_id": 1}
            system_prompt = STUDENT_PROMPT
            toolset = "student"
        else:  # teacher
            context = {"db": db, "teacher_user_id": 2}
            system_prompt = TEACHER_PROMPT
            toolset = "teacher"
        
        messages = [{"role": "user", "content": case["query"]}]

        t_start = time.time()
        try:
            reply, tool_calls_used = generate_response_with_tools(
                messages=messages,
                system_instruction=system_prompt,
                context=context,
                toolset=toolset,
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

        recall = len(actual_tools & expected) / len(expected) if expected else 1.0
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
    n = len(results)
    success_count = sum(1 for r in results if r["success"])
    successful = [r for r in results if r["success"]]
    if not successful:
        return {"total": n, "success_count": 0, "error": "全部失败"}

    avg_recall = sum(r["recall"] for r in successful) / len(successful)
    avg_precision = sum(r["precision"] for r in successful) / len(successful)
    avg_iterations = sum(r["iterations_used"] for r in successful) / len(successful)
    avg_tool_calls = sum(r["tool_call_count"] for r in successful) / len(successful)
    avg_elapsed = sum(r["elapsed_sec"] for r in successful) / len(successful)

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


def run_eval_set(role: str, cases: list[dict], hybrid_flag: str) -> dict:
    """跑一个评测集(学生或教师),返回完整 result dict。"""
    print("\n" + "=" * 70)
    print(f"评测集: {role.upper()} ({len(cases)} cases) | hybrid={hybrid_flag}")
    print("=" * 70)
    
    results = []
    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case['id']} ({case['category']})")
        print(f"  Query: {case['query']}")
        result = run_one_case(case, role)
        results.append(result)
        marker = "✓" if result["success"] else "✗"
        print(
            f"  {marker} recall={result['recall']} precision={result['precision']} "
            f"tools={result['actual_tools']} elapsed={result['elapsed_sec']}s"
        )
        if not result["success"]:
            print(f"  ERROR: {result['error']}")
    
    metrics = aggregate_metrics(results)
    
    output = {
        "role": role,
        "run_at": datetime.now().isoformat(),
        "version": f"v2_hybrid_{hybrid_flag}",
        "system_prompt": STUDENT_PROMPT if role == "student" else TEACHER_PROMPT,
        "metrics": metrics,
        "details": results,
    }
    
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"v2_{role}_hybrid_{hybrid_flag}_{timestamp}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n[{role}] 完成: 召回={metrics['overall_recall']} 精确={metrics['overall_precision']} "
          f"耗时均值={metrics['avg_elapsed_sec']}s")
    print(f"输出: {out_path}")
    return output


def main():
    hybrid_flag = "on" if os.getenv("HYBRID_SEARCH_ENABLED", "true").lower() == "true" else "off"
    
    print("=" * 70)
    print(f"Agent 评测 v2 开始")
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"混合检索: {hybrid_flag}")
    print("=" * 70)

    student_result = run_eval_set("student", STUDENT_EVAL_CASES, hybrid_flag)
    teacher_result = run_eval_set("teacher", TEACHER_EVAL_CASES, hybrid_flag)
    
    # 输出最终对比汇总
    print("\n" + "=" * 70)
    print("评测完成 - 总览")
    print("=" * 70)
    print(f"\n【学生端 {len(STUDENT_EVAL_CASES)} cases】")
    sm = student_result["metrics"]
    print(f"  召回率: {sm['overall_recall']}  精确率: {sm['overall_precision']}  成功率: {sm['success_rate']}")
    print(f"  平均 ReAct 轮数: {sm['avg_iterations_per_query']}  平均工具调用: {sm['avg_tool_calls_per_query']}")
    print(f"  平均耗时: {sm['avg_elapsed_sec']}s")
    print(f"  按类别:")
    for cat, m in sm["by_category"].items():
        print(f"    {cat}: recall={m['avg_recall']} precision={m['avg_precision']} elapsed={m['avg_elapsed']}s ({m['count']} cases)")
    
    print(f"\n【教师端 {len(TEACHER_EVAL_CASES)} cases】")
    tm = teacher_result["metrics"]
    print(f"  召回率: {tm['overall_recall']}  精确率: {tm['overall_precision']}  成功率: {tm['success_rate']}")
    print(f"  平均 ReAct 轮数: {tm['avg_iterations_per_query']}  平均工具调用: {tm['avg_tool_calls_per_query']}")
    print(f"  平均耗时: {tm['avg_elapsed_sec']}s")
    print(f"  按类别:")
    for cat, m in tm["by_category"].items():
        print(f"    {cat}: recall={m['avg_recall']} precision={m['avg_precision']} elapsed={m['avg_elapsed']}s ({m['count']} cases)")


if __name__ == "__main__":
    main()
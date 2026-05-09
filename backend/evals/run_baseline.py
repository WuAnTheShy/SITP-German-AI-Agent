"""跑学生 + 教师 Agent 评测集 v2,通过真实 HTTP endpoint 触发,
产出指标 JSON + 真实 trace 数据。

用法:
    cd backend
    python -m evals.run_baseline
    
环境变量:
    EVAL_BASE_URL: API 基础 URL,默认 http://localhost:8000
    EVAL_STUDENT_USER: 学生账号,默认 2452001
    EVAL_STUDENT_PASS: 学生密码,默认 StudentDemo@2026!
    EVAL_TEACHER_USER: 教师账号,默认 26001
    EVAL_TEACHER_PASS: 教师密码,默认 TeacherDemo@2026!
    
输出: evals/results/v2_<role>_<timestamp>.json
"""
import sys
import io
import os
import logging
import json
import time
from datetime import datetime
from pathlib import Path

import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
logging.basicConfig(level=logging.WARNING)

from dotenv import load_dotenv
load_dotenv()

from evals.student_eval_set import STUDENT_EVAL_CASES, TEACHER_EVAL_CASES


BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")
STUDENT_USER = os.getenv("EVAL_STUDENT_USER", "2452001")
STUDENT_PASS = os.getenv("EVAL_STUDENT_PASS", "StudentDemo@2026!")
TEACHER_USER = os.getenv("EVAL_TEACHER_USER", "26001")
TEACHER_PASS = os.getenv("EVAL_TEACHER_PASS", "TeacherDemo@2026!")


def login(username: str, password: str) -> str:
    """登录拿 token。"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("token") or data.get("data", {}).get("token")
    if not token:
        raise RuntimeError(f"登录失败: {data}")
    return token


def run_one_case(case: dict, role: str, token: str) -> dict:
    """通过真实 HTTP endpoint 跑单个评测 case。"""
    endpoint = f"{BASE_URL}/api/{role}/chat"
    
    t_start = time.time()
    try:
        resp = requests.post(
            endpoint,
            json={"message": case["query"], "new_thread": True},
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
            timeout=300,  # 5 分钟超时(嵌套 LLM 调用可能很慢)
        )
        elapsed = time.time() - t_start
        
        if resp.status_code != 200:
            return {
                "id": case["id"],
                "category": case["category"],
                "query": case["query"],
                "expected_tools": sorted(set(case["expected_tools"])),
                "actual_tools": [],
                "recall": 0,
                "precision": 0,
                "iterations_used": 0,
                "tool_call_count": 0,
                "elapsed_sec": round(elapsed, 2),
                "success": False,
                "error": f"HTTP {resp.status_code}: {resp.text[:200]}",
                "trace_id": None,
                "rag_used": False,
                "reply_preview": "",
            }
        
        data = resp.json()
        reply = data.get("reply", "")
        tool_calls_used = data.get("tool_calls_used", [])
        trace_id = data.get("trace_id")
        rag_used = data.get("rag_used", False)
        
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
                (tc.get("iteration", 0) for tc in tool_calls_used), default=0
            ),
            "tool_call_count": len(tool_calls_used),
            "elapsed_sec": round(elapsed, 2),
            "success": True,
            "error": None,
            "trace_id": trace_id,
            "rag_used": rag_used,
            "reply_preview": reply[:120],
        }
    except Exception as e:
        elapsed = time.time() - t_start
        return {
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "expected_tools": sorted(set(case["expected_tools"])),
            "actual_tools": [],
            "recall": 0,
            "precision": 0,
            "iterations_used": 0,
            "tool_call_count": 0,
            "elapsed_sec": round(elapsed, 2),
            "success": False,
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "trace_id": None,
            "rag_used": False,
            "reply_preview": "",
        }


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

    by_category: dict = {}
    for r in successful:
        by_category.setdefault(r["category"], []).append(r)
    category_metrics = {
        cat: {
            "count": len(items),
            "avg_recall": round(sum(i["recall"] for i in items) / len(items), 3),
            "avg_precision": round(sum(i["precision"] for i in items) / len(items), 3),
            "avg_elapsed": round(sum(i["elapsed_sec"] for i in items) / len(items), 2),
        }
        for cat, items in by_category.items()
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


def run_eval_set(role: str, cases: list[dict], token: str) -> dict:
    print("\n" + "=" * 70)
    print(f"评测集: {role.upper()} ({len(cases)} cases),走真实 endpoint /api/{role}/chat")
    print("=" * 70)
    
    results = []
    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case['id']} ({case['category']})")
        print(f"  Query: {case['query']}")
        result = run_one_case(case, role, token)
        results.append(result)
        marker = "✓" if result["success"] else "✗"
        trace_short = (result.get("trace_id") or "")[:16] if result.get("trace_id") else "—"
        print(
            f"  {marker} recall={result['recall']} precision={result['precision']} "
            f"tools={result['actual_tools']} elapsed={result['elapsed_sec']}s "
            f"trace={trace_short}"
        )
        if not result["success"]:
            print(f"  ERROR: {result['error']}")
    
    metrics = aggregate_metrics(results)
    
    output = {
        "role": role,
        "run_at": datetime.now().isoformat(),
        "version": "v2_via_endpoint",
        "metrics": metrics,
        "details": results,
    }
    
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"v2_{role}_via_endpoint_{timestamp}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n[{role}] 完成: 召回={metrics['overall_recall']} 精确={metrics['overall_precision']} "
          f"耗时均值={metrics['avg_elapsed_sec']}s")
    print(f"输出: {out_path}")
    return output


def main():
    print("=" * 70)
    print(f"Agent 评测 v2 (via HTTP endpoint) 开始")
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"BASE_URL: {BASE_URL}")
    print("=" * 70)

    print("\n[登录] 学生 + 教师")
    student_token = login(STUDENT_USER, STUDENT_PASS)
    teacher_token = login(TEACHER_USER, TEACHER_PASS)
    print(f"  ✓ 登录成功")

    student_result = run_eval_set("student", STUDENT_EVAL_CASES, student_token)
    teacher_result = run_eval_set("teacher", TEACHER_EVAL_CASES, teacher_token)
    
    print("\n" + "=" * 70)
    print("评测完成 - 总览(每个 case 都走真实 endpoint,产生了真实 trace)")
    print("=" * 70)
    
    for label, r in [("学生端", student_result), ("教师端", teacher_result)]:
        m = r["metrics"]
        print(f"\n【{label} {m['total']} cases】")
        print(f"  召回率: {m['overall_recall']}  精确率: {m['overall_precision']}  成功率: {m['success_rate']}")
        print(f"  平均 ReAct 轮数: {m['avg_iterations_per_query']}  平均工具调用: {m['avg_tool_calls_per_query']}")
        print(f"  平均耗时: {m['avg_elapsed_sec']}s")
        for cat, mc in m["by_category"].items():
            print(f"    {cat}: recall={mc['avg_recall']} precision={mc['avg_precision']} elapsed={mc['avg_elapsed']}s ({mc['count']} cases)")
    
    print(f"\n💡 提示: 所有 trace 已写入 agent_traces 表,访问 http://localhost:{BASE_URL.rsplit(':', 1)[-1] if ':' in BASE_URL else 8000}/admin/observability 查看")


if __name__ == "__main__":
    main()
"""跑 v3 评测集:走真实 endpoint + LLM-as-Judge 任务完成度评分。

用法:
    python -m evals.run_v3
    
环境变量同 run_baseline.py。

输出: evals/results/v3_<role>_<timestamp>.json
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

from evals.student_eval_set_v3 import STUDENT_EVAL_CASES_V3, TEACHER_EVAL_CASES_V3
from evals.judge import judge_reply


BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")
STUDENT_USER = os.getenv("EVAL_STUDENT_USER", "2452001")
STUDENT_PASS = os.getenv("EVAL_STUDENT_PASS", "StudentDemo@2026!")
TEACHER_USER = os.getenv("EVAL_TEACHER_USER", "26001")
TEACHER_PASS = os.getenv("EVAL_TEACHER_PASS", "TeacherDemo@2026!")


def login(username: str, password: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("token") or data.get("data", {}).get("token")


def run_one_case(case: dict, role: str, token: str) -> dict:
    """跑单个 case:走真实 endpoint + 调 judge 打分。"""
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
            timeout=300,
        )
        elapsed = time.time() - t_start
        
        if resp.status_code != 200:
            return _make_failed_result(case, elapsed, f"HTTP {resp.status_code}: {resp.text[:200]}")
        
        data = resp.json()
        reply = data.get("reply", "")
        tool_calls_used = data.get("tool_calls_used", [])
        trace_id = data.get("trace_id")
        rag_used = data.get("rag_used", False)
        
        actual_tools = {tc["name"] for tc in tool_calls_used}
        expected = set(case["expected_tools"])
        accept_no_tool_when_rag = case.get("acceptable_no_tool_when_rag_used", False)
        
        # ─── 工具召回率(v3 加灵活规则) ───
        if not actual_tools:
            if not expected:
                tool_recall = 1.0  # 都不期望也没调,完美
            elif accept_no_tool_when_rag and rag_used:
                tool_recall = 1.0  # ← 关键:预 RAG 命中时不调工具也 OK
            else:
                tool_recall = 0.0
        else:
            tool_recall = len(actual_tools & expected) / len(expected) if expected else 0.0
        
        # 工具精确率(同 v2)
        if not actual_tools:
            tool_precision = 1.0 if not expected else (1.0 if accept_no_tool_when_rag and rag_used else 0.0)
        else:
            tool_precision = len(actual_tools & expected) / len(actual_tools)
        
        # ─── LLM-as-Judge 任务完成度 ───
        print(f"    [judge] 评估中...", end="", flush=True)
        judge_result = judge_reply(
            query=case["query"],
            expected_outcome=case.get("expected_outcome", ""),
            reply=reply,
        )
        print(f" → 总分 {judge_result['overall_score']}/5")
        
        return {
            "id": case["id"],
            "category": case["category"],
            "query": case["query"],
            "expected_tools": sorted(expected),
            "actual_tools": sorted(actual_tools),
            "tool_recall": round(tool_recall, 3),
            "tool_precision": round(tool_precision, 3),
            "judge": judge_result,
            "iterations_used": max(
                (tc.get("iteration", 0) for tc in tool_calls_used), default=0
            ),
            "tool_call_count": len(tool_calls_used),
            "elapsed_sec": round(elapsed, 2),
            "success": True,
            "error": None,
            "trace_id": trace_id,
            "rag_used": rag_used,
            "reply_preview": reply[:200],
            "expected_outcome": case.get("expected_outcome", ""),
        }
    except Exception as e:
        return _make_failed_result(case, time.time() - t_start, f"{type(e).__name__}: {str(e)[:200]}")


def _make_failed_result(case: dict, elapsed: float, error: str) -> dict:
    return {
        "id": case["id"],
        "category": case["category"],
        "query": case["query"],
        "expected_tools": sorted(set(case["expected_tools"])),
        "actual_tools": [],
        "tool_recall": 0,
        "tool_precision": 0,
        "judge": {
            "task_completion": 0, "relevance": 0, "groundedness": 0,
            "overall_score": 0.0, "reasoning": "Case 失败,未调用 judge",
        },
        "iterations_used": 0,
        "tool_call_count": 0,
        "elapsed_sec": round(elapsed, 2),
        "success": False,
        "error": error,
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
    
    avg_tool_recall = sum(r["tool_recall"] for r in successful) / len(successful)
    avg_tool_precision = sum(r["tool_precision"] for r in successful) / len(successful)
    avg_iterations = sum(r["iterations_used"] for r in successful) / len(successful)
    avg_tool_calls = sum(r["tool_call_count"] for r in successful) / len(successful)
    avg_elapsed = sum(r["elapsed_sec"] for r in successful) / len(successful)
    
    # LLM-as-Judge 聚合
    judged = [r for r in successful if not r["judge"].get("_judge_failed")]
    judge_avg = {
        "task_completion": round(sum(r["judge"]["task_completion"] for r in judged) / max(1, len(judged)), 2),
        "relevance": round(sum(r["judge"]["relevance"] for r in judged) / max(1, len(judged)), 2),
        "groundedness": round(sum(r["judge"]["groundedness"] for r in judged) / max(1, len(judged)), 2),
        "overall_score": round(sum(r["judge"]["overall_score"] for r in judged) / max(1, len(judged)), 2),
        "judged_count": len(judged),
        "judge_failed_count": len(successful) - len(judged),
    }
    
    by_category = {}
    for r in successful:
        by_category.setdefault(r["category"], []).append(r)
    category_metrics = {
        cat: {
            "count": len(items),
            "avg_tool_recall": round(sum(i["tool_recall"] for i in items) / len(items), 3),
            "avg_tool_precision": round(sum(i["tool_precision"] for i in items) / len(items), 3),
            "avg_judge_overall": round(
                sum(i["judge"]["overall_score"] for i in items if not i["judge"].get("_judge_failed")) 
                / max(1, len([i for i in items if not i["judge"].get("_judge_failed")])),
                2
            ),
            "avg_elapsed": round(sum(i["elapsed_sec"] for i in items) / len(items), 2),
        }
        for cat, items in by_category.items()
    }
    
    return {
        "total": n,
        "success_count": success_count,
        "success_rate": round(success_count / n, 3),
        "tool_recall": round(avg_tool_recall, 3),
        "tool_precision": round(avg_tool_precision, 3),
        "judge_metrics": judge_avg,
        "avg_iterations_per_query": round(avg_iterations, 2),
        "avg_tool_calls_per_query": round(avg_tool_calls, 2),
        "avg_elapsed_sec": round(avg_elapsed, 2),
        "by_category": category_metrics,
    }


def run_eval_set(role: str, cases: list[dict], token: str) -> dict:
    print("\n" + "=" * 70)
    print(f"评测集 v3: {role.upper()} ({len(cases)} cases)")
    print("=" * 70)
    
    results = []
    for i, case in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {case['id']} ({case['category']})")
        print(f"  Query: {case['query']}")
        result = run_one_case(case, role, token)
        results.append(result)
        if result["success"]:
            j = result["judge"]
            print(
                f"  ✓ tool_recall={result['tool_recall']} judge={j['overall_score']}/5 "
                f"(tc={j['task_completion']} rel={j['relevance']} gnd={j['groundedness']}) "
                f"elapsed={result['elapsed_sec']}s"
            )
        else:
            print(f"  ✗ ERROR: {result['error']}")
    
    metrics = aggregate_metrics(results)
    
    output = {
        "role": role,
        "run_at": datetime.now().isoformat(),
        "version": "v3_with_llm_judge",
        "metrics": metrics,
        "details": results,
    }
    
    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"v3_{role}_{timestamp}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    
    j = metrics["judge_metrics"]
    print(f"\n[{role}] 完成")
    print(f"  工具召回={metrics['tool_recall']} 工具精确={metrics['tool_precision']}")
    print(f"  Judge: 任务完成={j['task_completion']}/5 相关={j['relevance']}/5 有据={j['groundedness']}/5 总分={j['overall_score']}/5")
    print(f"  耗时均值={metrics['avg_elapsed_sec']}s")
    print(f"输出: {out_path}")
    return output


def main():
    print("=" * 70)
    print(f"Agent 评测 v3 (with LLM-as-Judge)")
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"BASE_URL: {BASE_URL}")
    print("=" * 70)
    
    print("\n[登录] 学生 + 教师")
    student_token = login(STUDENT_USER, STUDENT_PASS)
    teacher_token = login(TEACHER_USER, TEACHER_PASS)
    print(f"  ✓ 登录成功")
    
    student_result = run_eval_set("student", STUDENT_EVAL_CASES_V3, student_token)
    teacher_result = run_eval_set("teacher", TEACHER_EVAL_CASES_V3, teacher_token)
    
    print("\n" + "=" * 70)
    print("评测 v3 完成 - 总览")
    print("=" * 70)
    
    for label, r in [("学生端", student_result), ("教师端", teacher_result)]:
        m = r["metrics"]
        j = m["judge_metrics"]
        print(f"\n【{label} {m['total']} cases】")
        print(f"  工具召回: {m['tool_recall']}  工具精确: {m['tool_precision']}")
        print(f"  Judge 总分: {j['overall_score']}/5  (任务={j['task_completion']} 相关={j['relevance']} 有据={j['groundedness']})")
        print(f"  Judge 失败数: {j['judge_failed_count']}/{j['judged_count'] + j['judge_failed_count']}")
        print(f"  平均耗时: {m['avg_elapsed_sec']}s")
        print(f"  按类别:")
        for cat, mc in m["by_category"].items():
            print(f"    {cat}: tool_recall={mc['avg_tool_recall']} judge={mc['avg_judge_overall']}/5 elapsed={mc['avg_elapsed']}s ({mc['count']} cases)")


if __name__ == "__main__":
    main() 
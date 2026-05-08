"""对比两次 v3 评测的差异(修复前 vs 修复后)。

用法:
    python -m evals.compare_v3
    
自动从 evals/results/ 取最近 2 次 v3_student/v3_teacher,对比差异。
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def load_recent_results(role: str, count: int = 2) -> list[dict]:
    """取最近 count 次 v3 评测结果(降序)。"""
    results_dir = Path(__file__).parent / "results"
    files = sorted(
        results_dir.glob(f"v3_{role}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:count]
    if len(files) < 2:
        print(f"⚠️ {role} 端少于 2 次 v3 评测结果,无法对比")
        return []
    return [
        (f, json.loads(f.read_text(encoding="utf-8")))
        for f in files
    ]


def format_diff(before: float, after: float, decimals: int = 2) -> str:
    """格式化差值,带升降标记。"""
    diff = after - before
    if abs(diff) < 0.01:
        return f"{after:.{decimals}f} (─)"
    arrow = "↑" if diff > 0 else "↓"
    color_marker = "✅" if diff > 0 else "⚠️"
    return f"{after:.{decimals}f} {arrow}{abs(diff):.{decimals}f} {color_marker}"


def compare_role(role: str):
    files = load_recent_results(role)
    if not files:
        return
    
    (after_file, after_data), (before_file, before_data) = files
    
    print("\n" + "=" * 80)
    print(f"【{role.upper()} 端 v3 修复前 → 修复后对比】")
    print("=" * 80)
    print(f"修复前文件: {before_file.name}  ({before_data['run_at'][:19]})")
    print(f"修复后文件: {after_file.name}  ({after_data['run_at'][:19]})")
    print()
    
    bm = before_data["metrics"]
    am = after_data["metrics"]
    
    bj = bm["judge_metrics"]
    aj = am["judge_metrics"]
    
    print(f"  工具召回率:  {bm['tool_recall']:.3f} → {format_diff(bm['tool_recall'], am['tool_recall'], 3)}")
    print(f"  工具精确率:  {bm['tool_precision']:.3f} → {format_diff(bm['tool_precision'], am['tool_precision'], 3)}")
    print()
    print(f"  Judge 总分:           {bj['overall_score']:.2f} → {format_diff(bj['overall_score'], aj['overall_score'])}")
    print(f"  └─ task_completion: {bj['task_completion']:.2f} → {format_diff(bj['task_completion'], aj['task_completion'])}")
    print(f"  └─ relevance:       {bj['relevance']:.2f} → {format_diff(bj['relevance'], aj['relevance'])}")
    print(f"  └─ groundedness:    {bj['groundedness']:.2f} → {format_diff(bj['groundedness'], aj['groundedness'])}")
    print()
    print(f"  平均耗时:    {bm['avg_elapsed_sec']:.2f}s → {am['avg_elapsed_sec']:.2f}s")
    print()
    
    print("  按类别 Judge 总分:")
    for cat in bm["by_category"].keys():
        if cat not in am["by_category"]:
            continue
        b_score = bm["by_category"][cat]["avg_judge_overall"]
        a_score = am["by_category"][cat]["avg_judge_overall"]
        count = bm["by_category"][cat]["count"]
        print(f"    {cat:20s}: {b_score:.2f} → {format_diff(b_score, a_score)}  ({count} cases)")


def main():
    print("=" * 80)
    print(f"评测体系 v3 改进效果对比 (生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("=" * 80)
    
    compare_role("student")
    compare_role("teacher")
    
    print("\n" + "=" * 80)
    print("简历素材建议:")
    print("=" * 80)
    print("""
基于此次 EDD 闭环,可写入简历:

> 评测驱动开发(EDD)实践:通过 LLM-as-Judge 评测精准定位 2 个真问题
> (groundedness 偏低 + composite 类 fallback bug),针对性修复后重测,
> Judge 总分从 X.XX 升至 Y.YY (+提升幅度),验证了"观测 → 评测 → 发现 →
> 改进 → 验证"的工业级闭环方法论。
""")


if __name__ == "__main__":
    main()
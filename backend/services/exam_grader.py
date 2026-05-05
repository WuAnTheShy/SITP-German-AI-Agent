"""试卷自动评分服务。

纯函数:不读数据库、不调 LLM、不依赖 Session。
输入题目 + 答案,返回评分结果。便于单元测试。
"""

from typing import Any


def _is_grammar_correct(user_answer: str, correct_answer: str) -> bool:
    """判断语法题答案是否正确。
    
    兼容多种答题格式:
      - "A" vs "A"          → True
      - "A. werden" vs "A"  → True (用户答案以正确答案开头)
      - "A" vs "A. werden"  → True (正确答案以用户答案开头)
    """
    if not correct_answer:
        return False
    u = (user_answer or "").strip()
    c = correct_answer.strip()
    return (
        u == c
        or u.startswith(c + ".")
        or u.startswith(c + " ")
        or c.startswith(u)
        or u.startswith(c)
    )


class ExamGrader:
    """试卷自动评分服务。"""

    @staticmethod
    def grade(content: list[dict], answers: dict[str, str]) -> dict[str, Any]:
        """对一份试卷的答案打分。
        
        Args:
            content: 试卷题目列表(每题 dict 含 type/answer/score 等)
            answers: 学生答案字典 {"0": "A", "1": "我的作文..."}
        
        Returns:
            {
                "earned_score": 30,
                "wrong_questions": [
                    {"index": 0, "question": "...", "user_answer": "B", 
                     "correct_answer": "A"}
                ],
                "comment_lines": ["第 1 题(语法): 答错了..."]
            }
        """
        earned_score = 0
        wrong_questions = []
        comment_lines = []

        for idx, q_data in enumerate(content or []):
            q_score = q_data.get("score", 0)
            user_ans = answers.get(str(idx), "")

            if q_data.get("type") == "grammar":
                correct_ans = str(q_data.get("answer", ""))
                if _is_grammar_correct(user_ans, correct_ans):
                    earned_score += q_score
                else:
                    comment_lines.append(
                        f"第 {idx + 1} 题(语法): 答错了,你的答案 [{user_ans}];正确答案 [{correct_ans}]"
                    )
                    wrong_questions.append({
                        "index": idx,
                        "question": q_data.get("q") or q_data.get("content") or f"第 {idx + 1} 题",
                        "user_answer": user_ans,
                        "correct_answer": correct_ans,
                    })
            else:
                comment_lines.append(
                    f"第 {idx + 1} 题(写作): 已记录答案,待教师或 AI 后续评分。"
                )

        return {
            "earned_score": earned_score,
            "wrong_questions": wrong_questions,
            "comment_lines": comment_lines,
        }
"""测试 generate_response_with_tools 跑通各种工具调用。"""

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from dotenv import load_dotenv
load_dotenv("../.env")

from db.session import SessionLocal
from services.llm import generate_response_with_tools


SYSTEM_PROMPT = (
    "你是德语学习助教,叫小智。你可以调用工具查询学生的真实数据来回答问题。"
    "当用户询问个人相关信息(档案、能力、活动、作业)时,主动调用对应工具,"
    "不要凭空回答。回答用中文,简洁友好。"
)


def run_test(name: str, user_msg: str, *, student_id: int | None = None, teacher_user_id: int | None = None):
    """跑一次工具调用测试。
    
    必须传 student_id 或 teacher_user_id 之一。
    """
    db = SessionLocal()
    try:
        if teacher_user_id is not None:
            context = {"db": db, "teacher_user_id": teacher_user_id}
            role_label = f"教师 user_id={teacher_user_id}"
        else:
            context = {"db": db, "student_id": student_id}
            role_label = f"学生 student_id={student_id}"
        
        messages = [{"role": "user", "content": user_msg}]

        print("\n" + "=" * 70)
        print(f"测试: {name}")
        print(f"角色: {role_label}")
        print(f"用户问: {user_msg}")
        print("=" * 70)

        reply = generate_response_with_tools(
            messages=messages,
            system_instruction=SYSTEM_PROMPT,
            context=context,
        )

        print("\n--- Agent 回答 ---")
        print(reply)
        print("=" * 70)
    finally:
        db.close()


if __name__ == "__main__":
    # P0 三个工具的端到端测试
    
    # run_test(
    #     "1. 查档案(query_my_profile)",
    #     "你好,我是谁?帮我查一下我的档案信息。",
    # )
    
    # run_test(
    #     "2. 查能力(query_my_abilities)",
    #     "我现在德语水平怎么样?哪里比较弱?",
    # )
    
    # run_test(
    #     "3. 查最近活动(query_my_recent_activity)",
    #     "我最近一周都学了些什么?练习了多久?",
    # )
    
    # run_test(
    #     "4. 查作业(query_my_homeworks)",
    #     "我有哪些作业?完成了多少?",
    # )
    
    # run_test(
    #     "5. 复合查询(可能调多个工具)",
    #     "总结一下我最近的学习状态,告诉我应该重点改进哪方面。",
    # )

    # # P1 三个工具测试
    
    # run_test(
    #     "6. 查最近对话(query_my_recent_chats)",
    #     "我之前都问过些什么问题?帮我回顾一下。",
    # )
    
    # run_test(
    #     "7. 推荐练习题(recommend_grammar_exercises)",
    #     "给我推荐几道适合我的语法练习题吧。",
    # )
    
    # run_test(
    #     "8. 搜知识库(search_knowledge_base)",
    #     "Konjunktiv II 是什么?该怎么用?",
    # )
    
    # run_test(
    #     "9. 复合查询(P0 + P1 工具组合)",
    #     "结合我的薄弱点,推荐几道适合的练习题,然后告诉我相关语法规则。",
    # )


    # ─── 教师端 P0 工具测试(teacher_user_id=2 是张老师) ───
    
    run_test(
        "10. 班级总览(query_class_overview)",
        "我教的班整体情况怎么样?学生水平如何?",
        teacher_user_id=2,
    )
    
    run_test(
        "11. 查指定学生(query_student_by_uid)",
        "学号 2452001 的同学最近怎么样?给我看看她的学情。",
        teacher_user_id=2,
    )
    
    run_test(
        "12. 找薄弱学生(find_struggling_students)",
        "我班里听力最弱的同学是谁?",
        teacher_user_id=2,
    )
    
    run_test(
        "13. 推荐考点(recommend_exam_focus)",
        "下次考试我应该重点考什么内容?",
        teacher_user_id=2,
    )
    
    run_test(
        "14. 教师复合查询",
        "总结一下我班整体情况,并告诉我哪几个学生需要特别关注,以及下次考试应该考什么。",
        teacher_user_id=2,
    )
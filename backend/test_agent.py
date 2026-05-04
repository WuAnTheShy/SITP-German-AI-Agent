"""测试 generate_response_with_tools 真正能跑通工具循环。"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载 .env
from dotenv import load_dotenv
load_dotenv("../.env")

from db.session import SessionLocal
from services.llm import generate_response_with_tools


def test_query_my_profile():
    """测试 query_my_profile 工具调用。"""
    db = SessionLocal()
    try:
        # 假设 student_id=1（演示账号 s_li 李娜）
        context = {"db": db, "student_id": 1}
        
        messages = [
            {"role": "user", "content": "你好,我是谁?帮我查一下我的档案信息。"},
        ]
        
        system = (
            "你是德语学习助教,可以使用工具查询学生信息。"
            "当用户询问个人相关问题时,主动调用对应的工具获取真实数据。"
        )
        
        print("=" * 60)
        print("测试: 用户询问自己的档案")
        print("=" * 60)
        
        reply = generate_response_with_tools(
            messages=messages,
            system_instruction=system,
            context=context,
        )
        
        print("\n" + "=" * 60)
        print("最终回答:")
        print("=" * 60)
        print(reply)
    finally:
        db.close()


if __name__ == "__main__":
    test_query_my_profile()
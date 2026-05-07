生成一份德语考试卷。重点考察：{topics_str}。总分：{total_score}。

要求 {sections_count} 个 section，每 section 含 2-3 道题（不要太多）。
每题包含：题型(grammar/vocabulary/translation/writing)、题干（德语）、答案、分值、解析。
所有 section 分值之和必须等于 {total_score}。

只输出 JSON，不要任何解释文字、不要 markdown 代码块标记。直接以 {{ 开头，以 }} 结尾。

JSON 格式示例：
{{
  "title": "德语周测 - 虚拟式与被动语态",
  "total_score": {total_score},
  "duration_minutes": 60,
  "sections": [
    {{
      "section_name": "一、语法填空",
      "instruction": "在空格处填入正确的形式",
      "subtotal_score": 30,
      "questions": [
        {{"type": "grammar", "question": "Wenn ich Zeit ___ (haben), ginge ich.", "answer": "hätte", "score": 6, "analysis": "虚拟式 II"}}
]
}}
]
}}

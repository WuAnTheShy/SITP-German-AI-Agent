"""学生 + 教师 Agent 评测集 v2。

设计原则:
1. query 用真实师生口语表达,不用实验室技术语言
2. knowledge_query 只用词典确实有的词(SQL 验证过)
3. 教师场景覆盖班务/备课/学情/咨询
4. expected_tools 用 set 比较顺序无关
"""

# ════════════════ 学生端评测集 ════════════════

STUDENT_EVAL_CASES = [
    # ─── 学情类(5个): 真实学生口语 ───
    {
        "id": "ST01",
        "category": "profile_query",
        "query": "我哪里学得不好啊?",
        "expected_tools": {"query_my_abilities"},
    },
    {
        "id": "ST02",
        "category": "profile_query",
        "query": "我这周学了多久?都干嘛了?",
        "expected_tools": {"query_my_recent_activity"},
    },
    {
        "id": "ST03",
        "category": "profile_query",
        "query": "我作业完成情况怎么样,平均分多少?",
        "expected_tools": {"query_my_homeworks"},
    },
    {
        "id": "ST04",
        "category": "profile_query",
        "query": "我之前都问过些什么问题?",
        "expected_tools": {"query_my_recent_chats"},
    },
    {
        "id": "ST05",
        "category": "profile_query",
        "query": "我叫什么来着?哪个班的?",
        "expected_tools": {"query_my_profile"},
    },
    
    # ─── 知识类(4个): 词典里真有的词 ───
    {
        "id": "ST06",
        "category": "knowledge_query",
        "query": "Lehrer 在德语里啥意思?",
        "expected_tools": {"search_knowledge_base"},
    },
    {
        "id": "ST07",
        "category": "knowledge_query",
        "query": "Computer 这个词德语怎么说,有变形吗?",
        "expected_tools": {"search_knowledge_base"},
    },
    {
        "id": "ST08",
        "category": "knowledge_query",
        "query": "Freund 跟 Freundin 什么区别?",
        "expected_tools": {"search_knowledge_base"},
    },
    {
        "id": "ST09",
        "category": "knowledge_query",
        "query": "我想查一下 Familie 这个词",
        "expected_tools": {"search_knowledge_base"},
    },
    
    # ─── 综合任务(3个): 多工具协作 ───
    {
        "id": "ST10",
        "category": "composite",
        "query": "根据我的薄弱点,帮我推荐几道练习题",
        "expected_tools": {"recommend_grammar_exercises"},
        "notes": "工具内部已查 weak_point,LLM 跳过冗余调用是正确行为",
    },
    {
        "id": "ST11",
        "category": "composite",
        "query": "总结一下我最近的学习状态,给点建议",
        "expected_tools": {"query_my_abilities", "query_my_recent_activity"},
    },
    {
        "id": "ST12",
        "category": "composite",
        "query": "我哪里弱?推荐几道针对性的练习",
        "expected_tools": {"query_my_abilities", "recommend_grammar_exercises"},
    },
    
    # ─── 开放对话(3个): 不应调工具 ───
    {
        "id": "ST13",
        "category": "general_chat",
        "query": "你好,你是谁啊?",
        "expected_tools": set(),
    },
    {
        "id": "ST14",
        "category": "general_chat",
        "query": "学德语有什么好方法吗?",
        "expected_tools": set(),
    },
    {
        "id": "ST15",
        "category": "general_chat",
        "query": "谢啦,先这样",
        "expected_tools": set(),
    },
]


# ════════════════ 教师端评测集 ════════════════

TEACHER_EVAL_CASES = [
    # ─── 班务洞察(4个) ───
    {
        "id": "TE01",
        "category": "class_insight",
        "query": "我班学生整体水平怎么样?",
        "expected_tools": {"query_class_overview"},
    },
    {
        "id": "TE02",
        "category": "class_insight",
        "query": "哪几个学生需要重点关注?",
        "expected_tools": {"find_struggling_students"},
    },
    {
        "id": "TE03",
        "category": "class_insight",
        "query": "我班里听力最差的是谁?",
        "expected_tools": {"find_struggling_students"},
    },
    {
        "id": "TE04",
        "category": "class_insight",
        "query": "学生 2452002 王强这孩子学得怎么样?",
        "expected_tools": {"query_student_by_uid"},
    },
    
    # ─── 学情分析(3个) ───
    {
        "id": "TE05",
        "category": "student_analysis",
        "query": "李娜最近作业做得怎样?",
        "expected_tools": {"query_student_by_uid"},
    },
    {
        "id": "TE06",
        "category": "student_analysis",
        "query": "下次考试我应该重点考什么?",
        "expected_tools": {"recommend_exam_focus"},
    },
    {
        "id": "TE07",
        "category": "student_analysis",
        "query": "总结一下我班的情况,告诉我哪几个要重点抓,然后建议下次考啥",
        "expected_tools": {"query_class_overview", "find_struggling_students", "recommend_exam_focus"},
    },
    
    # ─── 教研咨询(3个,知识类) ───
    {
        "id": "TE08",
        "category": "knowledge_query",
        "query": "Lehrer 这个词怎么变复数?有什么需要注意的?",
        "expected_tools": {"search_knowledge_base"},
    },
    {
        "id": "TE09",
        "category": "knowledge_query",
        "query": "Computer 在德语里是阳性还是中性?",
        "expected_tools": {"search_knowledge_base"},
    },
    {
        "id": "TE10",
        "category": "knowledge_query",
        "query": "查一下 Auto 在词典里的释义",
        "expected_tools": {"search_knowledge_base"},
    },
    
    # ─── 开放对话(3个,不应调工具) ───
    {
        "id": "TE11",
        "category": "general_chat",
        "query": "你好,你能帮我做什么?",
        "expected_tools": set(),
    },
    {
        "id": "TE12",
        "category": "general_chat",
        "query": "怎么给学生讲虚拟式比较容易理解?",
        "expected_tools": set(),
        "notes": "教学法咨询,通用知识就够,不该调工具",
    },
    {
        "id": "TE13",
        "category": "general_chat",
        "query": "如何提升学生的学习兴趣?",
        "expected_tools": set(),
    },
    
    # ─── 边界场景(2个) ───
    {
        "id": "TE14",
        "category": "edge_case",
        "query": "学号 9999999 是哪个同学?",
        "expected_tools": {"query_student_by_uid"},
        "notes": "工具会返回'未找到',测试 Agent 处理空结果",
    },
    {
        "id": "TE15",
        "category": "edge_case",
        "query": "看看班里情况和重点学生,然后查 Lehrer 这词",
        "expected_tools": {"query_class_overview", "find_struggling_students", "search_knowledge_base"},
        "notes": "学情 + 知识混合场景",
    },
]


# 兼容旧脚本(默认导出学生端集合)
EVAL_CASES = STUDENT_EVAL_CASES
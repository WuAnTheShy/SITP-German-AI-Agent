"""学生 + 教师 Agent 评测集 v3。

v3 改进(相对 v2):
1. 加 acceptable_no_tool_when_rag_used 字段
   - 当 RAG 强命中(top_score >= 0.4)使 LLM 已能回答时,不调工具也算正确
   - 适用于 knowledge_query 类
2. 加 expected_outcome 字段(给 LLM-as-Judge 用)
   - 描述"任务成功的标准"
   - LLM 据此判断 reply 是否完成任务
"""

# ════════════════ 学生端 v3 ════════════════

STUDENT_EVAL_CASES_V3 = [
    # ─── 学情类(5个) ───
    {
        "id": "ST01",
        "category": "profile_query",
        "query": "我哪里学得不好啊?",
        "expected_tools": {"query_my_abilities"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该明确指出学生薄弱的能力维度(如听力/口语/阅读/写作)和具体薄弱点(weak_point),并给出针对性建议",
    },
    {
        "id": "ST02",
        "category": "profile_query",
        "query": "我这周学了多久?都干嘛了?",
        "expected_tools": {"query_my_recent_activity"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该列出学生近期学习活动总时长和各模块分布(如情景对话/语法练习等)",
    },
    {
        "id": "ST03",
        "category": "profile_query",
        "query": "我作业完成情况怎么样,平均分多少?",
        "expected_tools": {"query_my_homeworks"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该报告作业总数、完成率、平均分,最好附作业列表",
    },
    {
        "id": "ST04",
        "category": "profile_query",
        "query": "我之前都问过些什么问题?",
        "expected_tools": {"query_my_recent_chats"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该列出学生最近对话的主要话题或会话标题",
    },
    {
        "id": "ST05",
        "category": "profile_query",
        "query": "我叫什么来着?哪个班的?",
        "expected_tools": {"query_my_profile"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该报告学生姓名、学号、班级",
    },
    
    # ─── 知识类(4个,允许"预 RAG 替代工具调用") ───
    {
        "id": "ST06",
        "category": "knowledge_query",
        "query": "Lehrer 在德语里啥意思?",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,    # ← 关键:RAG 命中时不调工具也 OK
        "expected_outcome": "应该解释 Lehrer 的中文意思'老师'(可能附词性、复数等)",
    },
    {
        "id": "ST07",
        "category": "knowledge_query",
        "query": "Computer 这个词德语怎么说,有变形吗?",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,
        "expected_outcome": "应该说明 Computer 在德语里就是 Computer(借词),阳性,可能附变形信息",
    },
    {
        "id": "ST08",
        "category": "knowledge_query",
        "query": "Freund 跟 Freundin 什么区别?",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,
        "expected_outcome": "应该说明 Freund 是男性朋友,Freundin 是女性朋友(且可能解释更深含义如'男友/女友')",
    },
    {
        "id": "ST09",
        "category": "knowledge_query",
        "query": "我想查一下 Familie 这个词",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,
        "expected_outcome": "应该解释 Familie 中文意思'家庭',词性等",
    },
    
    # ─── 综合任务(3个) ───
    {
        "id": "ST10",
        "category": "composite",
        "query": "根据我的薄弱点,帮我推荐几道练习题",
        "expected_tools": {"recommend_grammar_exercises"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该返回针对学生薄弱点的真实练习题(包含题干和参考答案)",
    },
    {
        "id": "ST11",
        "category": "composite",
        "query": "总结一下我最近的学习状态,给点建议",
        "expected_tools": {"query_my_abilities", "query_my_recent_activity"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该综合学生能力数据 + 学习活动数据,给出针对性改进建议",
    },
    {
        "id": "ST12",
        "category": "composite",
        "query": "我哪里弱?推荐几道针对性的练习",
        "expected_tools": {"query_my_abilities", "recommend_grammar_exercises"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该先指出学生薄弱点,再推荐针对性练习题",
    },
    
    # ─── 开放对话(3个) ───
    {
        "id": "ST13",
        "category": "general_chat",
        "query": "你好,你是谁啊?",
        "expected_tools": set(),
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该自我介绍为德语 AI 助教,语气友好",
    },
    {
        "id": "ST14",
        "category": "general_chat",
        "query": "学德语有什么好方法吗?",
        "expected_tools": set(),
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该给出 3-5 条具体的德语学习方法建议(如多听多说/专项练习/制定计划等)",
    },
    {
        "id": "ST15",
        "category": "general_chat",
        "query": "谢啦,先这样",
        "expected_tools": set(),
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该礼貌告别,鼓励学生继续学习,简短即可",
    },
]


# ════════════════ 教师端 v3 ════════════════

TEACHER_EVAL_CASES_V3 = [
    # ─── 班务洞察(4个) ───
    {
        "id": "TE01",
        "category": "class_insight",
        "query": "我班学生整体水平怎么样?",
        "expected_tools": {"query_class_overview"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该报告班级总人数、活跃度、四维能力均分、薄弱点分布",
    },
    {
        "id": "TE02",
        "category": "class_insight",
        "query": "哪几个学生需要重点关注?",
        "expected_tools": {"find_struggling_students"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该列出薄弱学生的姓名、学号、薄弱维度和分数",
    },
    {
        "id": "TE03",
        "category": "class_insight",
        "query": "我班里听力最差的是谁?",
        "expected_tools": {"find_struggling_students"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该指出听力维度最低分的具体学生(姓名+分数)",
    },
    {
        "id": "TE04",
        "category": "class_insight",
        "query": "学生 2452002 王强这孩子学得怎么样?",
        "expected_tools": {"query_student_by_uid"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该报告王强同学的能力评分、薄弱点、作业情况、错题数",
    },
    
    # ─── 学情分析(3个) ───
    {
        "id": "TE05",
        "category": "student_analysis",
        "query": "李娜最近作业做得怎样?",
        "expected_tools": {"query_student_by_uid"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该按姓名找到李娜并报告其作业完成情况",
    },
    {
        "id": "TE06",
        "category": "student_analysis",
        "query": "下次考试我应该重点考什么?",
        "expected_tools": {"recommend_exam_focus"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该基于学生错题数据推荐考试重点方向",
    },
    {
        "id": "TE07",
        "category": "student_analysis",
        "query": "总结一下我班的情况,告诉我哪几个要重点抓,然后建议下次考啥",
        "expected_tools": {"query_class_overview", "find_struggling_students", "recommend_exam_focus"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该综合班级数据 + 重点学生 + 考试方向,给出全面教学建议",
    },
    
    # ─── 教研咨询(3个,允许预 RAG 替代) ───
    {
        "id": "TE08",
        "category": "knowledge_query",
        "query": "Lehrer 这个词怎么变复数?有什么需要注意的?",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,
        "expected_outcome": "应该说明 Lehrer 的复数形式(die Lehrer,不变),强调德语-er 结尾男性职业词的零词尾复数特点",
    },
    {
        "id": "TE09",
        "category": "knowledge_query",
        "query": "Computer 在德语里是阳性还是中性?",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,
        "expected_outcome": "应该说明 Computer 是阳性(der Computer)",
    },
    {
        "id": "TE10",
        "category": "knowledge_query",
        "query": "查一下 Auto 在词典里的释义",
        "expected_tools": {"search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": True,
        "expected_outcome": "应该报告 Auto 的中文释义(汽车)和性别(中性,das Auto)",
    },
    
    # ─── 开放对话(3个) ───
    {
        "id": "TE11",
        "category": "general_chat",
        "query": "你好,你能帮我做什么?",
        "expected_tools": set(),
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该介绍助手能查询班级/学生学情、生成练习题、出试卷等具体能力",
    },
    {
        "id": "TE12",
        "category": "general_chat",
        "query": "怎么给学生讲虚拟式比较容易理解?",
        "expected_tools": set(),
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该给出虚拟式教学法建议,如对比英语/分阶段讲解/用情境引入等",
    },
    {
        "id": "TE13",
        "category": "general_chat",
        "query": "如何提升学生的学习兴趣?",
        "expected_tools": set(),
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该给出具体可操作的学习兴趣提升方法",
    },
    
    # ─── 边界场景(2个) ───
    {
        "id": "TE14",
        "category": "edge_case",
        "query": "学号 9999999 是哪个同学?",
        "expected_tools": {"query_student_by_uid"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该尝试调用工具查询,工具返回'未找到'后如实告知教师该学号不存在",
    },
    {
        "id": "TE15",
        "category": "edge_case",
        "query": "看看班里情况和重点学生,然后查 Lehrer 这词",
        "expected_tools": {"query_class_overview", "find_struggling_students", "search_knowledge_base"},
        "acceptable_no_tool_when_rag_used": False,
        "expected_outcome": "应该完成所有 3 个任务:班级总览 + 重点学生 + Lehrer 词义",
    },
]
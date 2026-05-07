"""学生端 Agent 评测集 v1。

每个 case 包含:
  - id: 唯一标识
  - category: 5 大类型(profile/knowledge/composite/general/edge)
  - query: 用户问题
  - expected_tools: 期望被调用的工具集(用 set 比较顺序无关)
  - notes: 标注理由,方便 review
"""

EVAL_CASES = [
    # ─── 类型 1: 学情查询(纯学情,不需要 KB) ───
    {
        "id": "S01",
        "category": "profile_query",
        "query": "我是谁?帮我看看档案",
        "expected_tools": {"query_my_profile"},
        "notes": "经典个人信息查询",
    },
    {
        "id": "S02",
        "category": "profile_query",
        "query": "我现在德语水平怎么样?哪里比较弱?",
        "expected_tools": {"query_my_abilities"},
        "notes": "明确指向能力评估",
    },
    {
        "id": "S03",
        "category": "profile_query",
        "query": "我最近一周都学了什么?练习了多久?",
        "expected_tools": {"query_my_recent_activity"},
        "notes": "时间范围 + 学习活动",
    },
    {
        "id": "S04",
        "category": "profile_query",
        "query": "我有哪些作业?完成了多少?平均分多少?",
        "expected_tools": {"query_my_homeworks"},
        "notes": "作业统计",
    },

    # ─── 类型 2: 知识检索(应该走 KB) ───
    {
        "id": "S05",
        "category": "knowledge_query",
        "query": "Apfel 在德语里什么意思?",
        "expected_tools": {"search_knowledge_base"},
        "notes": "词典查询,KB 应该有",
    },
    {
        "id": "S06",
        "category": "knowledge_query",
        "query": "der Schraubenzieher 怎么翻译?",
        "expected_tools": {"search_knowledge_base"},
        "notes": "专有名词词典查询",
    },
    {
        "id": "S07",
        "category": "knowledge_query",
        "query": "德语里和'颜色'相关的词有哪些?",
        "expected_tools": {"search_knowledge_base"},
        "notes": "词汇范畴查询",
    },
    {
        "id": "S08",
        "category": "knowledge_query",
        "query": "怎么用德语说'你好'?",
        "expected_tools": {"search_knowledge_base"},
        "notes": "基础翻译,KB 可能有可能没,但应该尝试",
    },

    # ─── 类型 3: 复合查询(多工具) ───
    {
        "id": "S09",
        "category": "composite",
        "query": "结合我的薄弱点给我推荐几道题",
        "expected_tools": {"query_my_abilities", "recommend_grammar_exercises"},
        "notes": "先查能力 → 再推荐",
    },
    {
        "id": "S10",
        "category": "composite",
        "query": "总结我最近的学习状态,告诉我应该改进哪方面",
        "expected_tools": {"query_my_abilities", "query_my_recent_activity"},
        "notes": "需要双数据源整合",
    },
    {
        "id": "S11",
        "category": "composite",
        "query": "我的作业怎么样?哪些方面要继续练?",
        "expected_tools": {"query_my_homeworks", "query_my_abilities"},
        "notes": "作业 + 能力分析",
    },
    {
        "id": "S12",
        "category": "composite",
        "query": "我之前问过哪些类型的问题,反映了什么学习偏好?",
        "expected_tools": {"query_my_recent_chats"},
        "notes": "对话历史分析",
    },

    # ─── 类型 4: 通用对话(不应调工具) ───
    {
        "id": "S13",
        "category": "general_chat",
        "query": "你好,你是谁?",
        "expected_tools": set(),
        "notes": "Agent 自我介绍,不需要工具",
    },
    {
        "id": "S14",
        "category": "general_chat",
        "query": "学德语有什么好的方法?",
        "expected_tools": set(),
        "notes": "开放性建议,通用知识就够",
    },
    {
        "id": "S15",
        "category": "general_chat",
        "query": "谢谢你,再见",
        "expected_tools": set(),
        "notes": "礼貌告别,绝对不该调工具",
    },
    {
        "id": "S16",
        "category": "general_chat",
        "query": "你能帮我做什么?",
        "expected_tools": set(),
        "notes": "能力介绍,不需要查数据",
    },

    # ─── 类型 5: 边界场景 ───
    {
        "id": "S17",
        "category": "edge_case",
        "query": "推荐一些虚拟式的题目",
        "expected_tools": {"recommend_grammar_exercises"},
        "notes": "明确分类指定,直接推荐",
    },
    {
        "id": "S18",
        "category": "edge_case",
        "query": "Konjunktiv II 怎么用?有相关练习吗?",
        "expected_tools": {"search_knowledge_base", "recommend_grammar_exercises"},
        "notes": "知识 + 推题混合,可能调 1 或 2 个",
    },
    {
        "id": "S19",
        "category": "edge_case",
        "query": "测试123",
        "expected_tools": set(),
        "notes": "无意义输入,Agent 应礼貌引导",
    },
    {
        "id": "S20",
        "category": "edge_case",
        "query": "我哪里弱呢?另外Konjunktiv II 是什么?",
        "expected_tools": {"query_my_abilities", "search_knowledge_base"},
        "notes": "学情 + 知识双类型,必须并行调",
    },
]
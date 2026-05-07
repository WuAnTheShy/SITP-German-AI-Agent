"""Agent 工具注册中心。

所有可被 Qwen 调用的工具都在这里登记。每个工具有两件东西：
  - schema: 给 Qwen 看的（OpenAI 工具 JSON 格式）
  - handler: 真正的实现函数（Python 可调用对象）

注册后，generate_response_with_tools 会自动把 schemas 发给 Qwen，
并把 Qwen 选中的工具调用 dispatch 到对应的 handler。
"""

from typing import Any, Callable
from . import handlers
import logging
logger = logging.getLogger(__name__)

class ToolRegistry:
    """简单的工具注册中心，按名字登记 schema + handler。"""

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
        toolsets: list[str] | None = None,
    ):
        """注册一个工具。
        
        Args:
            name: 工具名(技术标识)
            description: 给 LLM 看的描述
            parameters: JSON Schema 定义参数
            handler: 实际执行函数 (args, context) -> dict
            toolsets: 这个工具属于哪些工具集,可多选。
                     可选值: "student" / "teacher" / "common"
                     默认 ["student"](向后兼容)
        """
        if toolsets is None:
            toolsets = ["student"]
        self._tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
            "handler": handler,
            "toolsets": toolsets,
        }

    def get_schemas(self) -> list[dict[str, Any]]:
        """返回所有工具的 schema（用于发给 Qwen 的 tools 参数）。"""
        return [t["schema"] for t in self._tools.values()]
    
    def get_schemas_by_toolset(self, toolset: str) -> list[dict]:
        """返回某个工具集下所有工具的 schema(给 LLM 看)。
        
        Args:
            toolset: "student" / "teacher" / "common"
        
        Returns:
            该工具集下所有工具的 OpenAI 格式 schema 列表
        """
        return [
            tool["schema"]
            for tool in self._tools.values()
            if toolset in tool["toolsets"]
        ]

    def call(self, name: str, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """执行工具。根据工具名找到对应 handler

        context 里包含调用方信息（如 student_id、db session），handler 自己解构使用。
        """
        if name not in self._tools:
            return {"error": f"unknown tool: {name}"}
        try:
            handler = self._tools[name]["handler"]
            return handler(args, context)
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {type(e).__name__}: {e}")
            return {"error": f"{type(e).__name__}: {e}"}


# ─── 全局单例：所有工具在这里注册 ───
registry = ToolRegistry()


registry.register(
    name="query_my_profile",
    description=(
        "查询当前学生的基本档案信息，包括姓名、班级、学号等等。"
        "当用户询问'我是谁'、'我属于哪个班'等身份相关问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    handler=handlers.query_my_profile,
    toolsets=["student"],
)



registry.register(
    name="query_my_abilities",
    description=(
        "查询当前学生的德语四维能力评估(听/说/读/写,各 0-100 分)、"
        "AI 学情诊断、最薄弱和最强项。"
        "当用户询问'我哪里弱'、'我的能力如何'、'我的成绩怎么样'等问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    handler=handlers.query_my_abilities,
    toolsets=["student"],
)


registry.register(
    name="query_my_recent_activity",
    description=(
        "查询当前学生最近 N 天(默认 7 天)的学习活动统计:"
        "总学习时长、各模块(语法练习/词汇学习/智能对话/综合测验等)的活动次数和时长、"
        "最活跃的模块。"
        "当用户询问'我最近学了什么'、'我练习多久了'、'我最近在忙什么'等问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "查询的天数范围,默认 7 天,最大 30 天",
                "default": 7,
            },
        },
        "required": [],
    },
    handler=handlers.query_my_recent_activity,
    toolsets=["student"],
)


registry.register(
    name="query_my_homeworks",
    description=(
        "查询当前学生的作业列表,包括标题、状态、得分、提交时间、AI 评语摘要。"
        "支持按状态筛选(已完成/未提交/进行中/待订正/逾期补交)。"
        "当用户询问'我有哪些作业'、'我的作业成绩'、'我还有什么没做'等问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "返回最近多少条作业,默认 10,最大 30",
                "default": 10,
            },
            "status": {
                "type": "string",
                "description": "按状态筛选作业,留空则返回所有状态",
                "enum": ["已完成", "未提交", "进行中", "待订正", "逾期补交"],
            },
        },
        "required": [],
    },
    handler=handlers.query_my_homeworks,
    toolsets=["student"],
)



registry.register(
    name="query_my_recent_chats",
    description=(
        "查询当前学生最近的对话会话列表(标题、首问、消息数等),不返回完整对话原文。"
        "当用户询问'我之前都问过什么'、'最近聊了什么'、'我经常问哪类问题'时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "返回最近多少个会话,默认 5,最大 20",
                "default": 5,
            },
        },
        "required": [],
    },
    handler=handlers.query_my_recent_chats,
    toolsets=["student"],
)


registry.register(
    name="recommend_grammar_exercises",
    description=(
        "为当前学生推荐语法练习题。"
        "默认按学生薄弱点(weak_point)推荐;若指定 category_name 则按指定分类推。"
        "可选分类:动词变位、名词格变化、完成时、被动语态、虚拟式、介词搭配、句序。"
        "当用户询问'给我推荐几道题'、'我想练 xx 语法'、'有什么练习'时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "count": {
                "type": "integer",
                "description": "推荐多少道题,默认 5,最大 10",
                "default": 5,
            },
            "category_name": {
                "type": "string",
                "description": "可选语法分类名(中文),不指定则按薄弱点自动选",
                "enum": ["动词变位", "名词格变化", "完成时", "被动语态", "虚拟式", "介词搭配", "句序"],
            },
        },
        "required": [],
    },
    handler=handlers.recommend_grammar_exercises,
    toolsets=["student"],
)


registry.register(
    name="search_knowledge_base",
    description=(
        "检索德语学习知识库(教材、词典),返回与查询最相关的内容片段。"
        "适用于:德语词汇查询、语法规则查询、固定搭配、文化知识等开放性问题。"
        "当用户询问的问题需要查阅教材资料才能准确回答时使用。"
        "注意:个人学情问题(我的成绩/作业/能力)不要用此工具,用 query_my_* 系列工具。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索查询,通常是用户问题的关键提取(如'Konjunktiv II 用法'、'apple 德语怎么说')",
            },
            "top_k": {
                "type": "integer",
                "description": "返回最相关的 N 个片段,默认 3,最大 5",
                "default": 3,
            },
        },
        "required": ["query"],
    },
    handler=handlers.search_knowledge_base,
    toolsets=["student","teacher"],
)



registry.register(
    name="query_class_overview",
    description=(
        "查询教师所教班级的总览数据:学生数、活跃度、四维能力均分、薄弱点分布等。"
        "可指定 class_code 只看某一个班,默认查所有任教班级。"
        "当教师询问'班里整体水平'、'各班对比'、'班级活跃度'等问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "class_code": {
                "type": "string",
                "description": "可选,指定班级编码(如 'SE-2026-4'),不指定则返回所有任教班级",
            },
        },
        "required": [],
    },
    handler=handlers.query_class_overview,
    toolsets=["teacher"],
)


registry.register(
    name="query_student_by_uid",
    description=(
        "按学号查询指定学生的完整学情:能力四维分、薄弱点、最近作业、错题数等。"
        "工具会做权限校验,只能查询教师任教班级里的学生。"
        "当教师询问'XXX 同学怎么样'、'学号 XXXXX 的情况'时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "uid": {
                "type": "string",
                "description": "学生学号(7 位数字,例如 '2452001')",
            },
        },
        "required": ["uid"],
    },
    handler=handlers.query_student_by_uid,
    toolsets=["teacher"],
)


registry.register(
    name="find_struggling_students",
    description=(
        "找出薄弱学生:按指定维度('listening'/'speaking'/'reading'/'writing'/'overall')"
        "或综合分数,返回低于阈值的学生列表(按分数从低到高排)。"
        "当教师询问'谁需要重点关注'、'听力差的学生有哪些'、'班里最薄弱的几个'时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "dimension": {
                "type": "string",
                "description": "评估维度,默认 'overall'(综合)",
                "enum": ["listening", "speaking", "reading", "writing", "overall"],
                "default": "overall",
            },
            "threshold": {
                "type": "integer",
                "description": "薄弱阈值(低于此分数算薄弱),默认 60",
                "default": 60,
            },
            "limit": {
                "type": "integer",
                "description": "最多返回多少人,默认 20",
                "default": 20,
            },
        },
        "required": [],
    },
    handler=handlers.find_struggling_students,
    toolsets=["teacher"],
)


registry.register(
    name="recommend_exam_focus",
    description=(
        "基于学生错题热点,推荐试卷应该重点考察的方向。"
        "返回错题最多的 N 个来源(语法练习/试卷测验等)及覆盖学生数。"
        "当教师询问'下次考试该考什么'、'学生哪类题错最多'、'考试重点'时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "class_code": {
                "type": "string",
                "description": "可选,只分析某个班级(如 'SE-2026-4'),不指定则综合所有任教班级",
            },
            "top_n": {
                "type": "integer",
                "description": "返回前 N 个错题热点,默认 3",
                "default": 3,
            },
        },
        "required": [],
    },
    handler=handlers.recommend_exam_focus,
    toolsets=["teacher"],
)
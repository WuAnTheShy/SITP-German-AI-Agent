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
        parameters: dict[str, Any],
        handler: Callable[..., Any],
    ):
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
        }

    def get_schemas(self) -> list[dict[str, Any]]:
        """返回所有工具的 schema（用于发给 Qwen 的 tools 参数）。"""
        return [t["schema"] for t in self._tools.values()]

    def call(self, name: str, args: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """执行工具。

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
        "查询当前学生的基本档案信息，包括姓名、班级、学号。"
        "当用户询问'我是谁'、'我属于哪个班'等身份相关问题时使用。"
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    handler=handlers.query_my_profile,
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
)
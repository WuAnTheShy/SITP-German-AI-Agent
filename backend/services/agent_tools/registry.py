"""Agent 工具注册中心。

所有可被 Qwen 调用的工具都在这里登记。每个工具有两件东西：
  - schema: 给 Qwen 看的（OpenAI 工具 JSON 格式）
  - handler: 真正的实现函数（Python 可调用对象）

注册后，generate_response_with_tools 会自动把 schemas 发给 Qwen，
并把 Qwen 选中的工具调用 dispatch 到对应的 handler。
"""

from typing import Any, Callable

from . import handlers


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
            print(f"[AGENT-TOOL] {name} failed: {type(e).__name__}: {e}", flush=True)
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
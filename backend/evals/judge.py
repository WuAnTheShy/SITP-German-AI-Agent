"""LLM-as-Judge: 用 LLM 评估 Agent reply 的任务完成度。

每个 case 跑完后,把 (query, expected_outcome, actual_reply) 给 LLM,
让它打 1-5 分并解释。

设计:
- 用同一个 LLM 评估自己的输出有"裁判员当运动员"风险,
  但在没有 GPT-4 等更强模型可用时这是常见折中
- 评分用 5 级 likert,避免 LLM 倾向于打满分
"""
import logging
import json

from services.llm import ai_json


logger = logging.getLogger(__name__)


# JUDGE_PROMPT_TEMPLATE = """你是 AI 系统评估专家,需要客观评估一个 Agent 对用户问题的回答质量。

# 【用户问题】
# {query}

# 【任务期望(可参考,但回答方式可以多样)】
# {expected_outcome}

# 【Agent 实际回答】
# {reply}

# 请基于以下 3 个维度严格评分(1-5 分):

# 1. **task_completion** (任务完成度): 回答是否完成了用户的核心诉求?
#    - 5: 完全完成,信息准确完整
#    - 4: 基本完成,有小瑕疵
#    - 3: 部分完成,关键信息有缺失或不准确
#    - 2: 偏离主题或有明显错误
#    - 1: 未完成或完全错误

# 2. **relevance** (相关性): 回答是否紧扣问题,没有大段无关内容?
#    - 5: 完全聚焦
#    - 3: 部分跑题
#    - 1: 严重跑题

# 3. **groundedness** (有据性): 回答里的事实/数据是否可信(没有明显编造)?
#    - 5: 看起来基于真实数据/知识
#    - 3: 有些笼统但不算编造
#    - 1: 明显编造数据

# 输出严格 JSON(不要任何额外文字、不要 markdown):
# {{
#   "task_completion": 5,
#   "relevance": 5,
#   "groundedness": 5,
#   "overall_score": 5,
#   "reasoning": "中文简短说明评分理由(1-2 句)"
# }}

# 注意:
# - overall_score = round((task_completion + relevance + groundedness) / 3, 1)
# - 评分要严格,不要老好人式打满分
# - 回答看起来很长很详细但实际没解决问题的,task_completion 给 2-3 分
# """


# def judge_reply(query: str, expected_outcome: str, reply: str) -> dict:
#     """让 LLM 给 Agent reply 打分。
    
#     Returns:
#         dict: {
#           'task_completion': int,
#           'relevance': int,
#           'groundedness': int,
#           'overall_score': float,
#           'reasoning': str,
#           '_judge_failed': bool   # 失败时为 True
#         }
#     """
#     if not reply or not reply.strip():
#         return {
#             "task_completion": 1,
#             "relevance": 1,
#             "groundedness": 1,
#             "overall_score": 1.0,
#             "reasoning": "Agent 回答为空",
#             "_judge_failed": False,
#         }
    
#     prompt = JUDGE_PROMPT_TEMPLATE.format(
#         query=query,
#         expected_outcome=expected_outcome or "(未指定具体标准,按用户问题判断)",
#         reply=reply[:2000],   # 太长会浪费 token
#     )
    
#     try:
#         result = ai_json(prompt, max_tokens=500)
#         if not result or not isinstance(result, dict):
#             raise ValueError("LLM 返回非 dict")
        
#         tc = int(result.get("task_completion", 0))
#         rel = int(result.get("relevance", 0))
#         gnd = int(result.get("groundedness", 0))
        
#         # 校验合理范围
#         if not all(1 <= x <= 5 for x in (tc, rel, gnd)):
#             raise ValueError(f"分数不在 1-5: tc={tc} rel={rel} gnd={gnd}")
        
#         overall = round((tc + rel + gnd) / 3, 1)
        
#         return {
#             "task_completion": tc,
#             "relevance": rel,
#             "groundedness": gnd,
#             "overall_score": overall,
#             "reasoning": str(result.get("reasoning", ""))[:300],
#             "_judge_failed": False,
#         }
#     except Exception as e:
#         logger.warning(f"judge_reply 失败: {type(e).__name__}: {e}")
#         return {
#             "task_completion": 0,
#             "relevance": 0,
#             "groundedness": 0,
#             "overall_score": 0.0,
#             "reasoning": f"Judge 失败: {type(e).__name__}",
#             "_judge_failed": True,
#         }

JUDGE_PROMPT_TEMPLATE = """你是 AI 系统评估专家,需要客观评估一个 Agent 对用户问题的回答质量。

【用户问题】
{query}

【任务期望(可参考,但回答方式可以多样)】
{expected_outcome}

【Agent 调用的工具】
{tools_info}

【Agent 实际回答】
{reply}

请基于以下 3 个维度严格评分(1-5 分):

1. **task_completion** (任务完成度): 回答是否完成了用户的核心诉求?
   - 5: 完全完成,信息准确完整
   - 4: 基本完成,有小瑕疵
   - 3: 部分完成,关键信息有缺失或不准确
   - 2: 偏离主题或有明显错误
   - 1: 未完成或完全错误

2. **relevance** (相关性): 回答是否紧扣问题,没有大段无关内容?
   - 5: 完全聚焦
   - 3: 部分跑题
   - 1: 严重跑题

3. **groundedness** (有据性): 回答里的事实/数据是否可信?
   - 注意:**如果 Agent 调用了工具(见上方"Agent 调用的工具"),
     回答中引用的数据应被视为来自工具的真实数据,不算编造**
   - 只有当回答中含有工具未提供的具体数据(姓名/分数/日期等),且 Agent 没调相关工具时,才视为编造
   - 5: 看起来基于真实数据/知识(或工具调用结果)
   - 3: 有些笼统但不算编造
   - 1: 明显编造(且无对应工具调用支持)

输出严格 JSON(不要任何额外文字、不要 markdown):
{{
  "task_completion": 5,
  "relevance": 5,
  "groundedness": 5,
  "overall_score": 5,
  "reasoning": "中文简短说明评分理由(1-2 句)"
}}

注意:
- overall_score = round((task_completion + relevance + groundedness) / 3, 1)
- 评分要严格,不要老好人式打满分
- 回答看起来很长很详细但实际没解决问题的,task_completion 给 2-3 分
"""


def judge_reply(query: str, expected_outcome: str, reply: str, tool_calls_used: list = None) -> dict:
    """让 LLM 给 Agent reply 打分。"""
    if not reply or not reply.strip():
        return {
            "task_completion": 1,
            "relevance": 1,
            "groundedness": 1,
            "overall_score": 1.0,
            "reasoning": "Agent 回答为空",
            "_judge_failed": False,
        }
    
    # 构造工具调用上下文
    if tool_calls_used:
        tools_info = "Agent 调用了以下工具(其返回的数据应被视为可信的真实数据):\n"
        for tc in tool_calls_used:
            tools_info += f"  - {tc.get('display_name', tc['name'])}({tc.get('args', {})})\n"
    else:
        tools_info = "Agent 未调用任何工具(回答完全基于通用知识)"
    
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        query=query,
        expected_outcome=expected_outcome or "(未指定具体标准,按用户问题判断)",
        tools_info=tools_info,
        reply=reply[:2000],
    )
    
    try:
        result = ai_json(prompt, max_tokens=500)
        if not result or not isinstance(result, dict):
            raise ValueError("LLM 返回非 dict")
        
        tc = int(result.get("task_completion", 0))
        rel = int(result.get("relevance", 0))
        gnd = int(result.get("groundedness", 0))
        
        if not all(1 <= x <= 5 for x in (tc, rel, gnd)):
            raise ValueError(f"分数不在 1-5: tc={tc} rel={rel} gnd={gnd}")
        
        overall = round((tc + rel + gnd) / 3, 1)
        
        return {
            "task_completion": tc,
            "relevance": rel,
            "groundedness": gnd,
            "overall_score": overall,
            "reasoning": str(result.get("reasoning", ""))[:300],
            "_judge_failed": False,
        }
    except Exception as e:
        logger.warning(f"judge_reply 失败: {type(e).__name__}: {e}")
        return {
            "task_completion": 0,
            "relevance": 0,
            "groundedness": 0,
            "overall_score": 0.0,
            "reasoning": f"Judge 失败: {type(e).__name__}",
            "_judge_failed": True,
        }
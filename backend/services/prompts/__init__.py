"""Prompt template 集中管理。

设计原则:
- 每个 prompt 独立 .md 文件,便于版本管理 + A/B 测试
- 通过 load_prompt(name) 加载,内部缓存避免重复 I/O
- 支持 {variable} 占位符,通过 render(name, **kwargs) 渲染
- 所有 prompt 文件位于本包目录下

使用示例:
    from services.prompts import load_prompt, render_prompt
    
    # 加载原始模板(供 system_instruction 使用)
    sys_prompt = load_prompt("student_agent")
    
    # 渲染带变量的模板(供 ai_json/ai_text 使用)
    user_prompt = render_prompt(
        "gen_grammar_exercises",
        category="虚拟式",
        count=5,
        difficulty_hint="中等水平",
    )
"""
from pathlib import Path
import logging


logger = logging.getLogger(__name__)

# prompt 文件存放目录(本 __init__.py 同级)
PROMPTS_DIR = Path(__file__).parent

# 内存缓存:避免每次调用都读文件
_PROMPT_CACHE: dict[str, str] = {}


def load_prompt(name: str) -> str:
    """加载指定 prompt 模板的原始内容。
    
    Args:
        name: prompt 名称(对应 prompts/ 目录下的 {name}.md 文件)
    
    Returns:
        prompt 模板的完整文本。
    
    Raises:
        FileNotFoundError: prompt 文件不存在。
    """
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]
    
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt 模板不存在: {path}\n"
            f"可用模板: {[p.stem for p in PROMPTS_DIR.glob('*.md')]}"
        )
    
    content = path.read_text(encoding="utf-8")
    _PROMPT_CACHE[name] = content
    logger.debug(f"Loaded prompt: {name} ({len(content)} chars)")
    return content


def render_prompt(name: str, **kwargs) -> str:
    """加载并渲染 prompt 模板,替换占位符。
    
    Args:
        name: prompt 名称
        **kwargs: 用于替换 {variable} 占位符的变量
    
    Returns:
        渲染后的完整 prompt 文本。
    
    Example:
        render_prompt("gen_grammar_exercises", category="虚拟式", count=5)
    """
    template = load_prompt(name)
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(
            f"Prompt '{name}' 缺少必要变量: {e}. "
            f"已提供: {list(kwargs.keys())}"
        ) from e


def reload_prompts():
    """清空缓存,强制下次 load_prompt 重新读文件。
    
    开发时改 markdown 后调用此函数即可生效,无需重启服务。
    """
    _PROMPT_CACHE.clear()
    logger.info("Prompt cache cleared")
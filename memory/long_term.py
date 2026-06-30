import os
from typing import Literal
from mem0 import Memory, MemoryClient
from config.settings import MEM0_API_KEY, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, QDRANT_URL
from loguru import logger

# Mem0 的 openai provider 通过环境变量读取自定义 endpoint
os.environ.setdefault("OPENAI_API_KEY", DEEPSEEK_API_KEY)
os.environ.setdefault("OPENAI_BASE_URL", DEEPSEEK_BASE_URL)

_memory = None


_cloud_client = None

MemoryCategory = Literal["user_profile", "stock_judgment", "task_history"]

CATEGORY_LABELS: dict[str, str] = {
    "user_profile": "用户画像",
    "stock_judgment": "股票实体记忆",
    "task_history": "任务历史",
}

def _get_cloud_client() -> MemoryClient:
    global _cloud_client
    if _cloud_client is None:
        _cloud_client = MemoryClient(api_key=MEM0_API_KEY)
        logger.info("Mem0 云端模式：记忆跨设备持久化")
    return _cloud_client


def _get_memory() -> Memory:
    global _memory
    if _memory is None:
        qdrant_config = {
            "collection_name": "user_memory",
            "embedding_model_dims": 512,
        }
        if QDRANT_URL:
            qdrant_config["url"] = QDRANT_URL
        else:
            qdrant_config["path"] = "/tmp/mem0_qdrant"
        config = {
            "llm": {
                "provider": "openai",
                "config": {"model": DEEPSEEK_MODEL, "api_key": DEEPSEEK_API_KEY},
            },
            "vector_store": {"provider": "qdrant", "config": qdrant_config},
            "embedder": {
                "provider": "huggingface",
                "config": {"model": "BAAI/bge-small-zh-v1.5"},
            },
        }
        _memory = Memory.from_config(config)
        logger.warning("Mem0 本地模式，记忆不跨设备持久化")
    return _memory


def remember_memory(user_id: str, content: str, category: MemoryCategory = "user_profile") -> str:
    """Store typed memory for profile, stock judgments, or task history."""
    label = CATEGORY_LABELS.get(category, category)
    tagged_content = f"[{label}] {content}"
    try:
        if MEM0_API_KEY:
            client = _get_cloud_client()
            client.add([{"role": "user", "content": tagged_content}], user_id=user_id)
        else:
            mem = _get_memory()
            mem.add(tagged_content, user_id=user_id)
        logger.info(f"记忆存储: user={user_id}, category={category}, content={content[:50]}")
        return f"已记住[{label}]: {content}"
    except Exception as e:
        logger.error(f"记忆存储失败: {e}")
        return f"记忆存储失败: {str(e)}"


def remember_user_preference(user_id: str, content: str) -> str:
    """存储用户偏好（持仓、风险偏好、关注板块等）"""
    return remember_memory(user_id, content, category="user_profile")


def recall_user_context(user_id: str, query: str, category: MemoryCategory | None = None) -> str:
    """根据当前问题检索用户相关记忆"""
    label = CATEGORY_LABELS.get(category, "") if category else ""
    search_query = f"[{label}] {query}" if label else query
    try:
        if MEM0_API_KEY:
            client = _get_cloud_client()
            results = client.search(search_query, user_id=user_id, limit=5)
            # MemoryClient.search() returns a list directly
            memories = results if isinstance(results, list) else results.get("results", [])
        else:
            mem = _get_memory()
            results = mem.search(search_query, user_id=user_id, limit=5)
            memories = results.get("results", []) if isinstance(results, dict) else results
        if not memories:
            return "暂无该用户的历史记忆"
        lines = [f"- {m.get('memory', m.get('content', str(m)))}" for m in memories]
        return "用户历史记忆:\n" + "\n".join(lines)
    except Exception as e:
        logger.error(f"记忆检索失败: {e}")
        return ""


def remember_stock_judgment(user_id: str, ts_code: str, judgment: str) -> str:
    """记录对某只股票的分析判断（实体记忆）"""
    content = f"关于股票 {ts_code}：{judgment}"
    return remember_memory(user_id, content, category="stock_judgment")


def recall_stock_history(user_id: str, ts_code: str) -> str:
    """检索对某只股票的历史判断"""
    return recall_user_context(user_id, f"股票 {ts_code} 的历史分析判断", category="stock_judgment")


def remember_task_history(user_id: str, task_summary: str) -> str:
    """记录任务执行历史，用于跨会话恢复上下文。"""
    return remember_memory(user_id, task_summary, category="task_history")


def recall_user_profile(user_id: str, query: str = "持仓 风险偏好 关注板块") -> str:
    """检索用户画像记忆。"""
    return recall_user_context(user_id, query, category="user_profile")

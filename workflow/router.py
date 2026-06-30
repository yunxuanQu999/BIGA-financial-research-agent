import re
from dataclasses import dataclass
from typing import Literal

from loguru import logger

from memory.long_term import remember_user_preference
from rag.report_retriever import retrieve_report_context
from workflow.graph import run_research
from workflow.sector_graph import run_sector_analysis


RouteType = Literal["stock_research", "sector_rotation", "report_rag_qa", "memory_update", "unknown"]


@dataclass
class RouteDecision:
    route: RouteType
    reason: str
    ts_code: str = ""
    company_name: str = ""
    period: str = "日"
    memory_content: str = ""


def _extract_stock_code(text: str) -> str:
    match = re.search(r"\b(\d{6})(?:\.(SH|SZ|BJ))?\b", text, flags=re.IGNORECASE)
    if not match:
        return ""
    code = match.group(1)
    exchange = match.group(2)
    if exchange:
        return f"{code}.{exchange.upper()}"
    if code.startswith("6"):
        return f"{code}.SH"
    return f"{code}.SZ"


def _extract_period(text: str) -> str:
    if any(word in text for word in ["本月", "月度", "月"]):
        return "月"
    if any(word in text for word in ["本周", "周度", "周"]):
        return "周"
    return "日"


def classify_intent(user_input: str) -> RouteDecision:
    """Rule-based planner/router for stable CLI and tests."""
    text = user_input.strip()
    lowered = text.lower()
    stock_code = _extract_stock_code(text)

    if any(word in text for word in ["记住", "我的持仓", "风险偏好", "我持有", "关注板块"]):
        content = re.sub(r"^(请)?记住[:：]?", "", text).strip()
        return RouteDecision("memory_update", "用户在更新持仓/偏好记忆", memory_content=content)

    if any(word in text for word in ["板块", "行业", "轮动", "强势", "弱势"]):
        return RouteDecision("sector_rotation", "用户询问行业板块轮动", period=_extract_period(text))

    if any(word in text for word in ["年报", "季报", "财报", "报告"]) and any(
        word in text for word in ["总结", "风险", "现金流", "毛利率", "营收", "利润", "问答"]
    ):
        return RouteDecision(
            "report_rag_qa",
            "用户询问财报内容",
            ts_code=stock_code,
            company_name="",
        )

    if stock_code or any(word in lowered for word in ["stock", "股票", "个股", "分析"]):
        return RouteDecision("stock_research", "用户请求个股研究", ts_code=stock_code)

    return RouteDecision("unknown", "无法稳定判断任务类型")


def run_agent_request(user_input: str, user_id: str = "default_user", company_name: str = "") -> str:
    """Route a natural-language request to the right research workflow."""
    decision = classify_intent(user_input)
    logger.info(f"[Router] route={decision.route}, reason={decision.reason}")

    if decision.route == "memory_update":
        return remember_user_preference(user_id, decision.memory_content or user_input)

    if decision.route == "sector_rotation":
        return run_sector_analysis(period=decision.period, user_id=user_id)

    if decision.route == "report_rag_qa":
        query = user_input
        context = retrieve_report_context(
            company_name=company_name,
            ts_code=decision.ts_code,
            query=query,
            k=5,
        )
        return f"任务类型: 财报问答\n路由原因: {decision.reason}\n\n{context}"

    if decision.route == "stock_research":
        if not decision.ts_code:
            return "无法识别股票代码，请输入如 600519.SH 或 600519 的 A 股代码。"
        return run_research(ts_code=decision.ts_code, user_id=user_id, company_name=company_name)

    return (
        "暂时无法判断任务类型。你可以尝试输入：\n"
        "- 分析 600519.SH\n"
        "- 今日哪些板块强？\n"
        "- 记住我持有半导体ETF，风险偏好中等\n"
        "- 总结贵州茅台年报的风险因素"
    )

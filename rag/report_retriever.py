import os
import re
from functools import lru_cache

from langchain_core.documents import Document
from loguru import logger

from config.settings import LLAMA_CLOUD_API_KEY, REPORTS_DIR


def _safe_name(value: str) -> str:
    return value.strip().replace("/", "_").replace("\\", "_")


def _candidate_report_dirs(company_name: str, ts_code: str) -> list[str]:
    """Return existing report directories, most specific first."""
    candidates = []
    for name in (company_name, ts_code, ts_code.split(".")[0] if ts_code else ""):
        clean = _safe_name(name)
        if clean:
            candidates.append(os.path.join(REPORTS_DIR, clean))

    existing = [path for path in candidates if os.path.isdir(path)]
    if os.path.isdir(REPORTS_DIR):
        existing.append(REPORTS_DIR)

    deduped = []
    seen = set()
    for path in existing:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def _has_pdf(path: str) -> bool:
    try:
        return any(fname.lower().endswith(".pdf") for fname in os.listdir(path))
    except OSError:
        return False


def extract_citations(context: str) -> str:
    """Extract compact citation lines from report RAG context."""
    citations = []
    for line in context.splitlines():
        match = re.match(r"\[(\d+)\]\s+来源:\s*(.+?),\s*页码/块:\s*(.+)", line.strip())
        if match:
            idx, source, page = match.groups()
            citations.append(f"[{idx}] {source} page/block {page}")
    return "\n".join(citations)


@lru_cache(maxsize=8)
def _load_docs_for_dir(report_dir: str) -> tuple[Document, ...]:
    from rag.loader import load_all_reports

    return tuple(load_all_reports(report_dir))


def retrieve_report_context(company_name: str, ts_code: str, query: str, k: int = 4) -> str:
    """
    Retrieve annual-report context for stock analysis.

    The function is intentionally fail-soft: missing PDFs, missing LlamaParse keys,
    or index failures should not block the main research workflow.
    """
    if not LLAMA_CLOUD_API_KEY:
        return "未配置 LLAMA_CLOUD_API_KEY，跳过财报 PDF RAG 检索。"

    report_dirs = [path for path in _candidate_report_dirs(company_name, ts_code) if _has_pdf(path)]
    if not report_dirs:
        return (
            "未找到可检索的财报 PDF。可将 PDF 放入 "
            f"{REPORTS_DIR}/{company_name or ts_code}/ 或 {REPORTS_DIR}/ 后启用财报 RAG。"
        )

    try:
        from rag.hybrid_search import HybridSearchEngine
        from rag.hyde import generate_hypothetical_doc

        docs = []
        for report_dir in report_dirs[:1]:
            docs.extend(_load_docs_for_dir(report_dir))
        if not docs:
            return "财报 PDF 解析后无可用文本，跳过财报 RAG。"

        enhanced_query = generate_hypothetical_doc(query)
        engine = HybridSearchEngine()
        engine.build_index(docs)
        results = engine.search(enhanced_query, k=k)
    except Exception as exc:
        logger.warning(f"财报 RAG 检索失败: {exc}")
        return f"财报 RAG 检索失败，已降级为结构化财务指标分析。原因: {exc}"

    if not results:
        return "财报 RAG 未检索到相关段落。"

    snippets = []
    for idx, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "N/A")
        content = doc.page_content.strip().replace("\n\n", "\n")
        snippets.append(f"[{idx}] 来源: {source}, 页码/块: {page}\n{content[:900]}")
    return "财报 RAG 检索结果:\n" + "\n\n".join(snippets)

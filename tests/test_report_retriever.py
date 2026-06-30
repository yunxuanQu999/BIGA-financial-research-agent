from rag import report_retriever


def test_retrieve_report_context_skips_when_llama_key_missing(monkeypatch):
    monkeypatch.setattr(report_retriever, "LLAMA_CLOUD_API_KEY", "")

    result = report_retriever.retrieve_report_context(
        company_name="贵州茅台",
        ts_code="600519.SH",
        query="盈利能力",
    )

    assert "跳过财报 PDF RAG 检索" in result


def test_candidate_report_dirs_prefers_company_and_code_dirs(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    company_dir = reports_dir / "贵州茅台"
    code_dir = reports_dir / "600519.SH"
    raw_code_dir = reports_dir / "600519"
    for path in (company_dir, code_dir, raw_code_dir):
        path.mkdir(parents=True)

    monkeypatch.setattr(report_retriever, "REPORTS_DIR", str(reports_dir))

    result = report_retriever._candidate_report_dirs("贵州茅台", "600519.SH")

    assert result[:3] == [str(company_dir), str(code_dir), str(raw_code_dir)]
    assert result[-1] == str(reports_dir)


def test_extract_citations_from_rag_context():
    context = """财报 RAG 检索结果:
[1] 来源: report-2024.pdf, 页码/块: 0
经营现金流改善

[2] 来源: report-2024.pdf, 页码/块: 3
风险因素说明
"""

    result = report_retriever.extract_citations(context)

    assert "[1] report-2024.pdf page/block 0" in result
    assert "[2] report-2024.pdf page/block 3" in result

from workflow import graph


def test_report_retriever_node_uses_company_and_code(monkeypatch):
    calls = {}

    def fake_retrieve_report_context(company_name, ts_code, query, k):
        calls["company_name"] = company_name
        calls["ts_code"] = ts_code
        calls["query"] = query
        calls["k"] = k
        return "财报 RAG 检索结果: 经营现金流改善"

    monkeypatch.setattr(graph, "retrieve_report_context", fake_retrieve_report_context)

    result = graph.report_retriever_node({
        "company_name": "贵州茅台",
        "ts_code": "600519.SH",
    })

    assert result["annual_report_context"] == "财报 RAG 检索结果: 经营现金流改善"
    assert calls["company_name"] == "贵州茅台"
    assert calls["ts_code"] == "600519.SH"
    assert "盈利能力" in calls["query"]
    assert calls["k"] == 4


def test_run_research_initial_state_contains_annual_report_context(monkeypatch):
    captured = {}

    class FakeApp:
        def invoke(self, state):
            captured.update(state)
            return {"final_report": "ok"}

    monkeypatch.setattr(graph, "get_research_app", lambda: FakeApp())

    assert graph.run_research("600519.SH", user_id="u1", company_name="贵州茅台") == "ok"
    assert captured["annual_report_context"] == ""
    assert captured["annual_report_citations"] == ""
    assert captured["review_result"] == {}


def test_parse_review_json():
    parsed = graph._parse_review_json(
        '{"report":"核心观点","needs_correction":false,"correction_reason":"","checks":{"risk_warning":"pass"}}'
    )

    assert parsed["report"] == "核心观点"
    assert parsed["needs_correction"] is False

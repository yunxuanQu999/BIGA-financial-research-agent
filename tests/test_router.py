from workflow.router import classify_intent


def test_classify_stock_research_with_code():
    decision = classify_intent("分析一下 600519.SH")

    assert decision.route == "stock_research"
    assert decision.ts_code == "600519.SH"


def test_classify_sector_rotation():
    decision = classify_intent("本周哪些板块强？")

    assert decision.route == "sector_rotation"
    assert decision.period == "周"


def test_classify_memory_update():
    decision = classify_intent("记住我持有半导体ETF，风险偏好中等")

    assert decision.route == "memory_update"
    assert "半导体ETF" in decision.memory_content


def test_classify_report_rag_qa():
    decision = classify_intent("总结 600519.SH 年报的风险因素")

    assert decision.route == "report_rag_qa"
    assert decision.ts_code == "600519.SH"

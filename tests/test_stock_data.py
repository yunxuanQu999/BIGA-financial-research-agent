from tools.stock_data import _normalize_code, _sina_code


def test_normalize_code_strips_exchange_suffix():
    assert _normalize_code("600519.SH") == "600519"
    assert _normalize_code("000001.SZ") == "000001"


def test_sina_code_uses_explicit_exchange():
    assert _sina_code("600519.SH") == "sh600519"
    assert _sina_code("000001.SZ") == "sz000001"


def test_sina_code_defaults_by_code_prefix():
    assert _sina_code("600000") == "sh600000"
    assert _sina_code("300750") == "sz300750"

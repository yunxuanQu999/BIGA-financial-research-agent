from tools import sector_data


def test_sector_avg_return_ignores_missing_values(monkeypatch):
    returns = {"白酒": 1.25, "饮料制造": None, "食品加工制造": 2.75}

    def fake_period_return(name, period):
        assert period == "日"
        return returns[name]

    monkeypatch.setattr(sector_data, "_ths_period_return", fake_period_return)

    assert sector_data._sector_avg_return(["白酒", "饮料制造", "食品加工制造"], "日") == 2.0


def test_sector_avg_return_returns_none_when_all_missing(monkeypatch):
    monkeypatch.setattr(sector_data, "_ths_period_return", lambda name, period: None)

    assert sector_data._sector_avg_return(["白酒", "饮料制造"], "周") is None

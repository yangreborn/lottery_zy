from crawler.spiders.td import TDSpider
from crawler.spiders.pl3 import PL3Spider


def test_3d_parse():
    raw = {"result": [{"code": "2026164", "date": "2026-06-23(二)", "red": "6,9,0"}]}
    items = TDSpider().parse(raw)
    assert len(items) == 1
    assert items[0]["issue"] == "2026164"
    assert items[0]["numbers"] == {"digits": [6, 9, 0]}


def test_3d_parse_skips_bad():
    assert TDSpider().parse({"result": [{"code": "x", "date": "2026-06-23", "red": "a,b"}]}) == []


def test_pl3_parse():
    raw = {"value": {"list": [
        {"lotteryDrawNum": "26164", "lotteryDrawTime": "2026-06-23", "lotteryDrawResult": "7 1 5"}]}}
    items = PL3Spider().parse(raw)
    assert len(items) == 1
    assert items[0]["issue"] == "26164"
    assert items[0]["numbers"] == {"digits": [7, 1, 5]}


def test_pl3_parse_skips_bad():
    assert PL3Spider().parse({"value": {"list": [
        {"lotteryDrawNum": "x", "lotteryDrawTime": "2026-06-23", "lotteryDrawResult": "a b"}]}}) == []

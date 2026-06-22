import json
from datetime import date
from pathlib import Path
from crawler.spiders.ssq import SsqSpider

FIXTURE = Path(__file__).parent / "fixtures" / "ssq_sample.json"


def test_parse_ssq():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    items = SsqSpider().parse(raw)
    assert len(items) == 1
    it = items[0]
    assert it["issue"] == "2026073"
    assert it["draw_date"] == date(2026, 6, 22)
    assert it["numbers"] == {"red": [1, 5, 12, 20, 28, 33], "blue": [8]}
    assert it["pool_amount"] == "1500000000"
    assert it["prize_grades"][0] == {"level": 1, "count": "5", "amount": "8000000"}


def test_parse_ssq_bad_record_skipped():
    """坏记录（red 含非数字）应被跳过，好记录正常解析，parse() 不抛异常。"""
    valid_record = json.loads(FIXTURE.read_text(encoding="utf-8"))["result"][0]
    raw = {
        "result": [
            # 坏记录：red 含非数字 token
            {
                "name": "双色球", "code": "BAD001", "date": "2026-06-22(日)",
                "red": "01,05,XX,20,28,33", "blue": "08",
                "sales": "100000000", "poolmoney": "500000000",
                "prizegrades": [],
            },
            # 好记录：直接复用 fixture
            valid_record,
        ]
    }
    items = SsqSpider().parse(raw)
    assert len(items) == 1
    assert items[0]["issue"] == "2026073"

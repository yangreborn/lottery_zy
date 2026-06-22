import json
from datetime import date
from pathlib import Path
from crawler.spiders.dlt import DltSpider

FIXTURE = Path(__file__).parent / "fixtures" / "dlt_sample.json"


def test_parse_dlt():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    items = DltSpider().parse(raw)
    assert len(items) == 1
    it = items[0]
    assert it["issue"] == "26073"
    assert it["draw_date"] == date(2026, 6, 22)
    assert it["numbers"] == {"red": [1, 5, 12, 20, 30], "blue": [3, 7]}
    assert it["pool_amount"] == "800000000"
    assert it["prize_grades"][0] == {"level": "一等奖", "count": "3", "amount": "10000000"}


def test_parse_dlt_bad_record_skipped():
    """坏记录（lotteryDrawResult 含非数字）应被跳过，好记录正常解析，parse() 不抛异常。"""
    valid_record = json.loads(FIXTURE.read_text(encoding="utf-8"))["value"]["list"][0]
    raw = {
        "value": {
            "list": [
                # 坏记录：lotteryDrawResult 含非数字 token
                {
                    "lotteryDrawNum": "BAD001",
                    "lotteryDrawResult": "01 05 XX 20 30 03 07",
                    "lotteryDrawTime": "2026-06-22",
                    "totalSaleAmount": "100000000",
                    "poolBalanceAfterdraw": "500000000",
                    "prizeLevelList": [],
                },
                # 好记录：直接复用 fixture
                valid_record,
            ]
        }
    }
    items = DltSpider().parse(raw)
    assert len(items) == 1
    assert items[0]["issue"] == "26073"

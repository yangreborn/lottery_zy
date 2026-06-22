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

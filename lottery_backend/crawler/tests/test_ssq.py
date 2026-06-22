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

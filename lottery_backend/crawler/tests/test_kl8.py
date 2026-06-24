from crawler.spiders.kl8 import KL8Spider


def test_kl8_parse():
    raw = {"result": [
        {"code": "2026100", "date": "2026-06-23(二)",
         "red": "01,05,09,12,18,22,25,30,33,38,41,44,50,55,60,66,70,73,77,80"},
    ]}
    items = KL8Spider().parse(raw)
    assert len(items) == 1
    it = items[0]
    assert it["issue"] == "2026100"
    assert it["numbers"]["main"][:3] == [1, 5, 9]
    assert len(it["numbers"]["main"]) == 20


def test_kl8_parse_skips_bad_record():
    raw = {"result": [{"code": "x", "date": "2026-06-23", "red": "not,num"}]}
    assert KL8Spider().parse(raw) == []

from crawler.spiders.base import BaseSpider


class _FakeSpider(BaseSpider):
    lottery_code = "fake"

    def __init__(self):
        self.got = None

    def fetch(self, count=1):
        self.got = count
        return {"x": count}

    def parse(self, raw):
        return [raw]


def test_run_passes_count_to_fetch():
    s = _FakeSpider()
    out = s.run(7)
    assert s.got == 7
    assert out == [{"x": 7}]


def test_run_default_count_1():
    s = _FakeSpider()
    s.run()
    assert s.got == 1

from crawler import schedule
from crawler.tasks import poll_lottery


class _FakeQueue:
    def __init__(self):
        self.calls = []

    def enqueue(self, func, *args, **kwargs):
        self.calls.append((func, args))


def test_dispatch_enqueues_due_codes(monkeypatch):
    fake = _FakeQueue()
    monkeypatch.setattr(schedule, "due_codes", lambda now: ["ssq", "3d"])
    import django_rq
    monkeypatch.setattr(django_rq, "get_queue", lambda name: fake)

    schedule.dispatch_due_polls()

    assert [(f, a[0]) for f, a in fake.calls] == [
        (poll_lottery, "ssq"),
        (poll_lottery, "3d"),
    ]


def test_dispatch_no_due_enqueues_nothing(monkeypatch):
    fake = _FakeQueue()
    monkeypatch.setattr(schedule, "due_codes", lambda now: [])
    import django_rq
    monkeypatch.setattr(django_rq, "get_queue", lambda name: fake)

    schedule.dispatch_due_polls()

    assert fake.calls == []

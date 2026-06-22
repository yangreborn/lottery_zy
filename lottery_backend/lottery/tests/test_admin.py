import pytest
from datetime import date
from django.contrib.admin.sites import site
from lottery.models import Lottery, DrawResult
from lottery.admin import DrawResultAdmin


@pytest.mark.django_db
def test_models_registered():
    assert Lottery in site._registry
    assert DrawResult in site._registry


@pytest.mark.django_db
def test_publish_action_sets_status():
    lot = Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                 rule_config={}, draw_days=[])
    d = DrawResult.objects.create(lottery=lot, issue="2026073",
                                  draw_date=date(2026, 6, 22), numbers={},
                                  status=DrawResult.STATUS_DRAFT)
    admin = DrawResultAdmin(DrawResult, site)
    admin.publish_selected(request=None, queryset=DrawResult.objects.filter(pk=d.pk))
    d.refresh_from_db()
    assert d.status == DrawResult.STATUS_PUBLISHED

import pytest
from guide.models import PlayGuide


def test_create_defaults(db):
    g = PlayGuide.objects.create(title="双色球玩法", type=PlayGuide.TYPE_INTRO)
    assert g.lottery is None
    assert g.is_active is True
    assert g.sort == 0
    assert g.publish_at is None
    assert g.content == ""


def test_type_constants():
    assert PlayGuide.TYPE_INTRO == "intro"
    assert PlayGuide.TYPE_RULE == "rule"
    assert PlayGuide.TYPE_ACTIVITY == "activity"

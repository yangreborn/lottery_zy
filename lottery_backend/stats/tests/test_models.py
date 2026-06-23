import pytest
from stats.models import AccessLog


def test_create_defaults(db):
    log = AccessLog.objects.create(path="draw/latest")
    assert log.user_id == ""
    assert log.lottery_code == ""
    assert log.action == "view"
    assert log.created_at is not None


def test_action_constants():
    assert AccessLog.ACTION_VIEW == "view"
    assert AccessLog.ACTION_SAVE == "save_number"
    assert AccessLog.ACTION_CHECK == "check_number"

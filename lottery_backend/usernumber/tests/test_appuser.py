import pytest
from usernumber.models import AppUser, get_or_create_app_user


@pytest.mark.django_db
def test_get_or_create_app_user_idempotent():
    u1 = get_or_create_app_user("hash123", "openid-abc")
    u2 = get_or_create_app_user("hash123", "openid-abc")
    assert u1.id == u2.id
    assert AppUser.objects.count() == 1
    assert u1.openid == "openid-abc"


@pytest.mark.django_db
def test_appuser_unionid_default_blank():
    u = get_or_create_app_user("hashu", "openidu")
    assert u.unionid == ""


@pytest.mark.django_db
def test_short_id_and_str():
    u = get_or_create_app_user("abcdef0123456789", "openid-x")
    u.nickname = "小明"
    u.save()
    assert u.short_id == "abcdef01"
    assert str(u) == f"#{u.id} 小明"

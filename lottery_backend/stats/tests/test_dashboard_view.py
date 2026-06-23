import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


def test_dashboard_staff_200(db):
    User.objects.create_superuser("admin", "a@a.com", "pw")
    c = APIClient()
    c.login(username="admin", password="pw")
    resp = c.get("/dashboard/")
    assert resp.status_code == 200
    assert "运营看板" in resp.content.decode()


def test_dashboard_non_staff_redirect(db):
    resp = APIClient().get("/dashboard/")
    assert resp.status_code == 302

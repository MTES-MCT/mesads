from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.test import RequestFactory

from mesads.users.models import UserAuditEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def request_with_ip():
    return RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4, 10.0.0.1")


def test_login_creates_audit_entry(user_factory, request_with_ip):
    user = user_factory()

    user_logged_in.send(sender=user.__class__, request=request_with_ip, user=user)

    entry = UserAuditEntry.objects.get(user=user)
    assert entry.action == "login"
    assert entry.ip == "1.2.3.4"


def test_login_resets_delete_notification(user_factory, request_with_ip):
    user = user_factory(
        delete_notification_sent_at=datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
    )

    user_logged_in.send(sender=user.__class__, request=request_with_ip, user=user)

    user.refresh_from_db()
    assert user.delete_notification_sent_at is None


def test_logout_creates_audit_entry(user_factory, request_with_ip):
    user = user_factory()

    user_logged_out.send(sender=user.__class__, request=request_with_ip, user=user)

    entry = UserAuditEntry.objects.get(user=user)
    assert entry.action == "logout"
    assert entry.ip == "1.2.3.4"

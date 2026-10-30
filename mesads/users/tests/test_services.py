from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

import mesads.users.services as services
from mesads.app.models import ADSUpdateFile, ADSUpdateLog
from mesads.app.tests.factories import ADSFactory
from mesads.users.services import delete_old_users, notify_old_users
from mesads.users.tests.factories import (
    UserFactory,
)

from ..models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def now(monkeypatch):
    now = datetime(2026, 10, 28, 12, 0, tzinfo=dt_timezone.utc)
    monkeypatch.setattr(services.timezone, "now", lambda: now)
    return now


def test_delete_user_inactive_for_more_than_two_years():
    user = UserFactory(last_login=timezone.now() - relativedelta(years=3))

    deleted_count = delete_old_users()

    assert deleted_count == 1
    assert not user.__class__.objects.filter(pk=user.pk).exists()


def test_delete_user_inactive_for_exactly_two_years(now):
    user = UserFactory(last_login=now - relativedelta(years=2))

    deleted_count = delete_old_users()

    assert deleted_count == 1
    assert not User.objects.filter(pk=user.pk).exists()


def test_delete_user_without_last_login():
    user = UserFactory(last_login=None)

    deleted_count = delete_old_users()

    assert deleted_count == 1
    assert not User.objects.filter(pk=user.pk).exists()


def test_keep_recently_active_user():
    user = UserFactory(last_login=timezone.now() - relativedelta(years=1))

    deleted_count = delete_old_users()

    assert deleted_count == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_user_just_before_two_year_threshold(now):
    user = UserFactory(last_login=now - relativedelta(years=2) + timedelta(seconds=1))

    deleted_count = delete_old_users()

    assert deleted_count == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_inactive_user_with_ads_update_log():
    user = UserFactory(last_login=timezone.now() - relativedelta(years=3))
    ADSUpdateLog.objects.create(ads=ADSFactory(), user=user)

    deleted_count = delete_old_users()

    assert deleted_count == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_inactive_user_with_ads_update_file():
    user = UserFactory(last_login=timezone.now() - relativedelta(years=3))
    ADSUpdateFile.objects.create(user=user)

    deleted_count = delete_old_users()

    assert deleted_count == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_inactive_user_with_both_activities():
    user = UserFactory(last_login=timezone.now() - relativedelta(years=3))
    ADSUpdateLog.objects.create(ads=ADSFactory(), user=user)
    ADSUpdateFile.objects.create(user=user)

    deleted_count = delete_old_users()

    assert deleted_count == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_delete_only_eligible_users():
    old_user = UserFactory(last_login=timezone.now() - relativedelta(years=3))
    never_connected_user = UserFactory(last_login=None)
    recent_user = UserFactory(last_login=timezone.now() - relativedelta(months=6))
    user_with_log = UserFactory(last_login=timezone.now() - relativedelta(years=3))
    user_with_file = UserFactory(last_login=timezone.now() - relativedelta(years=3))
    ADSUpdateLog.objects.create(ads=ADSFactory(), user=user_with_log)
    ADSUpdateFile.objects.create(user=user_with_file)

    deleted_count = delete_old_users()

    assert deleted_count == 2

    assert not User.objects.filter(pk=old_user.pk).exists()
    assert not User.objects.filter(pk=never_connected_user.pk).exists()

    assert User.objects.filter(pk=recent_user.pk).exists()
    assert User.objects.filter(pk=user_with_log.pk).exists()
    assert User.objects.filter(pk=user_with_file.pk).exists()


def test_no_users_to_delete():
    deleted_count = delete_old_users()
    assert deleted_count == 0


def test_notify_user_approaching_two_years(now):
    user = UserFactory(last_login=now - relativedelta(years=2) + timedelta(days=15))

    notified_count = notify_old_users()

    assert notified_count == 1

    user.refresh_from_db()
    assert user.delete_notification_sent is True


def test_dont_notify_recently_active_user(now):
    UserFactory(last_login=now - relativedelta(years=1))

    notified_count = notify_old_users()

    assert notified_count == 0


def test_dont_notify_user_inactive_for_more_than_two_years(now):
    UserFactory(last_login=now - relativedelta(years=3))

    notified_count = notify_old_users()

    assert notified_count == 0


def test_dont_notify_user_already_notified(now):
    UserFactory(
        last_login=now - relativedelta(years=2) + timedelta(days=15),
        delete_notification_sent=True,
    )

    notified_count = notify_old_users()

    assert notified_count == 0


def test_dont_notify_user_with_ads_update_log(now):
    user = UserFactory(last_login=now - relativedelta(years=2) + timedelta(days=15))
    ADSUpdateLog.objects.create(ads=ADSFactory(), user=user)

    notified_count = notify_old_users()

    assert notified_count == 0


def test_dont_notify_user_with_ads_update_file(now):
    user = UserFactory(last_login=now - relativedelta(years=2) + timedelta(days=15))
    ADSUpdateFile.objects.create(user=user)

    notified_count = notify_old_users()

    assert notified_count == 0


def test_dont_notify_user_without_last_login():
    UserFactory(last_login=None)

    notified_count = notify_old_users()

    assert notified_count == 0


def test_notify_multiple_eligible_users(now):
    UserFactory.create_batch(
        3,
        last_login=now - relativedelta(years=2) + timedelta(days=15),
    )

    notified_count = notify_old_users()

    assert notified_count == 3

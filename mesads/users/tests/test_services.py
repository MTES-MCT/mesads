from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest
from dateutil.relativedelta import relativedelta

import mesads.users.services as services
from mesads.app.models import ADSUpdateFile
from mesads.app.tests.factories import ADSManagerRequestFactory
from mesads.users.tests.factories import UserFactory

from ..models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def now(monkeypatch):
    now = datetime(2026, 10, 28, 12, 0, tzinfo=dt_timezone.utc)
    monkeypatch.setattr(services.timezone, "now", lambda: now)
    return now


@pytest.fixture
def sent_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(services, "envoi_email", lambda **kwargs: sent.append(kwargs))
    return sent


def user_with_permission(**kwargs):
    user = UserFactory(**kwargs)
    ADSManagerRequestFactory(user=user, accepted=True)
    return user


# ---------------------------------------------------------------------------
# delete_old_users — utilisateurs sans permission
# ---------------------------------------------------------------------------


def test_delete_user_inactive_for_more_than_two_years(now):
    user = UserFactory(last_login=now - relativedelta(years=3))

    assert services.delete_old_users() == 1
    assert not User.objects.filter(pk=user.pk).exists()


def test_delete_user_inactive_for_exactly_two_years(now):
    user = UserFactory(last_login=now - relativedelta(years=2))

    assert services.delete_old_users() == 1
    assert not User.objects.filter(pk=user.pk).exists()


def test_delete_user_never_logged_in_joined_more_than_two_years_ago(now):
    user = UserFactory(last_login=None, date_joined=now - relativedelta(years=3))

    assert services.delete_old_users() == 1
    assert not User.objects.filter(pk=user.pk).exists()


def test_keep_user_never_logged_in_joined_recently(now):
    user = UserFactory(last_login=None, date_joined=now - relativedelta(months=6))

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_recently_active_user(now):
    user = UserFactory(last_login=now - relativedelta(years=1))

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_user_just_before_two_year_threshold(now):
    user = UserFactory(last_login=now - relativedelta(years=2) + timedelta(seconds=1))

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_inactive_user_with_ads_update_file(now):
    user = UserFactory(last_login=now - relativedelta(years=3))
    ADSUpdateFile.objects.create(user=user)

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_delete_only_eligible_users(now):
    old_user = UserFactory(last_login=now - relativedelta(years=3))
    never_connected_user = UserFactory(
        last_login=None, date_joined=now - relativedelta(years=3)
    )
    recent_user = UserFactory(last_login=now - relativedelta(months=6))
    user_with_file = UserFactory(last_login=now - relativedelta(years=3))
    ADSUpdateFile.objects.create(user=user_with_file)

    assert services.delete_old_users() == 2

    assert not User.objects.filter(pk=old_user.pk).exists()
    assert not User.objects.filter(pk=never_connected_user.pk).exists()
    assert User.objects.filter(pk=recent_user.pk).exists()
    assert User.objects.filter(pk=user_with_file.pk).exists()


def test_no_users_to_delete(now):
    assert services.delete_old_users() == 0


# ---------------------------------------------------------------------------
# delete_old_users — utilisateurs avec permission
# ---------------------------------------------------------------------------


def test_keep_inactive_user_with_permission_not_notified(now):
    user = user_with_permission(last_login=now - relativedelta(years=3))

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.parametrize(
    "user_kwargs",
    [{"is_staff": True}, {"is_superuser": True}],
)
def test_keep_inactive_staff_not_notified(now, user_kwargs):
    user = UserFactory(last_login=now - relativedelta(years=3), **user_kwargs)

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_keep_inactive_user_with_permission_notified_less_than_a_month_ago(now):
    user = user_with_permission(
        last_login=now - relativedelta(years=3),
        delete_notification_sent_at=now - relativedelta(days=15),
    )

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


def test_delete_inactive_user_with_permission_notified_a_month_ago(now):
    user = user_with_permission(
        last_login=now - relativedelta(years=3),
        delete_notification_sent_at=now - relativedelta(months=1),
    )

    assert services.delete_old_users() == 1
    assert not User.objects.filter(pk=user.pk).exists()


def test_keep_notified_user_with_permission_not_yet_inactive_for_two_years(now):
    user = user_with_permission(
        last_login=now - relativedelta(years=2) + timedelta(days=1),
        delete_notification_sent_at=now - relativedelta(months=2),
    )

    assert services.delete_old_users() == 0
    assert User.objects.filter(pk=user.pk).exists()


# ---------------------------------------------------------------------------
# notify_old_users
# ---------------------------------------------------------------------------


def test_notify_user_approaching_two_years(now, sent_emails):
    last_login = now - relativedelta(years=2) + timedelta(days=15)
    user = user_with_permission(last_login=last_login)

    assert services.notify_old_users() == 1

    user.refresh_from_db()
    assert user.delete_notification_sent_at == now
    assert len(sent_emails) == 1
    assert sent_emails[0]["destinataires"] == [user.email]
    # La suppression ne peut pas avoir lieu moins d'un mois après la notification
    assert sent_emails[0]["context"]["deletion_date"] == now + relativedelta(months=1)


def test_notify_user_exactly_one_month_before_deletion(now, sent_emails):
    last_login = now - relativedelta(years=2) + relativedelta(months=1)
    user_with_permission(last_login=last_login)

    assert services.notify_old_users() == 1
    assert sent_emails[0]["context"]["deletion_date"] == last_login + relativedelta(
        years=2
    )


def test_notify_user_already_inactive_for_more_than_two_years(now, sent_emails):
    user = user_with_permission(last_login=now - relativedelta(years=3))

    assert services.notify_old_users() == 1

    user.refresh_from_db()
    assert user.delete_notification_sent_at == now
    assert sent_emails[0]["context"]["deletion_date"] == now + relativedelta(months=1)


def test_notify_user_never_logged_in(now, sent_emails):
    user_with_permission(last_login=None, date_joined=now - relativedelta(years=3))

    assert services.notify_old_users() == 1


def test_dont_notify_user_without_permission(now, sent_emails):
    user = UserFactory(last_login=now - relativedelta(years=2) + timedelta(days=15))

    assert services.notify_old_users() == 0

    user.refresh_from_db()
    assert user.delete_notification_sent_at is None
    assert sent_emails == []


def test_dont_notify_recently_active_user(now, sent_emails):
    user_with_permission(last_login=now - relativedelta(years=1))

    assert services.notify_old_users() == 0


def test_dont_notify_user_already_notified(now, sent_emails):
    user_with_permission(
        last_login=now - relativedelta(years=2) + timedelta(days=15),
        delete_notification_sent_at=now - relativedelta(days=7),
    )

    assert services.notify_old_users() == 0
    assert sent_emails == []


def test_dont_notify_user_with_ads_update_file(now, sent_emails):
    user = user_with_permission(
        last_login=now - relativedelta(years=2) + timedelta(days=15)
    )
    ADSUpdateFile.objects.create(user=user)

    assert services.notify_old_users() == 0


def test_dont_notify_user_never_logged_in_joined_recently(now, sent_emails):
    user_with_permission(last_login=None, date_joined=now - relativedelta(months=6))

    assert services.notify_old_users() == 0


def test_notify_multiple_eligible_users(now, sent_emails):
    for _ in range(3):
        user_with_permission(
            last_login=now - relativedelta(years=2) + timedelta(days=15)
        )

    assert services.notify_old_users() == 3


def test_notify_respects_limit(now, sent_emails):
    for _ in range(5):
        user_with_permission(
            last_login=now - relativedelta(years=2) + timedelta(days=15)
        )

    assert services.notify_old_users(limit=3) == 3
    assert User.objects.filter(delete_notification_sent_at__isnull=False).count() == 3

    # Le passage suivant traite les utilisateurs restants
    assert services.notify_old_users(limit=3) == 2
    assert services.notify_old_users(limit=3) == 0
    assert len(sent_emails) == 5


def test_notify_oldest_inactive_users_first(now, sent_emails):
    recent = user_with_permission(
        last_login=now - relativedelta(years=2) + timedelta(days=15)
    )
    never_logged = user_with_permission(
        last_login=None, date_joined=now - relativedelta(years=4)
    )
    oldest_login = user_with_permission(last_login=now - relativedelta(years=3))

    assert services.notify_old_users(limit=2) == 2
    assert [email["destinataires"] for email in sent_emails] == [
        [never_logged.email],
        [oldest_login.email],
    ]

    recent.refresh_from_db()
    assert recent.delete_notification_sent_at is None


@pytest.mark.parametrize(
    "notified_count, expected",
    [
        (12, "12 utilisateurs notifiés"),
        (
            services.NOTIFICATION_BATCH_SIZE,
            f"{services.NOTIFICATION_BATCH_SIZE} utilisateurs notifiés (limite de "
            f"{services.NOTIFICATION_BATCH_SIZE} atteinte, la suite sera traitée au "
            "prochain passage)",
        ),
    ],
)
def test_notify_old_users_cron_message(monkeypatch, notified_count, expected):
    from mesads.app import crons

    monkeypatch.setattr(crons, "notify_old_users", lambda: notified_count)

    assert crons.NotifyOldUsers().do() == expected


def test_notify_continues_when_an_email_fails(now, monkeypatch):
    users = [
        user_with_permission(
            last_login=now - relativedelta(years=2) + timedelta(days=15)
        )
        for _ in range(2)
    ]
    failing_email = users[0].email

    def fake_envoi_email(**kwargs):
        if kwargs["destinataires"] == [failing_email]:
            raise RuntimeError("SMTP down")

    captured = []
    monkeypatch.setattr(services, "envoi_email", fake_envoi_email)
    monkeypatch.setattr(services, "capture_exception", captured.append)

    assert services.notify_old_users() == 1
    assert len(captured) == 1
    assert isinstance(captured[0], RuntimeError)

    users[0].refresh_from_db()
    users[1].refresh_from_db()
    assert users[0].delete_notification_sent_at is None
    assert users[1].delete_notification_sent_at == now


# ---------------------------------------------------------------------------
# Réinitialisation à la connexion
# ---------------------------------------------------------------------------


def test_login_resets_delete_notification(client, now):
    user = user_with_permission(
        last_login=now - relativedelta(years=2),
        delete_notification_sent_at=now - relativedelta(days=7),
    )

    client.force_login(user)

    user.refresh_from_db()
    assert user.delete_notification_sent_at is None


# ---------------------------------------------------------------------------
# Nombre de requêtes
# ---------------------------------------------------------------------------


def _count_queries(func):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as ctx:
        func()
    return len(ctx.captured_queries)


def test_delete_old_users_query_count_does_not_depend_on_user_count(now):
    def create_users(n):
        for _ in range(n):
            UserFactory(last_login=now - relativedelta(years=3))
            user_with_permission(last_login=now - relativedelta(years=3))

    create_users(1)
    queries_for_one = _count_queries(services.delete_old_users)

    create_users(5)
    queries_for_five = _count_queries(services.delete_old_users)

    assert queries_for_one == queries_for_five

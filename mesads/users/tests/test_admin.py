import pytest
from django.urls import reverse

from mesads.users.models import PermissionAuditEntry, UserAuditEntry


@pytest.fixture
def admin_client(user_factory, client_factory):
    admin = user_factory(email="admin@example.com", is_staff=True, is_superuser=True)
    client = client_factory(admin)
    session = client.session
    session["admin_mfa"] = {"user_id": str(admin.pk), "acr": "eidas1-mfa"}
    session.save()
    return client


def get_form_data(user, **overrides):
    data = {
        "email": user.email,
        "is_active": "on",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_admin_allows_proconnect_link_on_legacy_user(admin_client, user_factory):
    legacy_user = user_factory(email="legacy@example.com", proconnect_sub=None)
    url = reverse("admin:users_user_change", args=[legacy_user.pk])

    response = admin_client.post(
        url, get_form_data(legacy_user, proconnect_link_allowed="on")
    )

    assert response.status_code == 302
    legacy_user.refresh_from_db()
    assert legacy_user.proconnect_link_allowed is True

    entry = PermissionAuditEntry.objects.get(target_user=legacy_user)
    assert entry.action == PermissionAuditEntry.Action.PROCONNECT_LINK_ALLOWED
    assert entry.actor.email == "admin@example.com"
    assert not UserAuditEntry.objects.filter(user=legacy_user).exists()


@pytest.mark.django_db
def test_admin_revokes_proconnect_link(admin_client, user_factory):
    legacy_user = user_factory(proconnect_sub=None, proconnect_link_allowed=True)
    url = reverse("admin:users_user_change", args=[legacy_user.pk])

    response = admin_client.post(url, get_form_data(legacy_user))

    assert response.status_code == 302
    legacy_user.refresh_from_db()
    assert legacy_user.proconnect_link_allowed is False
    entry = PermissionAuditEntry.objects.get(target_user=legacy_user)
    assert entry.action == PermissionAuditEntry.Action.PROCONNECT_LINK_REVOKED
    assert entry.actor.email == "admin@example.com"


@pytest.mark.django_db
def test_admin_proconnect_link_readonly_when_already_linked(admin_client, user_factory):
    linked_user = user_factory(proconnect_sub="11111111-1111-4111-8111-111111111111")
    url = reverse("admin:users_user_change", args=[linked_user.pk])

    response = admin_client.post(
        url, get_form_data(linked_user, proconnect_link_allowed="on")
    )

    assert response.status_code == 302
    linked_user.refresh_from_db()
    assert linked_user.proconnect_link_allowed is False
    assert not PermissionAuditEntry.objects.filter(target_user=linked_user).exists()


@pytest.mark.django_db
def test_admin_save_without_change_does_not_log(admin_client, user_factory):
    legacy_user = user_factory(proconnect_sub=None)
    url = reverse("admin:users_user_change", args=[legacy_user.pk])

    response = admin_client.post(url, get_form_data(legacy_user))

    assert response.status_code == 302
    assert not PermissionAuditEntry.objects.filter(target_user=legacy_user).exists()


@pytest.mark.django_db
def test_admin_permission_audit_entries_are_read_only(admin_client, user_factory):
    target = user_factory()
    entry = PermissionAuditEntry.objects.create(
        action=PermissionAuditEntry.Action.PROCONNECT_LINKED, target_user=target
    )

    changelist = admin_client.get(
        reverse("admin:users_permissionauditentry_changelist")
        + f"?target_user__id__exact={target.pk}"
    )
    assert changelist.status_code == 200

    detail_url = reverse("admin:users_permissionauditentry_change", args=[entry.pk])
    assert admin_client.get(detail_url).status_code == 200
    admin_client.post(detail_url, {"action": "proconnect_link_allowed"})
    entry.refresh_from_db()
    assert entry.action == PermissionAuditEntry.Action.PROCONNECT_LINKED

    delete_url = reverse("admin:users_permissionauditentry_delete", args=[entry.pk])
    assert admin_client.post(delete_url, {"post": "yes"}).status_code == 403
    assert PermissionAuditEntry.objects.filter(pk=entry.pk).exists()


@pytest.mark.django_db
def test_admin_user_change_page_links_permission_audit_entries(
    admin_client, user_factory
):
    target = user_factory()

    response = admin_client.get(reverse("admin:users_user_change", args=[target.pk]))

    assert response.status_code == 200
    assert f"?target_user__id__exact={target.pk}".encode() in response.content


@pytest.fixture
def dated_audit_entries(user_factory):
    from datetime import datetime
    from datetime import timezone as dt_timezone

    user = user_factory()
    entries = {}
    for day in (1, 10, 20):
        entry = UserAuditEntry.objects.create(user=user, action="login")
        UserAuditEntry.objects.filter(pk=entry.pk).update(
            created_at=datetime(2026, 3, day, 12, 0, tzinfo=dt_timezone.utc)
        )
        entries[day] = entry
    return user, entries


def audit_changelist_pks(admin_client, user, **params):
    response = admin_client.get(
        reverse("admin:users_userauditentry_changelist"),
        {"user__id__exact": user.pk, **params},
    )
    assert response.status_code == 200
    return response, {entry.pk for entry in response.context["cl"].result_list}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("params", "expected_days"),
    [
        ({}, {1, 10, 20}),
        ({"created_at__gte": "2026-03-10"}, {10, 20}),
        ({"created_at__lte": "2026-03-10"}, {1, 10}),
        ({"created_at__gte": "2026-03-02", "created_at__lte": "2026-03-19"}, {10}),
        ({"created_at__gte": "2026-03-10", "created_at__lte": "2026-03-10"}, {10}),
        ({"created_at__gte": "", "created_at__lte": ""}, {1, 10, 20}),
    ],
)
def test_user_audit_entry_admin_date_range_filter(
    admin_client, dated_audit_entries, params, expected_days
):
    user, entries = dated_audit_entries

    _, pks = audit_changelist_pks(admin_client, user, **params)

    assert pks == {entries[day].pk for day in expected_days}


@pytest.mark.django_db
def test_user_audit_entry_admin_date_range_filter_keeps_other_params(
    admin_client, dated_audit_entries
):
    user, _ = dated_audit_entries

    response, _ = audit_changelist_pks(
        admin_client, user, action="login", created_at__gte="2026-03-10"
    )

    content = response.content.decode()
    assert 'name="created_at__gte" value="2026-03-10"' in content
    assert f'name="user__id__exact" value="{user.pk}"' in content
    assert 'name="action" value="login"' in content
    assert "Réinitialiser" in content


@pytest.mark.django_db
def test_user_audit_entry_admin_date_range_filter_invalid_date(
    admin_client, dated_audit_entries
):
    user, _ = dated_audit_entries

    response = admin_client.get(
        reverse("admin:users_userauditentry_changelist"),
        {"user__id__exact": user.pk, "created_at__gte": "pas-une-date"},
    )

    # L'admin Django redirige vers la liste avec le paramètre d'erreur `e=1`.
    assert response.status_code == 302
    assert "e=1" in response.url


@pytest.mark.django_db
@pytest.mark.parametrize("mfa_user", ["none", "other"])
def test_admin_requires_mfa(user_factory, client_factory, mfa_user):
    admin = user_factory(is_staff=True, is_superuser=True)
    client = client_factory(admin)

    if mfa_user == "other":
        session = client.session
        session["admin_mfa"] = {"user_id": str(admin.pk + 1), "acr": "eidas1-mfa"}
        session.save()

    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))

    response = client.get(response.url)
    assert response.status_code == 302
    assert response.url.startswith(reverse("oidc_admin_authenticate"))


@pytest.mark.django_db
def test_admin_login_with_mfa_redirects_to_next(admin_client):
    response = admin_client.get(reverse("admin:login"), {"next": "/admin/users/"})

    assert response.status_code == 302
    assert response.url == "/admin/users/"


@pytest.mark.django_db
def test_admin_login_with_mfa_non_staff_denied(user_factory, client_factory):
    user = user_factory(is_staff=False)
    client = client_factory(user)
    session = client.session
    session["admin_mfa"] = {"user_id": str(user.pk), "acr": "eidas1-mfa"}
    session.save()

    assert client.get(reverse("admin:login")).status_code == 403

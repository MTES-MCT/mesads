import pytest
from django.urls import reverse

from mesads.users.models import PermissionAuditEntry, UserAuditEntry


@pytest.fixture
def admin_client(user_factory, client_factory):
    admin = user_factory(email="admin@example.com", is_staff=True, is_superuser=True)
    return client_factory(admin)


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

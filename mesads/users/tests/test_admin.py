import pytest
from django.urls import reverse

from mesads.users.models import UserAuditEntry


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

    entry = UserAuditEntry.objects.get(user=legacy_user)
    assert entry.action == "proconnect_link_allowed"
    assert "autorisé par admin@example.com" in entry.body


@pytest.mark.django_db
def test_admin_revokes_proconnect_link(admin_client, user_factory):
    legacy_user = user_factory(proconnect_sub=None, proconnect_link_allowed=True)
    url = reverse("admin:users_user_change", args=[legacy_user.pk])

    response = admin_client.post(url, get_form_data(legacy_user))

    assert response.status_code == 302
    legacy_user.refresh_from_db()
    assert legacy_user.proconnect_link_allowed is False
    assert "révoqué" in UserAuditEntry.objects.get(user=legacy_user).body


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
    assert not UserAuditEntry.objects.filter(user=linked_user).exists()


@pytest.mark.django_db
def test_admin_save_without_change_does_not_log(admin_client, user_factory):
    legacy_user = user_factory(proconnect_sub=None)
    url = reverse("admin:users_user_change", args=[legacy_user.pk])

    response = admin_client.post(url, get_form_data(legacy_user))

    assert response.status_code == 302
    assert not UserAuditEntry.objects.filter(user=legacy_user).exists()

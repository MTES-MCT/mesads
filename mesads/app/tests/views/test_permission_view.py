import pytest
from django.conf import settings
from django.core import mail
from django.urls import reverse

from mesads.app.models import DemandeGestionPrefecture
from mesads.users.tests.factories import UserFactory

from ..factories import (
    ADSManagerAdministratorFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "statut, is_owner, expected",
    [
        (DemandeGestionPrefecture.ACCEPTE, True, True),
        (DemandeGestionPrefecture.EXPIRE, True, True),
        (DemandeGestionPrefecture.EN_ATTENTE, True, False),
        (DemandeGestionPrefecture.REFUSE, True, False),
        (DemandeGestionPrefecture.ACCEPTE, False, False),
        (DemandeGestionPrefecture.EXPIRE, False, False),
        (DemandeGestionPrefecture.EN_ATTENTE, False, False),
        (DemandeGestionPrefecture.REFUSE, False, False),
    ],
)
def test_permissions_user_list_view(client_factory, statut, is_owner, expected):
    user = UserFactory()
    other_user = UserFactory()
    administrator = ADSManagerAdministratorFactory()

    demande = DemandeGestionPrefecture.objects.create(
        administrator=administrator,
        user=user if is_owner else other_user,
        statut=statut,
    )

    client = client_factory(user)

    response = client.get(reverse("app.mes_acces"))

    assert response.status_code == 200

    permissions = response.context["permissions_prefecture"]

    assert (demande in permissions) == expected


def test_permissions_user_list_view_multiple(client_factory):
    user = UserFactory()
    other_user = UserFactory()
    administrator_1 = ADSManagerAdministratorFactory()
    administrator_2 = ADSManagerAdministratorFactory()
    administrator_3 = ADSManagerAdministratorFactory()
    administrator_4 = ADSManagerAdministratorFactory()

    accepted = DemandeGestionPrefecture.objects.create(
        administrator=administrator_1,
        user=user,
        statut=DemandeGestionPrefecture.ACCEPTE,
    )

    expired = DemandeGestionPrefecture.objects.create(
        administrator=administrator_2,
        user=user,
        statut=DemandeGestionPrefecture.EXPIRE,
    )

    DemandeGestionPrefecture.objects.create(
        administrator=administrator_3,
        user=user,
        statut=DemandeGestionPrefecture.EN_ATTENTE,
    )

    DemandeGestionPrefecture.objects.create(
        administrator=administrator_4,
        user=other_user,
        statut=DemandeGestionPrefecture.ACCEPTE,
    )

    client = client_factory(user)

    response = client.get(reverse("app.mes_acces"))

    assert response.status_code == 200

    permissions = response.context["permissions_prefecture"]

    assert set(permissions) == {accepted, expired}


@pytest.mark.parametrize(
    "statut, expected_status, expected_email_count",
    [
        (DemandeGestionPrefecture.ACCEPTE, 302, 1),
        (DemandeGestionPrefecture.EXPIRE, 302, 1),
        (DemandeGestionPrefecture.EN_ATTENTE, 404, 0),
        (DemandeGestionPrefecture.REFUSE, 404, 0),
    ],
)
def test_renouvellement_demande_gestion_prefecture(
    client_factory,
    statut,
    expected_status,
    expected_email_count,
):
    user = UserFactory()
    administrator = ADSManagerAdministratorFactory()

    demande = DemandeGestionPrefecture.objects.create(
        administrator=administrator,
        user=user,
        statut=statut,
    )

    client = client_factory(user)

    response = client.post(
        reverse(
            "app.ads-manager-admin.renouvellement_demande_gestion",
            kwargs={"prefecture_id": demande.administrator.prefecture.id},
        )
    )

    assert response.status_code == expected_status

    demande.refresh_from_db()

    assert demande.demande_renouvellement == (expected_status == 302)
    assert len(mail.outbox) == expected_email_count

    if expected_status == 302:
        assert response.url == reverse("app.mes_acces")
        assert mail.outbox[0].to == [settings.MESADS_CONTACT_EMAIL]


def test_renouvellement_demande_other_user(client_factory):
    user = UserFactory()
    other_user = UserFactory()
    administrator = ADSManagerAdministratorFactory()

    demande = DemandeGestionPrefecture.objects.create(
        administrator=administrator,
        user=other_user,
        statut=DemandeGestionPrefecture.ACCEPTE,
    )

    client = client_factory(user)

    response = client.post(
        reverse(
            "app.ads-manager-admin.renouvellement_demande_gestion",
            kwargs={"prefecture_id": demande.administrator.prefecture.id},
        )
    )

    assert response.status_code == 404

    demande.refresh_from_db()

    assert not demande.demande_renouvellement
    assert len(mail.outbox) == 0

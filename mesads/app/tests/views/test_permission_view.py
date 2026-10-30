from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail
from django.urls import reverse

from mesads.app.models import ADSManagerRequest, DemandeGestionPrefecture
from mesads.users.tests.factories import UserFactory

from ..factories import (
    ADSManagerAdministratorFactory,
    ADSManagerRequestFactory,
    DemandeGestionPrefectureFactory,
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
    "statut, expiration_delta, expected_status, expected_email_count",
    [
        # Dans la fenêtre de renouvellement
        (DemandeGestionPrefecture.ACCEPTE, relativedelta(days=0), 302, 1),
        (DemandeGestionPrefecture.ACCEPTE, relativedelta(days=15), 302, 1),
        (DemandeGestionPrefecture.EXPIRE, relativedelta(days=-30), 302, 1),
        # Hors fenêtre de renouvellement
        (DemandeGestionPrefecture.ACCEPTE, relativedelta(months=2), 400, 0),
        (DemandeGestionPrefecture.ACCEPTE, None, 400, 0),
        # Statuts non renouvelables
        (DemandeGestionPrefecture.EN_ATTENTE, relativedelta(days=15), 404, 0),
        (DemandeGestionPrefecture.REFUSE, relativedelta(days=15), 404, 0),
    ],
)
def test_renouvellement_demande_gestion_prefecture(
    client_factory,
    statut,
    expiration_delta,
    expected_status,
    expected_email_count,
):
    user = UserFactory()
    administrator = ADSManagerAdministratorFactory()

    demande = DemandeGestionPrefecture.objects.create(
        administrator=administrator,
        user=user,
        statut=statut,
        expire_at=date.today() + expiration_delta
        if expiration_delta is not None
        else None,
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
        expire_at=date.today() + relativedelta(days=15),
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


def url_renouvellement_gestionnaire(ads_manager_request):
    return reverse(
        "app.ads-manager.renouvellement_demande_gestion",
        kwargs={"manager_id": ads_manager_request.ads_manager.id},
    )


@pytest.mark.parametrize(
    "statut, expiration_delta, expected_status",
    [
        # Dans la fenêtre de renouvellement
        (ADSManagerRequest.ACCEPTE, relativedelta(days=0), 302),
        (ADSManagerRequest.ACCEPTE, relativedelta(days=15), 302),
        (ADSManagerRequest.EXPIRE, relativedelta(days=-30), 302),
        # Hors fenêtre de renouvellement
        (ADSManagerRequest.ACCEPTE, relativedelta(months=2), 400),
        (ADSManagerRequest.ACCEPTE, None, 400),
        # Statuts non renouvelables
        (ADSManagerRequest.EN_ATTENTE, relativedelta(days=15), 404),
        (ADSManagerRequest.REFUSE, relativedelta(days=15), 404),
    ],
)
def test_renouvellement_ads_manager_request(
    client_factory, statut, expiration_delta, expected_status
):
    user = UserFactory()
    demande = ADSManagerRequestFactory(
        user=user,
        statut=statut,
        expire_at=date.today() + expiration_delta
        if expiration_delta is not None
        else None,
    )
    administrator = demande.ads_manager.administrator

    # Gestionnaires préfecture de l'administrator relié à l'ads_manager
    prefecture_acceptee_1 = DemandeGestionPrefectureFactory(
        administrator=administrator,
        user=UserFactory(),
        statut=DemandeGestionPrefecture.ACCEPTE,
    )
    prefecture_acceptee_2 = DemandeGestionPrefectureFactory(
        administrator=administrator,
        user=UserFactory(),
        statut=DemandeGestionPrefecture.ACCEPTE,
    )
    # Ne doivent pas être notifiés
    for statut_prefecture in (
        DemandeGestionPrefecture.EN_ATTENTE,
        DemandeGestionPrefecture.REFUSE,
        DemandeGestionPrefecture.EXPIRE,
    ):
        DemandeGestionPrefectureFactory(
            administrator=administrator,
            user=UserFactory(),
            statut=statut_prefecture,
        )
    DemandeGestionPrefectureFactory(
        administrator=ADSManagerAdministratorFactory(),
        user=UserFactory(),
        statut=DemandeGestionPrefecture.ACCEPTE,
    )

    client = client_factory(user)
    response = client.post(url_renouvellement_gestionnaire(demande))

    assert response.status_code == expected_status

    demande.refresh_from_db()
    assert demande.demande_renouvellement == (expected_status == 302)

    if expected_status == 302:
        assert response.url == reverse("app.mes_acces")
        assert len(mail.outbox) == 1
        assert set(mail.outbox[0].to) == {
            prefecture_acceptee_1.user.email,
            prefecture_acceptee_2.user.email,
        }
        assert settings.MESADS_CONTACT_EMAIL not in mail.outbox[0].to
        url_demande = reverse(
            "app.ads-manager-admin.requests",
            kwargs={"prefecture_id": administrator.prefecture_id},
        )
        assert f"{url_demande}?id={demande.id}" in mail.outbox[0].body
    else:
        assert len(mail.outbox) == 0


def test_renouvellement_ads_manager_request_sans_gestionnaire_prefecture(
    client_factory,
):
    user = UserFactory()
    demande = ADSManagerRequestFactory(
        user=user,
        statut=ADSManagerRequest.ACCEPTE,
        expire_at=date.today() + relativedelta(days=15),
    )

    client = client_factory(user)
    response = client.post(url_renouvellement_gestionnaire(demande))

    assert response.status_code == 302
    demande.refresh_from_db()
    assert demande.demande_renouvellement
    assert len(mail.outbox) == 0


def test_renouvellement_ads_manager_request_other_user(client_factory):
    user = UserFactory()
    demande = ADSManagerRequestFactory(
        user=UserFactory(),
        statut=ADSManagerRequest.ACCEPTE,
        expire_at=date.today() + relativedelta(days=15),
    )
    DemandeGestionPrefectureFactory(
        administrator=demande.ads_manager.administrator,
        user=UserFactory(),
        statut=DemandeGestionPrefecture.ACCEPTE,
    )

    client = client_factory(user)
    response = client.post(url_renouvellement_gestionnaire(demande))

    assert response.status_code == 404
    demande.refresh_from_db()
    assert not demande.demande_renouvellement
    assert len(mail.outbox) == 0


def test_permissions_user_list_view_gestionnaire(client_factory):
    user = UserFactory()
    acceptee = ADSManagerRequestFactory(
        user=user,
        statut=ADSManagerRequest.ACCEPTE,
        expire_at=date.today() + relativedelta(days=15),
    )
    expiree = ADSManagerRequestFactory(user=user, statut=ADSManagerRequest.EXPIRE)
    ADSManagerRequestFactory(user=user, statut=ADSManagerRequest.EN_ATTENTE)
    ADSManagerRequestFactory(user=UserFactory(), statut=ADSManagerRequest.ACCEPTE)

    client = client_factory(user)
    response = client.get(reverse("app.mes_acces"))

    assert response.status_code == 200
    assert set(response.context["permissions_gestionnaire"]) == {acceptee, expiree}
    assert url_renouvellement_gestionnaire(acceptee) in response.content.decode()

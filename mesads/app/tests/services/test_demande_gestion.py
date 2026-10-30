from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from django.core import mail

from mesads.app.models import ADSManagerRequest, DemandeGestionPrefecture
from mesads.app.services.demande_gestion import (
    notify_ads_manager_request,
    notify_demande_gestion_prefecture,
    update_statut_ads_manager_request,
    update_statut_demande_gestion_prefecture,
)
from mesads.users.tests.factories import UserFactory

from ..factories import (
    ADSManagerAdministratorFactory,
    ADSManagerRequestFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "expiration_delta,expected",
    [
        (relativedelta(days=-1), 0),  # Déjà expirée
        (relativedelta(days=0), 1),  # Expire aujourd'hui
        (relativedelta(days=15), 1),  # Expire dans 15 jours
        (relativedelta(months=1), 1),  # Expire dans un mois
        (relativedelta(months=2), 0),  # Expire dans deux mois
    ],
)
def test_notify_prefecture(expiration_delta, expected):
    administrator = ADSManagerAdministratorFactory()
    user = UserFactory()
    today = date.today()

    demande = DemandeGestionPrefecture.objects.create(
        administrator=administrator,
        user=user,
        statut=DemandeGestionPrefecture.ACCEPTE,
        accepted_at=today - relativedelta(years=2),
        expire_at=today + expiration_delta,
    )

    result = notify_demande_gestion_prefecture()

    assert result == expected

    demande.refresh_from_db()
    assert demande.notified == bool(expected)
    assert len(mail.outbox) == expected

    if expected:
        assert mail.outbox[0].to == [user.email]


@pytest.mark.parametrize(
    "expiration_delta, initial_statut, expected_statut, expected_count",
    [
        (
            relativedelta(days=-1),
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.EXPIRE,
            1,
        ),
        (
            relativedelta(months=-1),
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.EXPIRE,
            1,
        ),
        (
            relativedelta(days=0),
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.ACCEPTE,
            0,
        ),
        (
            relativedelta(days=1),
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.ACCEPTE,
            0,
        ),
        (
            relativedelta(months=1),
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.ACCEPTE,
            0,
        ),
        (
            relativedelta(days=-1),
            DemandeGestionPrefecture.EXPIRE,
            DemandeGestionPrefecture.EXPIRE,
            0,
        ),
        (
            relativedelta(days=-1),
            DemandeGestionPrefecture.EN_ATTENTE,
            DemandeGestionPrefecture.EN_ATTENTE,
            0,
        ),
    ],
)
def test_update_statut_demande_gestion_prefecture(
    expiration_delta,
    initial_statut,
    expected_statut,
    expected_count,
):
    administrator = ADSManagerAdministratorFactory()
    user = UserFactory()
    today = date.today()

    demande = DemandeGestionPrefecture.objects.create(
        administrator=administrator,
        user=user,
        statut=initial_statut,
        accepted_at=today - relativedelta(years=2),
        expire_at=today + expiration_delta,
    )

    result = update_statut_demande_gestion_prefecture()

    assert result == expected_count

    demande.refresh_from_db()
    assert demande.statut == expected_statut


@pytest.mark.parametrize(
    "expiration_delta,expected",
    [
        (relativedelta(days=-1), 0),  # Déjà expirée
        (relativedelta(days=0), 1),  # Expire aujourd'hui
        (relativedelta(days=15), 1),  # Expire dans 15 jours
        (relativedelta(months=1), 1),  # Expire dans un mois
        (relativedelta(months=2), 0),  # Expire dans deux mois
    ],
)
def test_notify_ads_manager_request(expiration_delta, expected):
    user = UserFactory()
    today = date.today()

    demande = ADSManagerRequestFactory(
        user=user,
        statut=ADSManagerRequest.ACCEPTE,
        accepted_at=today - relativedelta(years=2),
        expire_at=today + expiration_delta,
    )

    result = notify_ads_manager_request()

    assert result == expected

    demande.refresh_from_db()
    assert demande.notified == bool(expected)
    assert len(mail.outbox) == expected

    if expected:
        assert mail.outbox[0].to == [user.email]


@pytest.mark.parametrize(
    "statut",
    [ADSManagerRequest.EN_ATTENTE, ADSManagerRequest.REFUSE, ADSManagerRequest.EXPIRE],
)
def test_notify_ads_manager_request_non_acceptee(statut):
    today = date.today()
    ADSManagerRequestFactory(
        user=UserFactory(),
        statut=statut,
        expire_at=today + relativedelta(days=15),
    )

    assert notify_ads_manager_request() == 0
    assert len(mail.outbox) == 0


def test_notify_ads_manager_request_deja_notifiee():
    today = date.today()
    ADSManagerRequestFactory(
        user=UserFactory(),
        statut=ADSManagerRequest.ACCEPTE,
        expire_at=today + relativedelta(days=15),
        notified=True,
    )

    assert notify_ads_manager_request() == 0
    assert len(mail.outbox) == 0


@pytest.mark.parametrize(
    "expiration_delta, initial_statut, expected_statut, expected_count",
    [
        (
            relativedelta(days=-1),
            ADSManagerRequest.ACCEPTE,
            ADSManagerRequest.EXPIRE,
            1,
        ),
        (
            relativedelta(months=-1),
            ADSManagerRequest.ACCEPTE,
            ADSManagerRequest.EXPIRE,
            1,
        ),
        (
            relativedelta(days=0),
            ADSManagerRequest.ACCEPTE,
            ADSManagerRequest.ACCEPTE,
            0,
        ),
        (
            relativedelta(months=1),
            ADSManagerRequest.ACCEPTE,
            ADSManagerRequest.ACCEPTE,
            0,
        ),
        (
            relativedelta(days=-1),
            ADSManagerRequest.EXPIRE,
            ADSManagerRequest.EXPIRE,
            0,
        ),
        (
            relativedelta(days=-1),
            ADSManagerRequest.EN_ATTENTE,
            ADSManagerRequest.EN_ATTENTE,
            0,
        ),
        (
            relativedelta(days=-1),
            ADSManagerRequest.REFUSE,
            ADSManagerRequest.REFUSE,
            0,
        ),
    ],
)
def test_update_statut_ads_manager_request(
    expiration_delta,
    initial_statut,
    expected_statut,
    expected_count,
):
    today = date.today()

    demande = ADSManagerRequestFactory(
        user=UserFactory(),
        statut=initial_statut,
        accepted_at=today - relativedelta(years=2),
        expire_at=today + expiration_delta,
    )

    result = update_statut_ads_manager_request()

    assert result == expected_count

    demande.refresh_from_db()
    assert demande.statut == expected_statut

import pytest
from dateutil.relativedelta import relativedelta
from django.core import mail
from django.utils import timezone

from mesads.app.models import InscriptionListeAttente
from mesads.app.services.liste_attente import (
    check_and_notify_duplicated,
    supression_inscriptions_archivees,
)
from mesads.users.tests.factories import UserFactory

from ..factories import (
    ADSManagerAdministratorFactory,
    ADSManagerFactory,
    ADSManagerRequestFactory,
    InscriptionListeAttenteFactory,
)

pytestmark = pytest.mark.django_db


def test_get_export_data_liste_attente():
    administrator = ADSManagerAdministratorFactory()
    commune = ADSManagerFactory(administrator=administrator, for_commune=True)

    inscription_1 = InscriptionListeAttenteFactory(
        ads_manager=commune
    )  # ne doit pas être supprimée
    inscription_2 = InscriptionListeAttenteFactory(
        ads_manager=commune, deleted_at=timezone.now() - relativedelta(months=5)
    )  # ne doit pas être supprimée
    inscription_3 = InscriptionListeAttenteFactory(
        ads_manager=commune, deleted_at=timezone.now() - relativedelta(months=6)
    )  # doit être supprimée
    inscription_4 = InscriptionListeAttenteFactory(
        ads_manager=commune, deleted_at=timezone.now() - relativedelta(months=8)
    )  # doit être supprimée

    inscriptions_supprimees = supression_inscriptions_archivees()
    assert inscriptions_supprimees == 2
    assert InscriptionListeAttente.with_deleted.count() == 2
    inscription_ids = InscriptionListeAttente.with_deleted.values_list("pk", flat=True)
    assert inscription_1.pk in inscription_ids
    assert inscription_2.pk in inscription_ids
    assert inscription_3.pk not in inscription_ids
    assert inscription_4.pk not in inscription_ids


def test_check_and_notify_duplicated_pas_de_doublon():
    administrator = ADSManagerAdministratorFactory()
    commune = ADSManagerFactory(administrator=administrator, for_commune=True)

    inscription = InscriptionListeAttenteFactory(ads_manager=commune)

    check_and_notify_duplicated(inscription)
    assert len(mail.outbox) == 0


def test_check_and_notify_duplicated_doublon_detecte():
    administrator = ADSManagerAdministratorFactory()
    commune_1 = ADSManagerFactory(administrator=administrator, for_commune=True)
    commune_2 = ADSManagerFactory(administrator=administrator, for_commune=True)
    request_commune_1 = ADSManagerRequestFactory(
        ads_manager=commune_1, user=UserFactory()
    )
    request_commune_2 = ADSManagerRequestFactory(
        ads_manager=commune_2, user=UserFactory()
    )

    inscription_1 = InscriptionListeAttenteFactory(
        ads_manager=commune_1, numero_licence="12345"
    )
    InscriptionListeAttenteFactory(ads_manager=commune_2, numero_licence="12345")

    check_and_notify_duplicated(inscription_1)
    assert len(mail.outbox) == 2
    emails = []
    for email in mail.outbox:
        emails = emails + email.to

    assert request_commune_1.user.email in emails
    assert request_commune_2.user.email in emails

import pytest
from django.test import Client

from mesads.app.tests.factories import (
    ADSFactory,
    ADSManagerAdministratorFactory,
    ADSManagerDecreeFactory,
    ADSManagerFactory,
    ADSManagerRequestFactory,
    DemandeAccesLectureSeuleFactory,
    DemandeGestionPrefectureFactory,
    EntreeRegistreTransactionFactory,
    InscriptionListeAttenteFactory,
)
from mesads.fradm.tests.factories import PrefectureFactory
from mesads.users.tests.factories import UserFactory
from mesads.vehicules_relais.tests.factories import ProprietaireFactory, VehiculeFactory


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_factory():
    def _user_factory(**kwargs):
        return UserFactory(**kwargs)

    return _user_factory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def client_logged(user):
    client = Client()
    client.force_login(user=user)
    return client


@pytest.fixture
def client_factory(user):
    def _client_factory(user_=None):
        client = Client()
        client.force_login(user=user_ or user)
        return client

    return _client_factory


@pytest.fixture
def prefecture():
    return PrefectureFactory()


@pytest.fixture
def prefecture_factory():
    def _prefecture_factory(**kwargs):
        return PrefectureFactory(**kwargs)

    return _prefecture_factory


@pytest.fixture
def ads_manager_administrator():
    return ADSManagerAdministratorFactory()


@pytest.fixture
def ads_manager_administrator_factory():
    def _ads_manager_administrator_factory(**kwargs):
        return ADSManagerAdministratorFactory(**kwargs)

    return _ads_manager_administrator_factory


@pytest.fixture
def ads_manager():
    return ADSManagerFactory()


@pytest.fixture
def ads_manager_factory():
    def _ads_manager_factory(**kwargs):
        return ADSManagerFactory(**kwargs)

    return _ads_manager_factory


@pytest.fixture
def ads():
    return ADSFactory()


@pytest.fixture
def ads_factory():
    def _ads_factory(**kwargs):
        return ADSFactory(**kwargs)

    return _ads_factory


@pytest.fixture
def ads_manager_request_factory(user, ads_manager):
    def _ads_manager_request(user_=None, manager_=None, **kwargs):
        return ADSManagerRequestFactory(
            user=user_ or user, ads_manager=manager_ or ads_manager, **kwargs
        )

    return _ads_manager_request


@pytest.fixture
def ads_manager_decree():
    return ADSManagerDecreeFactory()


@pytest.fixture
def ads_manager_decree_factory():
    def _ads_manager_decree_factory(**kwargs):
        return ADSManagerDecreeFactory(**kwargs)

    return _ads_manager_decree_factory


@pytest.fixture
def inscription_liste_attente():
    return InscriptionListeAttenteFactory()


@pytest.fixture
def inscription_liste_attente_factory():
    def _inscription_liste_attente_factory(**kwargs):
        return InscriptionListeAttenteFactory(**kwargs)

    return _inscription_liste_attente_factory


@pytest.fixture
def entree_registre_transaction():
    return EntreeRegistreTransactionFactory()


@pytest.fixture
def entree_registre_transaction_factory():
    def _entree_registre_transaction_factory(**kwargs):
        return EntreeRegistreTransactionFactory(**kwargs)

    return _entree_registre_transaction_factory


@pytest.fixture
def demande_gestion_prefecture():
    return DemandeGestionPrefectureFactory()


@pytest.fixture
def demande_gestion_prefecture_factory():
    def _demande_gestion_prefecture_factory(**kwargs):
        return DemandeGestionPrefectureFactory(**kwargs)

    return _demande_gestion_prefecture_factory


@pytest.fixture
def demande_acces_lecture_seule():
    return DemandeAccesLectureSeuleFactory()


@pytest.fixture
def demande_acces_lecture_seule_factory():
    def _demande_acces_lecture_seule_factory(**kwargs):
        return DemandeAccesLectureSeuleFactory(**kwargs)

    return _demande_acces_lecture_seule_factory


@pytest.fixture
def proprietaire():
    return ProprietaireFactory()


@pytest.fixture
def proprietaire_factory(user):
    def _proprietaire_factory(**kwargs):
        _user = kwargs.pop("user", user)
        proprietaire = ProprietaireFactory(**kwargs)
        proprietaire.users.add(_user)
        return proprietaire

    return _proprietaire_factory


@pytest.fixture
def vehicule():
    return VehiculeFactory()


@pytest.fixture
def vehicule_factory():
    def _vehicule_factory(**kwargs):
        return VehiculeFactory(**kwargs)

    return _vehicule_factory

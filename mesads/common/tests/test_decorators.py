import pytest

from mesads.app.models import DemandeGestionPrefecture

from ..decorators import (
    is_administrator,
    is_inspecteur,
    is_manager,
    is_proprietaire,
    is_staff,
)

pytestmark = pytest.mark.django_db


def test_is_staff_with_staff_user(user_factory):
    user = user_factory(is_staff=True)
    assert is_staff(user)


def test_is_staff_with_superuser_user(user_factory):
    user = user_factory(is_superuser=True)
    assert is_staff(user)


def test_is_staff_without_staff_or_superuser(user_factory):
    user = user_factory(is_superuser=False, is_staff=False)
    assert not is_staff(user)


def test_is_manager_without_user_manager_or_ads_manager(user):
    assert not is_manager(user)


def test_is_manager_without_user_manager(user, ads_manager):
    assert not is_manager(user, manager_id=ads_manager.id)


def test_is_manager_with_user_manager_not_accepted(
    user, ads_manager, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager, accepted=False)
    assert not is_manager(user, manager_id=ads_manager.id)


def test_is_manager_with_valid_user_manager(
    user, ads_manager, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager, accepted=True)
    assert is_manager(user, manager_id=ads_manager.id)


def test_is_manager_with_other_ads_manager(
    user, ads_manager, ads_manager_factory, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager, accepted=True)
    other_manager = ads_manager_factory()
    assert not is_manager(user, manager_id=other_manager.id)


def test_is_manager_with_ads_id(user, ads, ads_manager_request_factory):
    ads_manager_request_factory(user, ads.ads_manager)
    assert is_manager(user, manager_id=ads.ads_manager.id, ads_id=ads.id)


def test_is_manager_with_ads_id_from_other_manager(
    user, ads, ads_manager, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager)
    assert not is_manager(user, manager_id=ads.ads_manager.id, ads_id=ads.id)
    assert not is_manager(user, manager_id=ads_manager.id, ads_id=ads.id)


def test_is_manager_with_arrete_id(
    user, ads_manager_decree, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager_decree.ads_manager)
    assert is_manager(
        user,
        manager_id=ads_manager_decree.ads_manager.id,
        arrete_id=ads_manager_decree.id,
    )


def test_is_manager_with_arrete_id_from_other_manager(
    user, ads_manager_decree, ads_manager, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager)
    assert not is_manager(
        user,
        manager_id=ads_manager_decree.ads_manager.id,
        arrete_id=ads_manager_decree.id,
    )
    assert not is_manager(
        user, manager_id=ads_manager.id, arrete_id=ads_manager_decree.id
    )


def test_is_manager_with_inscription_id(
    user, inscription_liste_attente, ads_manager_request_factory
):
    ads_manager_request_factory(user, inscription_liste_attente.ads_manager)
    assert is_manager(
        user,
        manager_id=inscription_liste_attente.ads_manager.id,
        inscription_id=inscription_liste_attente.id,
    )


def test_is_manager_with_inscription_id_from_other_manager(
    user, inscription_liste_attente, ads_manager, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager)
    assert not is_manager(
        user,
        manager_id=inscription_liste_attente.ads_manager.id,
        inscription_id=inscription_liste_attente.id,
    )
    assert not is_manager(
        user, manager_id=ads_manager.id, inscription_id=inscription_liste_attente.id
    )


def test_is_manager_with_entree_id(
    user, entree_registre_transaction, ads_manager_request_factory
):
    ads_manager_request_factory(user, entree_registre_transaction.ads.ads_manager)
    assert is_manager(
        user,
        manager_id=entree_registre_transaction.ads.ads_manager.id,
        entree_id=entree_registre_transaction.id,
    )


def test_is_manager_with_entree_id_from_other_manager(
    user, entree_registre_transaction, ads_manager, ads_manager_request_factory
):
    ads_manager_request_factory(user, ads_manager)
    assert not is_manager(
        user,
        manager_id=entree_registre_transaction.ads.ads_manager.id,
        entree_id=entree_registre_transaction.id,
    )
    assert not is_manager(
        user, manager_id=ads_manager.id, entree_id=entree_registre_transaction.id
    )


def test_is_administrator_with_user_not_administrator(user):
    assert not is_administrator(user)


def test_is_administrator_with_user_administrator(
    user, demande_gestion_prefecture_factory
):
    demande_gestion_prefecture_factory(user=user)
    assert is_administrator(user)


def test_is_administrator_with_prefecture_id_not_ok(user, prefecture):
    assert not is_administrator(user=user, prefecture_id=prefecture.id)


@pytest.mark.parametrize(
    "statut,expected_result",
    [
        (DemandeGestionPrefecture.ACCEPTE, True),
        (DemandeGestionPrefecture.EN_ATTENTE, False),
        (DemandeGestionPrefecture.REFUSE, False),
    ],
)
def test_is_administrator_with_prefecture_id(
    statut, expected_result, user, demande_gestion_prefecture_factory
):
    demande = demande_gestion_prefecture_factory(user=user, statut=statut)
    assert (
        is_administrator(user=user, prefecture_id=demande.administrator.prefecture.id)
        is expected_result
    )


@pytest.mark.parametrize(
    "statut,expected_result",
    [
        (DemandeGestionPrefecture.ACCEPTE, True),
        (DemandeGestionPrefecture.EN_ATTENTE, False),
        (DemandeGestionPrefecture.REFUSE, False),
    ],
)
def test_is_administrator_with_manager_id(
    statut, expected_result, user, ads_manager, demande_gestion_prefecture_factory
):
    demande_gestion_prefecture_factory(
        user=user, administrator=ads_manager.administrator, statut=statut
    )
    assert is_administrator(user=user, manager_id=ads_manager.id) is expected_result


@pytest.mark.parametrize(
    "statut,expected_result",
    [
        (DemandeGestionPrefecture.ACCEPTE, True),
        (DemandeGestionPrefecture.EN_ATTENTE, False),
        (DemandeGestionPrefecture.REFUSE, False),
    ],
)
def test_is_administrator_with_vehicule_numero(
    statut,
    expected_result,
    user,
    ads_manager_administrator,
    vehicule_factory,
    demande_gestion_prefecture_factory,
):
    demande_gestion_prefecture_factory(
        user=user, administrator=ads_manager_administrator, statut=statut
    )
    vehicule = vehicule_factory(departement=ads_manager_administrator.prefecture)
    assert (
        is_administrator(user=user, vehicule_numero=vehicule.numero) is expected_result
    )


def test_is_proprietaire_not_ok(user, proprietaire):
    assert not is_proprietaire(user=user, proprietaire_id=proprietaire.id)


def test_is_proprietaire_ok(user, proprietaire_factory):
    proprietaire = proprietaire_factory(user=user)
    assert is_proprietaire(user=user, proprietaire_id=proprietaire.id)


def test_is_proprietaire_with_vehicule_not_ok(user, vehicule):
    assert not is_proprietaire(
        user=user,
        proprietaire_id=vehicule.proprietaire.id,
        vehicule_numero=vehicule.numero,
    )


def test_is_proprietaire_with_vehicule_ok(user, proprietaire_factory, vehicule_factory):
    proprietaire = proprietaire_factory(user=user)
    vehicule_1 = vehicule_factory(proprietaire=proprietaire)
    vehicule_2 = vehicule_factory()
    assert is_proprietaire(
        user=user, proprietaire_id=proprietaire.id, vehicule_numero=vehicule_1.numero
    )
    assert not is_proprietaire(
        user=user, proprietaire_id=proprietaire.id, vehicule_numero=vehicule_2.numero
    )


def test_is_inspecteur_with_user_not_inscpecteur(user):
    assert not is_inspecteur(user)


@pytest.mark.parametrize(
    "statut,expected_result",
    [
        (DemandeGestionPrefecture.ACCEPTE, True),
        (DemandeGestionPrefecture.EN_ATTENTE, False),
        (DemandeGestionPrefecture.REFUSE, False),
    ],
)
def test_is_inspecteur(
    statut, expected_result, user, demande_acces_lecture_seule_factory
):
    demande = demande_acces_lecture_seule_factory(user=user, statut=statut)
    assert (
        is_inspecteur(user=user, prefecture_id=demande.administrator.prefecture.id)
        is expected_result
    )

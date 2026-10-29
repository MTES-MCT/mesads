import datetime

import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from mesads.app.models import DemandeAccesLectureSeule, DemandeGestionPrefecture
from mesads.app.tests.factories import (
    ADSManagerAdministratorFactory,
    ADSManagerRequestFactory,
)
from mesads.vehicules_relais.models import Proprietaire

from ..models import User
from .factories import NoteUtilisateurFactory, UserAuditEntryFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_show_notation_without_connexion(user: User):
    assert not user.show_notation()


def test_show_notation_with_one_connexion(user: User):
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    assert not user.show_notation()


def test_show_notation_with_more_than_one_connexion(user: User):
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    assert user.show_notation()


def test_show_notation_with_last_affichage_older_than_a_month(user: User):
    last_affichage = timezone.now() - relativedelta(months=2)
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    NoteUtilisateurFactory(user=user, dernier_affichage=last_affichage.date())
    assert user.show_notation()


def test_show_notation_with_last_affichage_younger_than_a_month(user: User):
    last_affichage = timezone.now() - datetime.timedelta(days=10)
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    NoteUtilisateurFactory(user=user, dernier_affichage=last_affichage.date())
    assert not user.show_notation()


def test_show_notation_with_last_older_than_a_month_and_note_younger_than_six(
    user: User,
):
    last_affichage = timezone.now() - relativedelta(months=2)
    last_note = timezone.now() - relativedelta(months=2)
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    NoteUtilisateurFactory(
        user=user,
        dernier_affichage=last_affichage.date(),
        derniere_note=last_note.date(),
    )
    assert not user.show_notation()


def test_show_notation_with_last_older_than_a_month_and_note_older_than_six(user: User):
    last_affichage = timezone.now() - relativedelta(months=2)
    last_note = timezone.now() - relativedelta(months=7)
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    NoteUtilisateurFactory(
        user=user,
        dernier_affichage=last_affichage.date(),
        derniere_note=last_note.date(),
    )
    assert user.show_notation()


def test_show_notation_with_last_younger_than_a_month_and_note_older_than_six(
    user: User,
):
    last_affichage = timezone.now() - datetime.timedelta(days=10)
    last_note = timezone.now() - relativedelta(months=7)
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    UserAuditEntryFactory(
        user=user,
        action="login",
    )
    NoteUtilisateurFactory(
        user=user,
        dernier_affichage=last_affichage.date(),
        derniere_note=last_note.date(),
    )
    assert not user.show_notation()


# ---------------------------------------------------------------------------
# Permissions MesADS
# ---------------------------------------------------------------------------


def _accept_ads_manager_request(user):
    ADSManagerRequestFactory(user=user, accepted=True)


def _accept_lecture_seule(user):
    DemandeAccesLectureSeule.objects.create(
        user=user,
        administrator=ADSManagerAdministratorFactory(),
        statut=DemandeAccesLectureSeule.ACCEPTE,
    )


def _accept_gestion_prefecture(user):
    DemandeGestionPrefecture.objects.create(
        user=user,
        administrator=ADSManagerAdministratorFactory(),
        statut=DemandeGestionPrefecture.ACCEPTE,
    )


def _add_proprietaire(user):
    Proprietaire.objects.create(nom="Propriétaire").users.add(user)


def _make_staff(user):
    user.is_staff = True
    user.save()


def _make_superuser(user):
    user.is_superuser = True
    user.save()


@pytest.mark.parametrize(
    "grant",
    [
        _accept_ads_manager_request,
        _accept_lecture_seule,
        _accept_gestion_prefecture,
        _add_proprietaire,
        _make_staff,
        _make_superuser,
    ],
)
def test_permission_mesads(grant):
    user = UserFactory()
    other = UserFactory()
    grant(user)

    assert user.has_permission_mesads
    assert not other.has_permission_mesads
    assert list(User.objects.with_permission_mesads()) == [user]
    assert list(User.objects.without_permission_mesads()) == [other]


def test_no_permission_mesads_with_pending_or_refused_requests():
    user = UserFactory()
    ADSManagerRequestFactory(user=user, accepted=None)
    ADSManagerRequestFactory(user=user, accepted=False)
    DemandeAccesLectureSeule.objects.create(
        user=user,
        administrator=ADSManagerAdministratorFactory(),
        statut=DemandeAccesLectureSeule.EN_ATTENTE,
    )
    DemandeGestionPrefecture.objects.create(
        user=user,
        administrator=ADSManagerAdministratorFactory(),
        statut=DemandeGestionPrefecture.EN_ATTENTE,
    )

    assert not user.has_permission_mesads
    assert not User.objects.with_permission_mesads().exists()
    assert list(User.objects.without_permission_mesads()) == [user]


def test_with_permission_mesads_returns_no_duplicates():
    user = UserFactory()
    for _ in range(2):
        _accept_ads_manager_request(user)
        _accept_lecture_seule(user)

    assert list(User.objects.with_permission_mesads()) == [user]

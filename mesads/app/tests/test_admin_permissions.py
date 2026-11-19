"""Journalisation des changements d'accès réalisés depuis l'admin Django."""

import pytest
from django.urls import reverse

from mesads.app.models import (
    ADSManagerRequest,
    DemandeAccesLectureSeule,
    DemandeGestionPrefecture,
)
from mesads.app.tests.factories import (
    ADSManagerFactory,
    ADSManagerRequestFactory,
    DemandeAccesLectureSeuleFactory,
    DemandeGestionPrefectureFactory,
)
from mesads.users.models import PermissionAuditEntry

pytestmark = pytest.mark.django_db

Action = PermissionAuditEntry.Action


@pytest.fixture
def admin_user(user_factory):
    return user_factory(email="admin@example.com", is_staff=True, is_superuser=True)


@pytest.fixture
def admin_client(client_factory, admin_user):
    return client_factory(admin_user)


def entries_for(user):
    return list(
        PermissionAuditEntry.objects.filter(target_user=user)
        .order_by("created_at", "pk")
        .values_list("action", flat=True)
    )


def delete_selected(admin_client, model, objs):
    url = reverse(f"admin:app_{model._meta.model_name}_changelist")
    return admin_client.post(
        url,
        {
            "action": "delete_selected",
            "_selected_action": [obj.pk for obj in objs],
            "post": "yes",
        },
    )


# ---------------------------------------------------------------------------
# ADSManagerRequest
# ---------------------------------------------------------------------------


def ads_manager_request_form_data(ads_manager_request, accepted):
    return {
        "user": ads_manager_request.user.pk,
        "ads_manager": ads_manager_request.ads_manager.pk,
        "accepted": {True: "true", False: "false", None: "unknown"}[accepted],
    }


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (None, True, [Action.ADS_MANAGER_GRANTED]),
        (None, False, [Action.ADS_MANAGER_REFUSED]),
        (True, False, [Action.ADS_MANAGER_REVOKED]),
        (True, True, []),
    ],
)
def test_admin_change_ads_manager_request(
    admin_client, admin_user, user_factory, before, after, expected
):
    ads_manager_request = ADSManagerRequestFactory(user=user_factory(), accepted=before)

    response = admin_client.post(
        reverse("admin:app_adsmanagerrequest_change", args=[ads_manager_request.pk]),
        ads_manager_request_form_data(ads_manager_request, after),
    )

    assert response.status_code == 302
    assert entries_for(ads_manager_request.user) == expected
    for entry in PermissionAuditEntry.objects.all():
        assert entry.actor == admin_user
        assert entry.details["ads_manager_request_id"] == ads_manager_request.pk


def test_admin_add_accepted_ads_manager_request(admin_client, user_factory):
    user = user_factory()
    ads_manager = ADSManagerFactory()

    response = admin_client.post(
        reverse("admin:app_adsmanagerrequest_add"),
        {"user": user.pk, "ads_manager": ads_manager.pk, "accepted": "true"},
    )

    assert response.status_code == 302
    created = ADSManagerRequest.objects.get(user=user)
    assert entries_for(user) == [Action.ADS_MANAGER_GRANTED]
    assert (
        PermissionAuditEntry.objects.get().details["ads_manager_request_id"]
        == created.pk
    )


def test_admin_delete_ads_manager_request(admin_client, user_factory):
    accepted = ADSManagerRequestFactory(user=user_factory(), accepted=True)
    pending = ADSManagerRequestFactory(user=user_factory(), accepted=None)

    for obj in (accepted, pending):
        response = admin_client.post(
            reverse("admin:app_adsmanagerrequest_delete", args=[obj.pk]),
            {"post": "yes"},
        )
        assert response.status_code == 302

    assert entries_for(accepted.user) == [Action.ADS_MANAGER_REVOKED]
    entry = PermissionAuditEntry.objects.get()
    assert entry.details["deleted"] is True
    assert entry.details["ads_manager_request_id"] == accepted.pk
    assert entries_for(pending.user) == []


def test_admin_bulk_delete_ads_manager_requests(admin_client, user_factory):
    requests = [
        ADSManagerRequestFactory(user=user_factory(), accepted=True) for _ in range(2)
    ]

    response = delete_selected(admin_client, ADSManagerRequest, requests)

    assert response.status_code == 302
    assert not ADSManagerRequest.objects.exists()
    for obj in requests:
        assert entries_for(obj.user) == [Action.ADS_MANAGER_REVOKED]


# ---------------------------------------------------------------------------
# DemandeGestionPrefecture
# ---------------------------------------------------------------------------


def demande_form_data(demande, statut):
    data = {
        "user": demande.user.pk,
        "administrator": demande.administrator.pk,
        "statut": statut,
        "accepted_at": "",
    }
    if isinstance(demande, DemandeGestionPrefecture):
        data["statut_user"] = "Agent de préfecture"
    return data


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (
            DemandeGestionPrefecture.EN_ATTENTE,
            DemandeGestionPrefecture.ACCEPTE,
            [Action.PREFECTURE_MANAGER_GRANTED],
        ),
        (
            DemandeGestionPrefecture.EN_ATTENTE,
            DemandeGestionPrefecture.REFUSE,
            [Action.PREFECTURE_MANAGER_REFUSED],
        ),
        (
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.REFUSE,
            [Action.PREFECTURE_MANAGER_REVOKED],
        ),
        (
            DemandeGestionPrefecture.ACCEPTE,
            DemandeGestionPrefecture.EN_ATTENTE,
            [Action.PREFECTURE_MANAGER_REVOKED],
        ),
        (DemandeGestionPrefecture.REFUSE, DemandeGestionPrefecture.EN_ATTENTE, []),
    ],
)
def test_admin_change_demande_gestion_prefecture(
    admin_client, admin_user, user_factory, before, after, expected
):
    demande = DemandeGestionPrefectureFactory(user=user_factory(), statut=before)

    response = admin_client.post(
        reverse("admin:app_demandegestionprefecture_change", args=[demande.pk]),
        demande_form_data(demande, after),
    )

    assert response.status_code == 302
    assert entries_for(demande.user) == expected
    for entry in PermissionAuditEntry.objects.all():
        assert entry.actor == admin_user
        assert entry.details["demande_id"] == demande.pk
        assert entry.details["administrator_id"] == demande.administrator_id


def test_admin_delete_demande_gestion_prefecture(admin_client, user_factory):
    demande = DemandeGestionPrefectureFactory(
        user=user_factory(), statut=DemandeGestionPrefecture.ACCEPTE
    )

    response = admin_client.post(
        reverse("admin:app_demandegestionprefecture_delete", args=[demande.pk]),
        {"post": "yes"},
    )

    assert response.status_code == 302
    assert entries_for(demande.user) == [Action.PREFECTURE_MANAGER_REVOKED]
    assert PermissionAuditEntry.objects.get().details["deleted"] is True


def test_admin_bulk_delete_demandes_gestion_prefecture(admin_client, user_factory):
    accepted = DemandeGestionPrefectureFactory(
        user=user_factory(), statut=DemandeGestionPrefecture.ACCEPTE
    )
    pending = DemandeGestionPrefectureFactory(
        user=user_factory(), statut=DemandeGestionPrefecture.EN_ATTENTE
    )

    response = delete_selected(
        admin_client, DemandeGestionPrefecture, [accepted, pending]
    )

    assert response.status_code == 302
    assert entries_for(accepted.user) == [Action.PREFECTURE_MANAGER_REVOKED]
    assert entries_for(pending.user) == []


# ---------------------------------------------------------------------------
# DemandeAccesLectureSeule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (
            DemandeAccesLectureSeule.EN_ATTENTE,
            DemandeAccesLectureSeule.ACCEPTE,
            [Action.READ_ONLY_GRANTED],
        ),
        (
            DemandeAccesLectureSeule.EN_ATTENTE,
            DemandeAccesLectureSeule.REFUSE,
            [Action.READ_ONLY_REFUSED],
        ),
        (
            DemandeAccesLectureSeule.ACCEPTE,
            DemandeAccesLectureSeule.REFUSE,
            [Action.READ_ONLY_REVOKED],
        ),
        (
            DemandeAccesLectureSeule.ACCEPTE,
            DemandeAccesLectureSeule.EN_ATTENTE,
            [Action.READ_ONLY_REVOKED],
        ),
        (DemandeAccesLectureSeule.ACCEPTE, DemandeAccesLectureSeule.ACCEPTE, []),
    ],
)
def test_admin_change_demande_lecture_seule(
    admin_client, admin_user, user_factory, before, after, expected
):
    demande = DemandeAccesLectureSeuleFactory(user=user_factory(), statut=before)

    response = admin_client.post(
        reverse("admin:app_demandeacceslectureseule_change", args=[demande.pk]),
        demande_form_data(demande, after),
    )

    assert response.status_code == 302
    assert entries_for(demande.user) == expected
    for entry in PermissionAuditEntry.objects.all():
        assert entry.actor == admin_user
        assert entry.details["demande_id"] == demande.pk
        assert entry.details["administrator_id"] == demande.administrator_id


def test_admin_demande_lecture_seule_sets_accepted_at(admin_client, user_factory):
    demande = DemandeAccesLectureSeuleFactory(
        user=user_factory(), statut=DemandeAccesLectureSeule.EN_ATTENTE
    )

    admin_client.post(
        reverse("admin:app_demandeacceslectureseule_change", args=[demande.pk]),
        demande_form_data(demande, DemandeAccesLectureSeule.ACCEPTE),
    )

    demande.refresh_from_db()
    assert demande.statut == DemandeAccesLectureSeule.ACCEPTE
    assert demande.accepted_at is not None


def test_admin_delete_demande_lecture_seule(admin_client, user_factory):
    demande = DemandeAccesLectureSeuleFactory(
        user=user_factory(), statut=DemandeAccesLectureSeule.ACCEPTE
    )

    response = admin_client.post(
        reverse("admin:app_demandeacceslectureseule_delete", args=[demande.pk]),
        {"post": "yes"},
    )

    assert response.status_code == 302
    assert entries_for(demande.user) == [Action.READ_ONLY_REVOKED]


def test_admin_bulk_delete_demandes_lecture_seule(admin_client, user_factory):
    demande = DemandeAccesLectureSeuleFactory(
        user=user_factory(), statut=DemandeAccesLectureSeule.ACCEPTE
    )

    response = delete_selected(admin_client, DemandeAccesLectureSeule, [demande])

    assert response.status_code == 302
    assert entries_for(demande.user) == [Action.READ_ONLY_REVOKED]

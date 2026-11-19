"""Journalisation des changements d'accès aux ADS (gestionnaire d'administration,
gestionnaire de préfecture, lecture seule) dans `PermissionAuditEntry`."""

from mesads.users.services import log_access_change

from ..models import DemandeAccesLectureSeule, DemandeGestionPrefecture

DEMANDE_STATUT_TO_GRANTED = {
    DemandeGestionPrefecture.ACCEPTE: True,
    DemandeGestionPrefecture.REFUSE: False,
    DemandeGestionPrefecture.EN_ATTENTE: None,
    "": None,
    None: None,
}

DEMANDE_ACCESS_TYPES = {
    DemandeGestionPrefecture: "prefecture_manager",
    DemandeAccesLectureSeule: "read_only",
}


def log_ads_manager_request_change(
    ads_manager_request, was_accepted, actor=None, request=None
):
    return log_access_change(
        "ads_manager",
        ads_manager_request.user,
        was_granted=was_accepted,
        is_granted=ads_manager_request.accepted,
        actor=actor,
        request=request,
        **ads_manager_request_details(ads_manager_request),
    )


def log_ads_manager_request_deletion(ads_manager_request, actor=None, request=None):
    return log_access_change(
        "ads_manager",
        ads_manager_request.user,
        was_granted=ads_manager_request.accepted,
        is_granted=None,
        actor=actor,
        request=request,
        deleted=True,
        **ads_manager_request_details(ads_manager_request),
    )


def ads_manager_request_details(ads_manager_request):
    ads_manager = ads_manager_request.ads_manager
    return {
        "ads_manager_request_id": ads_manager_request.pk,
        "ads_manager_id": ads_manager.pk,
        "administration": ads_manager.content_object.display_text(),
    }


def log_demande_acces_change(
    demande, old_statut, new_statut=None, actor=None, request=None, deleted=False
):
    if new_statut is None and not deleted:
        new_statut = demande.statut

    details = {
        "demande_id": demande.pk,
        "administrator_id": demande.administrator_id,
        "prefecture": str(demande.administrator.prefecture),
    }
    if deleted:
        details["deleted"] = True

    return log_access_change(
        DEMANDE_ACCESS_TYPES[type(demande)],
        demande.user,
        was_granted=DEMANDE_STATUT_TO_GRANTED[old_statut],
        is_granted=None if deleted else DEMANDE_STATUT_TO_GRANTED[new_statut],
        actor=actor,
        request=request,
        **details,
    )

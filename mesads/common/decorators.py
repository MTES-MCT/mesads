from functools import wraps

from django.http import Http404

from mesads.app.models import (
    ADS,
    ADSManager,
    ADSManagerDecree,
    ADSManagerRequest,
    DemandeAccesLectureSeule,
    DemandeGestionPrefecture,
    EntreeRegistreTransaction,
    InscriptionListeAttente,
)
from mesads.vehicules_relais.models import Proprietaire, Vehicule


def is_staff(user, *args, **kwargs):
    return user.is_staff or user.is_superuser


def is_manager(user, *args, **kwargs):
    if kwargs.get("manager_id"):
        manager_request = ADSManagerRequest.objects.filter(
            user=user,
            ads_manager__id=kwargs.get("manager_id"),
            accepted=True,
        ).first()
        if not manager_request:
            return False

        if kwargs.get("entree_id"):
            return EntreeRegistreTransaction.with_deleted.filter(
                id=kwargs["entree_id"], ads__ads_manager=manager_request.ads_manager
            ).exists()
        if kwargs.get("ads_id"):
            return ADS.with_deleted.filter(
                id=kwargs["ads_id"], ads_manager=manager_request.ads_manager
            ).exists()
        if kwargs.get("inscription_id"):
            return InscriptionListeAttente.with_deleted.filter(
                id=kwargs["inscription_id"], ads_manager=manager_request.ads_manager
            ).exists()
        if kwargs.get("arrete_id"):
            return ADSManagerDecree.objects.filter(
                id=kwargs["arrete_id"], ads_manager=manager_request.ads_manager
            ).exists()

        return True
    return False


def is_administrator(user, *args, **kwargs):
    if kwargs.get("prefecture_id"):
        return DemandeGestionPrefecture.objects.filter(
            administrator__prefecture__id=kwargs.get("prefecture_id"),
            user=user,
            statut=DemandeGestionPrefecture.ACCEPTE,
        ).exists()
    elif kwargs.get("manager_id"):
        ads_manager = ADSManager.objects.filter(id=kwargs.get("manager_id")).first()
        if not ads_manager:
            return False

        return DemandeGestionPrefecture.objects.filter(
            administrator=ads_manager.administrator,
            user=user,
            statut=DemandeGestionPrefecture.ACCEPTE,
        ).exists()
    elif kwargs.get("vehicule_numero"):
        vehicule = Vehicule.objects.filter(numero=kwargs.get("vehicule_numero")).first()
        if not vehicule:
            return False
        return DemandeGestionPrefecture.objects.filter(
            administrator__prefecture=vehicule.departement,
            user=user,
            statut=DemandeGestionPrefecture.ACCEPTE,
        ).exists()
    else:
        return DemandeGestionPrefecture.objects.filter(
            user=user, statut=DemandeGestionPrefecture.ACCEPTE
        ).exists()


def is_proprietaire(user, *args, **kwargs):
    if kwargs.get("proprietaire_id"):
        proprietaire = Proprietaire.objects.filter(
            id=kwargs.get("proprietaire_id"), users__in=[user]
        ).first()
        if not proprietaire:
            return False
        if kwargs.get("vehicule_numero"):
            return Vehicule.objects.filter(
                proprietaire=proprietaire, numero=kwargs["vehicule_numero"]
            )
        return True
    return False


def is_inspecteur(user, *args, **kwargs):
    return DemandeAccesLectureSeule.objects.filter(
        user=user, statut=DemandeAccesLectureSeule.ACCEPTE
    ).exists()


def profil_required(*checks):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise Http404
            if any(check(request.user, *args, **kwargs) for check in checks):
                return view_func(request, *args, **kwargs)

            raise Http404

        return wrapper

    return decorator

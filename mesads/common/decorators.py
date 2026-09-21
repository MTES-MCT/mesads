from functools import wraps

from django.http import Http404

from mesads.app.models import (
    ADSManager,
    ADSManagerAdministrator,
    ADSManagerRequest,
    DemandeAccesLectureSeule,
)
from mesads.vehicules_relais.models import Proprietaire, Vehicule


def is_staff(user, *args, **kwargs):
    return user.is_staff or user.is_superuser


def is_manager(user, *args, **kwargs):
    if kwargs.get("manager_id"):
        return ADSManagerRequest.objects.filter(
            user=user,
            ads_manager__id=kwargs.get("manager_id"),
            accepted=True,
        )
    return None


def is_administrator(user, *args, **kwargs):
    if kwargs.get("prefecture_id"):
        return ADSManagerAdministrator.objects.filter(
            prefecture__id=kwargs.get("prefecture_id"), users__in=[user]
        ).exists()
    elif kwargs.get("manager_id"):
        ads_manager = ADSManager.objects.filter(id=kwargs.get("manager_id")).first()
        if not ads_manager:
            return False

        return ADSManagerAdministrator.objects.filter(
            id=ads_manager.administrator.id, users__in=[user]
        ).exists()
    elif kwargs.get("vehicule_numero"):
        vehicule = Vehicule.objects.filter(numero=kwargs.get("vehicule_numero")).first()
        if not vehicule:
            return False
        return ADSManagerAdministrator.objects.filter(
            prefecture=vehicule.departement, users__in=[user]
        ).exists()
    else:
        return ADSManagerAdministrator.objects.filter(users__in=[user]).exists()


def is_proprietaire(user, *args, **kwargs):
    if kwargs.get("proprietaire_id"):
        return Proprietaire.objects.filter(
            id=kwargs.get("proprietaire_id"), users__in=[user]
        ).exists()
    return None


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

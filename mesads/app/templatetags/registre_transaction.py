from django import template
from django.urls import reverse

from mesads.app.models import EntreeRegistreTransaction

register = template.Library()


@register.simple_tag
def modification_url(entree_registre):
    kwargs = {
        "manager_id": entree_registre.ads.ads_manager.id,
        "entree_id": entree_registre.id,
    }
    if entree_registre.statut != EntreeRegistreTransaction.BROUILLON:
        return reverse("app.transaction-edition", kwargs=kwargs)

    if entree_registre.documents_complet:
        return reverse("app.transaction-enregistrement", kwargs=kwargs)
    return reverse("app.transaction-documents", kwargs=kwargs)

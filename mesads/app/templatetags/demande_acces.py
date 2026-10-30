from django import template

from mesads.app.models import DemandeAcces

register = template.Library()


@register.filter
def statut_css_class(obj):
    if obj.statut == DemandeAcces.ACCEPTE:
        return "fr-badge--success"
    elif obj.statut == DemandeAcces.EXPIRE:
        return "fr-badge--warning"
    elif obj.statut == DemandeAcces.REFUSE:
        return "fr-badge--error"
    else:
        return "fr-badge--info"

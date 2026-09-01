from django import template

from mesads.newsletters.models import BandeauInformation

register = template.Library()


@register.inclusion_tag("pages/accueil/bandeau_information.html")
def bandeau_information():
    bandeau = BandeauInformation.get_solo()
    return {
        "bandeau_information": bandeau,
    }

from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings

from mesads.common.mail import envoi_email

from ..models import DemandeGestionPrefecture


def notify_demande_gestion_prefecture():
    today = date.today()
    nombre_notifications = 0
    for demande in DemandeGestionPrefecture.objects.filter(
        statut=DemandeGestionPrefecture.ACCEPTE,
        expire_at__gte=today,
        expire_at__lte=today + relativedelta(months=1),
        notified=False,
    ):
        envoi_email(
            content_template_txt="demande_gestion_prefecture/email_demande_gestion_prefecture_expiration_content.txt",
            content_template_mjml="demande_gestion_prefecture/email_demande_gestion_prefecture_expiration_content.mjml",
            context={"demande": demande, "base_url": settings.MESADS_BASE_URL},
            destinataires=[demande.user.email],
            sujet="Mes ADS - Renouvellement de vos droits d'accès.",
        )
        demande.notified = True
        demande.save(update_fields=["notified"])
        nombre_notifications += 1
    return nombre_notifications


def update_statut_demande_gestion_prefecture():
    return DemandeGestionPrefecture.objects.filter(
        statut=DemandeGestionPrefecture.ACCEPTE,
        expire_at__lt=date.today(),
    ).update(statut=DemandeGestionPrefecture.EXPIRE)

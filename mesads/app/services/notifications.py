from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import (
    BooleanField,
    Case,
    DateTimeField,
    ExpressionWrapper,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Now
from django.template.loader import render_to_string

from ..models import (
    ADS,
    ADSManager,
    ADSManagerAdministrator,
    ADSManagerRequest,
    ADSUpdateLog,
)


def notify_managers_for_verification(prefecture, progress):
    """
    Fonctions qui prends en paramètre une Queryset de prefectures
    (sous forme d'ADSManagerAdministrator)
    On va regarder tout les administrations de ces préfectures.
    Pour chaque administrations, si il y a au moins une ADS
    qui n'est pas complète/à jour, on va envoyer un mail pour le
    signifier au(x) gestionnaire(s).
    """

    subject = render_to_string("mail_ads_manager/demande_verification_subject.txt")
    from_email = settings.MESADS_CONTACT_EMAIL

    nb_mails_send = 0
    for ads_manager in ADSManager.objects.filter(administrator=prefecture):
        latest_log_qs = ADSUpdateLog.objects.filter(ads=OuterRef("pk")).order_by(
            "-update_at"
        )
        queryset = (
            ADS.objects.filter(ads_manager=ads_manager)
            .annotate(
                latest_update_log=Subquery(latest_log_qs.values("update_at")[:1]),
                latest_update_log_is_complete=Subquery(
                    latest_log_qs.values("is_complete")[:1]
                ),
                latest_update_log_is_outdated=Case(
                    When(
                        latest_update_log__gte=ExpressionWrapper(
                            Now() - timedelta(days=ADSUpdateLog.OUTDATED_LOG_DAYS),
                            output_field=DateTimeField(),
                        ),
                        then=Value(False),
                    ),
                    default=Value(True),
                    output_field=BooleanField(),
                ),
            )
            .filter(
                Q(latest_update_log_is_outdated=True)
                | Q(latest_update_log_is_complete__in=[False, None])
            )
        )

        if queryset.count() == 0:
            continue

        context = {"ads_manager": ads_manager, "BASE_URL": settings.MESADS_BASE_URL}
        recipients = [
            req.user.email
            for req in ADSManagerRequest.objects.filter(
                ads_manager=ads_manager, accepted=True
            )
        ]

        body = render_to_string(
            "mail_ads_manager/demande_verification_content.txt", context
        )
        body_html = render_to_string(
            "mail_ads_manager/demande_verification_content.mjml", context
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=recipients,
        )
        email.attach_alternative(body_html, "text/html")
        email.send(fail_silently=True)
        nb_mails_send += 1
    progress(f"Envoi de mail pour {prefecture.prefecture}: {nb_mails_send} envoyés")


def notify_prefectures_gestionnaires(progress=None):
    progress = progress or (lambda message: None)

    prefectures = ADSManagerAdministrator.objects.filter(
        notify_verification_enabled=True
    )
    progress(f"{prefectures.count()} prefectures à notifier")
    for prefecture in prefectures:
        notify_managers_for_verification(prefecture, progress=progress)

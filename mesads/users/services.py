from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from mesads.common.mail import envoi_email
from mesads.users.models import User


def delete_old_users():
    two_years_ago = timezone.now() - relativedelta(years=2)

    users = User.objects.filter(
        Q(last_login__lte=two_years_ago) | Q(last_login__isnull=True),
        ads_update_files__isnull=True,
        ads_update_logs__isnull=True,
    )

    _, deleted_by_model = users.delete()

    return deleted_by_model.get(User._meta.label, 0)


def notify_old_users():
    now = timezone.now()

    deletion_date = now - relativedelta(years=2)
    notification_date = deletion_date + relativedelta(months=1)

    users = User.objects.filter(
        last_login__gt=deletion_date,
        last_login__lte=notification_date,
        ads_update_files__isnull=True,
        ads_update_logs__isnull=True,
        delete_notification_sent=False,
    )

    notified_count = 0

    for user in users:
        envoi_email(
            content_template_txt="users/notification_suppression.txt",
            content_template_mjml="users/notification_suppression.mjml",
            context={
                "deletion_date": user.last_login + relativedelta(years=2),
                "user": user,
                "base_url": settings.MESADS_BASE_URL,
            },
            destinataires=[user.email],
            sujet="MesADS - Suppression prochaine de votre compte.",
        )

        user.delete_notification_sent = True
        user.save(update_fields=["delete_notification_sent"])

        notified_count += 1

    return notified_count

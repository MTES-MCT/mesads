from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from sentry_sdk import capture_exception

from mesads.common.mail import envoi_email
from mesads.users.models import PermissionAuditEntry, User, UserAuditEntry

INACTIVITY_DELAY = relativedelta(years=2)
NOTIFICATION_DELAY = relativedelta(months=1)
# Nombre maximum d'utilisateurs traités par exécution de `notify_old_users`, pour
# étaler l'envoi des emails (et donc les suppressions) sur plusieurs jours.
NOTIFICATION_BATCH_SIZE = 1000
# Durée de conservation de l'historique des connexions (`UserAuditEntry`).
USER_AUDIT_ENTRY_RETENTION = relativedelta(years=1)


def get_client_ip(request):
    """In production, REMOTE_ADDR is the load balancer IP, not the client IP. On
    Clever-Cloud, the client IP is in the X-Forwarded-For header."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # In case of multiple IPs, take the first one
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def delete_old_user_audit_entries():
    """Supprime les entrées de l'historique des connexions de plus d'un an,
    qui contiennent des données personnelles (adresses IP)."""
    deleted_count, _ = UserAuditEntry.objects.filter(
        created_at__lt=timezone.now() - USER_AUDIT_ENTRY_RETENTION
    ).delete()
    return deleted_count


def log_permission_change(action, target_user, *, actor=None, request=None, **details):
    """Enregistre un changement de permission ou d'identité dans le journal
    `PermissionAuditEntry`.

    `actor` est l'utilisateur à l'origine du changement, ou `None` si le
    changement est réalisé automatiquement par l'application. Les `details`
    doivent être sérialisables en JSON."""
    return PermissionAuditEntry.objects.create(
        action=action,
        target_user=target_user,
        actor=actor,
        ip=get_client_ip(request) if request is not None else None,
        details=details,
    )


def _inactive_users(since):
    """Utilisateurs sans fichier de mise à jour ADS, dont la dernière connexion
    (ou la date d'inscription s'ils ne se sont jamais connectés) est antérieure
    ou égale à `since`."""
    return User.objects.filter(
        Q(last_login__lte=since) | Q(last_login__isnull=True, date_joined__lte=since),
        ads_update_files__isnull=True,
    )


def delete_old_users():
    """Supprime les utilisateurs inactifs depuis plus de deux ans.

    - Les utilisateurs sans permission sur MesADS sont supprimés directement,
      sans notification préalable : ils n'ont accès à aucune donnée.
    - Les utilisateurs avec permission ne sont supprimés qu'au moins un mois
      après l'envoi de la notification par `notify_old_users`.
    """
    now = timezone.now()
    notification_deadline = now - NOTIFICATION_DELAY

    _, deleted_by_model = (
        _inactive_users(now - INACTIVITY_DELAY)
        .filter(
            ~User.objects.permission_mesads_q()
            | Q(delete_notification_sent_at__lte=notification_deadline)
        )
        .delete()
    )

    return deleted_by_model.get(User._meta.label, 0)


def notify_old_users(limit=NOTIFICATION_BATCH_SIZE):
    """Prévient par email les utilisateurs avec permission sur MesADS dont le
    compte sera supprimé pour inactivité dans un mois ou moins.

    Au plus `limit` utilisateurs sont traités par appel, les plus anciennement
    inactifs en premier ; les suivants le seront lors des prochains appels."""
    now = timezone.now()

    users = (
        _inactive_users(now - INACTIVITY_DELAY + NOTIFICATION_DELAY)
        .with_permission_mesads()
        .filter(delete_notification_sent_at__isnull=True)
        .order_by(Coalesce("last_login", "date_joined"), "pk")[:limit]
    )

    notified_count = 0

    for user in users.iterator():
        inactivity_date = user.last_login or user.date_joined
        # La suppression n'intervient jamais moins d'un mois après la notification.
        deletion_date = max(
            inactivity_date + INACTIVITY_DELAY,
            now + NOTIFICATION_DELAY,
        )

        try:
            envoi_email(
                content_template_txt="users/notification_suppression.txt",
                content_template_mjml="users/notification_suppression.mjml",
                context={
                    "deletion_date": deletion_date,
                    "user": user,
                    "base_url": settings.MESADS_BASE_URL,
                },
                destinataires=[user.email],
                sujet="MesADS - Suppression prochaine de votre compte.",
                fail_silently=False,
            )
            user.delete_notification_sent_at = now
            user.save(update_fields=["delete_notification_sent_at"])
            notified_count += 1
        except Exception as e:
            capture_exception(e)
            continue

    return notified_count

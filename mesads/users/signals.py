from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from .models import UserAuditEntry
from .services import get_client_ip


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    UserAuditEntry.objects.create(user=user, action="login", ip=get_client_ip(request))
    if user.delete_notification_sent_at:
        user.delete_notification_sent_at = None
        user.save(update_fields=["delete_notification_sent_at"])


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    UserAuditEntry.objects.create(user=user, action="logout", ip=get_client_ip(request))

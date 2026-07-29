import functools
import io
from contextlib import redirect_stderr, redirect_stdout

from django.core.management import call_command
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from sentry_sdk import capture_exception


def sentry_exceptions(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            capture_exception(e)
            raise

    return inner


class ImportDataForParis(CronJobBase):
    # Run every day
    schedule = Schedule(run_every_mins=60 * 24)

    code = (
        "import_last_update_file_from_Paris"  # unique code to represent this cron job
    )

    @sentry_exceptions
    def do(self):
        # Redirect stdout and stderr to a buffer to capture the output of the
        # command. By returning it, django-cron will log it in the database.
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            call_command("import_last_update_file_from_paris")
        return buf.getvalue()


class DeleteOldUsers(CronJobBase):
    # Run every week
    schedule = Schedule(run_every_mins=60 * 24 * 7)

    code = "remove_old_accounts"  # unique code to represent this cron job

    @sentry_exceptions
    def do(self):
        # Redirect stdout and stderr to a buffer to capture the output of the
        # command. By returning it, django-cron will log it in the database.
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            call_command("remove_old_accounts")
        return buf.getvalue()


class NotificationListeAttente(CronJobBase):
    # Run every day
    schedule = Schedule(run_every_mins=60 * 24)

    code = "notify_liste_attente"  # unique code to represent this cron job

    @sentry_exceptions
    def do(self):
        # Redirect stdout and stderr to a buffer to capture the output of the
        # command. By returning it, django-cron will log it in the database.
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            call_command("liste_attente_mail_delai_depasse")
        return buf.getvalue()


class NotificationVerification(CronJobBase):
    # Run every day
    schedule = Schedule(run_every_mins=60 * 24)

    code = "notify_verifications"  # unique code to represent this cron job

    @sentry_exceptions
    def do(self):
        # Redirect stdout and stderr to a buffer to capture the output of the
        # command. By returning it, django-cron will log it in the database.

        today = timezone.localdate()
        if today.day != 15:
            return "Skipped - Notifications envoyées uniquement le 15 de chaque mois."

        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            call_command("notify_prefectures_gestionnaires")
        return buf.getvalue()


class SupressionInscriptionsArchivees(CronJobBase):
    # Run every week
    schedule = Schedule(run_every_mins=60 * 24 * 7)

    code = "supression_inscriptions_archivees"  # unique code to represent this cron job

    @sentry_exceptions
    def do(self):
        # Redirect stdout and stderr to a buffer to capture the output of the
        # command. By returning it, django-cron will log it in the database.
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            call_command("supression_inscriptions_archivees")
        return buf.getvalue()

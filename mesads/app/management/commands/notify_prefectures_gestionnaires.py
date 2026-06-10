from django.core.management.base import BaseCommand

from mesads.app.services.notifications import notify_prefectures_gestionnaires


class Command(BaseCommand):
    help = (
        "Notifie les gestionnaires des prefectures en "
        "cas d'ADS pas complètes et vérifiées"
    )

    def handle(self, *args, **options):
        notify_prefectures_gestionnaires(
            progress=self.stdout.write,
        )

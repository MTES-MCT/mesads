from django.core.management.base import BaseCommand

from mesads.app.services.liste_attente import supression_inscriptions_archivees


class Command(BaseCommand):
    help = (
        "Supprime les inscriptions à la liste d'attente archivées depuis plus de 6 mois"
    )

    def handle(self, *args, **options):
        inscriptions_count = supression_inscriptions_archivees()
        self.stdout.write(
            f"{inscriptions_count} inscriptions archivées ont été supprimées."
        )

from pathlib import Path

from django.core.management.base import BaseCommand

from mesads.app.models import ADSManager
from mesads.app.services.import_ads import import_ads_from_excel
from mesads.users.models import User


class Command(BaseCommand):
    help = "Import ADS from excel file"

    def add_arguments(self, parser):
        parser.add_argument("-f", "--ads-file", required=True)
        parser.add_argument("--manager-id", required=True, help="ID du manager ADS")

    def handle(self, ads_file, manager_id, **opts):
        ads_manager = ADSManager.objects.get(id=manager_id)
        file = Path(ads_file)
        user = User.objects.get(email="antoine-j.michon@beta.gouv.fr")
        import_ads_from_excel(file, ads_manager, user)

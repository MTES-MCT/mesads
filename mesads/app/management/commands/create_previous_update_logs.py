from django.core.management.base import BaseCommand
from django.db.models import Count
from reversion.models import Version

from mesads.app.models import ADS, ADSManagerAdministrator, ADSUpdateLog


class Command(BaseCommand):
    help = "Import ADS from excel file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--departement", required=True, help="Numéro du département"
        )

    def create_for_ads_retrospectively(self, ads):
        latest_version = Version.objects.get_for_object(ads).first()
        if latest_version is None:
            return False

        user = latest_version.revision.user
        last_update = ads.last_update
        if not last_update or not user:
            return False
        update_log = ADSUpdateLog.create_for_ads(ads, user)
        ADSUpdateLog.objects.filter(pk=update_log.pk).update(update_at=last_update)
        return True

    def handle(self, departement, **opts):
        administrator = ADSManagerAdministrator.objects.filter(
            prefecture__numero=departement
        ).first()
        if not administrator:
            return

        nb_update_log_crees = 0
        nb_update_logs_non_cree = 0

        ads_without_update_logs = (
            ADS.objects.filter(ads_manager__administrator=administrator)
            .annotate(nb_update_logs=Count("ads_update_logs"))
            .filter(nb_update_logs=0)
        )
        self.stdout.write(f"Nb ADS sans update logs: {ads_without_update_logs.count()}")
        for ads in ads_without_update_logs:
            result = self.create_for_ads_retrospectively(ads)
            if result:
                nb_update_log_crees += 1
            else:
                nb_update_logs_non_cree += 1

        self.stdout.write(f"Nb update log créés {nb_update_log_crees}")
        self.stdout.write(f"Nb update log non créés {nb_update_logs_non_cree}")

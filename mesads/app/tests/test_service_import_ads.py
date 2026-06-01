from datetime import date
from pathlib import Path

import pytest

from mesads.app.models import ADS, ADSUser
from mesads.app.services.import_ads import import_ads_from_excel
from mesads.users.tests.factories import UserFactory

from .factories import (
    ADSManagerAdministratorFactory,
    ADSManagerFactory,
)

BASE_DIR = Path(__file__).resolve().parent
excel_path = BASE_DIR / "file_test_import.xlsx"

pytestmark = pytest.mark.django_db


def test_get_export_data_liste_attente():
    administrator = ADSManagerAdministratorFactory()
    commune = ADSManagerFactory(administrator=administrator, for_commune=True)

    ads = ADS.objects.create(ads_manager=commune, number="1", ads_in_use=False)

    assert ADS.objects.filter(ads_manager=commune).count() == 1

    user = UserFactory(email="test@test.com")

    import_ads_from_excel(excel_path, commune, user)

    assert ADS.objects.filter(ads_manager=commune).count() == 2
    ads.refresh_from_db()
    assert ads.adsuser_set.count() == 2
    assert ads.ads_in_use
    assert ads.ads_creation_date == date(1995, 11, 5)
    assert ads.ads_renew_date is None
    assert ads.attribution_date == date(2021, 12, 10)
    assert ads.immatriculation_plate == "GHJKD-01"
    assert not ads.accepted_cpam
    assert ads.vehicle_compatible_pmr
    assert ads.eco_vehicle
    assert ads.owner_name == "John Doe"
    assert ads.owner_siret == "1234567890100"
    assert ads.owner_phone == "0404040404"
    assert ads.owner_mobile == "0606060606"
    assert ads.owner_email == "johndoe@test.com"

    user = ads.adsuser_set.first()
    assert user.status == ADSUser.LOCATAIRE_GERANT
    assert user.name == "Jean Locataire"
    assert user.siret == "645457946315"
    assert user.license_number == "34548974"

    user = ads.adsuser_set.last()
    assert user.status == ADSUser.SALARIE
    assert user.name == "Jean Salarié"
    assert user.siret == ""
    assert user.license_number == "324568901"

    ads = ADS.objects.last()
    assert ads.adsuser_set.count() == 1
    assert ads.number == "2"
    assert ads.ads_in_use
    assert ads.ads_creation_date == date(2023, 10, 10)
    assert ads.ads_renew_date == date(2023, 10, 10)
    assert ads.attribution_date is None
    assert ads.immatriculation_plate == "HGDQJ-01"
    assert ads.accepted_cpam
    assert not ads.vehicle_compatible_pmr
    assert not ads.eco_vehicle
    assert ads.owner_name == "Jane Doe"
    assert ads.owner_siret == "98765432100"
    assert ads.owner_phone == "0505050505"
    assert ads.owner_mobile == "0707070707"
    assert ads.owner_email == "janedoe@test.com"

    user = ads.adsuser_set.first()
    assert user.status == ADSUser.TITULAIRE_EXPLOITANT
    assert user.name == ""
    assert user.siret == ""
    assert user.license_number == "123456789"

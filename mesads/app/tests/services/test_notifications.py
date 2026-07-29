from datetime import date, timedelta

import pytest
from django.utils import timezone

from mesads.app.services.notifications import notify_prefectures_gestionnaires
from mesads.users.tests.factories import UserFactory

from ...models import ADS, ADSUpdateLog, ADSUser
from ..factories import (
    ADSManagerAdministratorFactory,
    ADSManagerFactory,
    ADSManagerRequestFactory,
)

pytestmark = pytest.mark.django_db


def test_notify_verification_no_ads(mailoutbox):
    administrator = ADSManagerAdministratorFactory()
    manager_prefecture = ADSManagerFactory(
        administrator=administrator, for_object=administrator.prefecture
    )
    manager_commune = ADSManagerFactory(administrator=administrator, for_commune=True)
    manager_epci = ADSManagerFactory(administrator=administrator, for_epci=True)
    ADSManagerRequestFactory(ads_manager=manager_prefecture, user=UserFactory())
    ADSManagerRequestFactory(ads_manager=manager_commune, user=UserFactory())
    ADSManagerRequestFactory(ads_manager=manager_epci, user=UserFactory())
    administrator.notify_verification_enabled = True
    administrator.save()
    notify_prefectures_gestionnaires()
    assert len(mailoutbox) == 0


def test_notify_verification_ads_complete(mailoutbox):
    administrator = ADSManagerAdministratorFactory()
    manager_prefecture = ADSManagerFactory(
        administrator=administrator, for_object=administrator.prefecture
    )
    request_pref = ADSManagerRequestFactory(
        ads_manager=manager_prefecture, user=UserFactory()
    )
    ads = ADS.objects.create(
        ads_manager=manager_prefecture,
        ads_creation_date=date(2013, 1, 1),
        number="1",
        ads_in_use=True,
        attribution_date=date(2013, 1, 1),
        accepted_cpam=True,
        immatriculation_plate="HDHSKHKD",
        vehicle_compatible_pmr=False,
        eco_vehicle=False,
        owner_name="Jean Taxi",
        owner_siret="1234567890123",
        owner_phone="0404040404",
        owner_mobile="0606060606",
        owner_email="jean@test.com",
    )
    ADSUser.objects.create(
        ads=ads, status=ADSUser.TITULAIRE_EXPLOITANT, license_number="01234567"
    )
    ADSUpdateLog.create_for_ads(ads, request_pref.user)
    administrator.notify_verification_enabled = True
    administrator.save()
    notify_prefectures_gestionnaires()
    assert len(mailoutbox) == 0


def test_notify_verification_ads_outdated(mailoutbox):
    administrator = ADSManagerAdministratorFactory()
    manager_prefecture = ADSManagerFactory(
        administrator=administrator, for_object=administrator.prefecture
    )
    request_pref = ADSManagerRequestFactory(
        ads_manager=manager_prefecture, user=UserFactory()
    )
    ads = ADS.objects.create(
        ads_manager=manager_prefecture,
        ads_creation_date=date(2013, 1, 1),
        number="1",
        ads_in_use=True,
        attribution_date=date(2013, 1, 1),
        accepted_cpam=True,
        immatriculation_plate="HDHSKHKD",
        vehicle_compatible_pmr=False,
        eco_vehicle=False,
        owner_name="Jean Taxi",
        owner_siret="1234567890123",
        owner_phone="0404040404",
        owner_mobile="0606060606",
        owner_email="jean@test.com",
    )
    ADSUser.objects.create(
        ads=ads, status=ADSUser.TITULAIRE_EXPLOITANT, license_number="01234567"
    )
    ads_log = ADSUpdateLog.create_for_ads(ads, request_pref.user)
    ADSUpdateLog.objects.filter(pk=ads_log.pk).update(
        update_at=timezone.now() - timedelta(days=365)
    )
    administrator.notify_verification_enabled = True
    administrator.save()
    notify_prefectures_gestionnaires()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].recipients() == [request_pref.user.email]


def test_notify_verification_ads_incomplete(mailoutbox):
    administrator = ADSManagerAdministratorFactory()
    manager_prefecture = ADSManagerFactory(
        administrator=administrator, for_object=administrator.prefecture
    )
    request_pref = ADSManagerRequestFactory(
        ads_manager=manager_prefecture, user=UserFactory()
    )
    ads = ADS.objects.create(
        ads_manager=manager_prefecture,
        ads_creation_date=date(2013, 1, 1),
        number="1",
        ads_in_use=True,
        attribution_date=date(2013, 1, 1),
        accepted_cpam=True,
        vehicle_compatible_pmr=False,
        eco_vehicle=False,
        owner_name="Jean Taxi",
        owner_siret="1234567890123",
        owner_phone="0404040404",
        owner_mobile="0606060606",
        owner_email="jean@test.com",
    )
    ADSUser.objects.create(
        ads=ads, status=ADSUser.TITULAIRE_EXPLOITANT, license_number="01234567"
    )
    ADSUpdateLog.create_for_ads(ads, request_pref.user)
    administrator.notify_verification_enabled = True
    administrator.save()
    notify_prefectures_gestionnaires()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].recipients() == [request_pref.user.email]

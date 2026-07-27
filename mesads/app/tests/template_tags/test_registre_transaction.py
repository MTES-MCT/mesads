import logging
from datetime import date

from django.urls import reverse

from mesads.app.models import EntreeRegistreTransaction
from mesads.app.templatetags.registre_transaction import modification_url
from mesads.users.unittest import ClientTestCase as BaseClientTestCase

from ..factories import (
    ADSFactory,
    ADSManagerFactory,
)


class TestTagUrlTransaction(BaseClientTestCase):
    def setUp(self):
        super().setUp()
        self.client, self.user = self.create_client()
        self.ads_manager = ADSManagerFactory(for_commune=True)
        self.old_ads = ADSFactory(
            ads_manager=self.ads_manager, ads_creation_date=date(2013, 1, 1)
        )
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Enable logging
        logging.disable(logging.NOTSET)

    def test_get_brouillon_no_document_complets(self):
        entree = EntreeRegistreTransaction.objects.create(ads=self.old_ads)

        url = modification_url(entree)

        assert url == reverse(
            "app.transaction-documents",
            kwargs={
                "entree_id": entree.id,
                "manager_id": self.ads_manager.id,
            },
        )

    def test_get_brouillon_document_complets(self):
        entree = EntreeRegistreTransaction.objects.create(
            ads=self.old_ads, documents_complet=True
        )

        url = modification_url(entree)

        assert url == reverse(
            "app.transaction-enregistrement",
            kwargs={
                "entree_id": entree.id,
                "manager_id": self.ads_manager.id,
            },
        )

    def test_get_enregistree(self):
        entree = EntreeRegistreTransaction.objects.create(
            ads=self.old_ads, statut=EntreeRegistreTransaction.ENREGISTREE
        )

        url = modification_url(entree)

        assert url == reverse(
            "app.transaction-edition",
            kwargs={
                "entree_id": entree.id,
                "manager_id": self.ads_manager.id,
            },
        )

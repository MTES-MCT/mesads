import http
import logging
from datetime import date

from django.urls import reverse

from mesads.app.models import EntreeRegistreTransaction
from mesads.users.unittest import ClientTestCase as BaseClientTestCase

from ..factories import (
    ADSFactory,
    ADSManagerFactory,
    ADSManagerRequestFactory,
)


class ClientTestCase(BaseClientTestCase):
    def setUp(self):
        super().setUp()
        self.client, self.user = self.create_client()
        self.ads_manager = ADSManagerFactory(for_commune=True)
        self.other_manager = ADSManagerFactory(for_commune=True)
        self.ads_manager_request = ADSManagerRequestFactory(
            user=self.user, ads_manager=self.ads_manager
        )
        self.old_ads = ADSFactory(
            ads_manager=self.ads_manager, ads_creation_date=date(2013, 1, 1)
        )
        self.new_ads = ADSFactory(
            ads_manager=self.ads_manager, ads_creation_date=date(2016, 1, 1)
        )
        self.ads_other_manager = ADSFactory(
            ads_manager=self.other_manager, ads_creation_date=date(2013, 1, 1)
        )
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Enable logging
        logging.disable(logging.NOTSET)


class TestListeRegistreTransactions(ClientTestCase):
    def test_get_list(self):
        EntreeRegistreTransaction.objects.create(
            ads=self.old_ads, statut=EntreeRegistreTransaction.ENREGISTREE
        )
        EntreeRegistreTransaction.objects.create(
            ads=self.old_ads, statut=EntreeRegistreTransaction.ENREGISTREE
        )
        EntreeRegistreTransaction.objects.create(
            ads=self.old_ads, statut=EntreeRegistreTransaction.ENREGISTREE
        )

        entree_autre = EntreeRegistreTransaction.objects.create(
            ads=self.ads_other_manager, statut=EntreeRegistreTransaction.ENREGISTREE
        )

        response = self.client.get(
            reverse("app.transaction-liste", kwargs={"manager_id": self.ads_manager.id})
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertQuerySetEqual(
            response.context["entrees"],
            EntreeRegistreTransaction.objects.filter(
                ads__ads_manager=self.ads_manager
            ).order_by("-date_transaction"),
        )
        self.assertTemplateUsed(
            response, "pages/ads_register/registre_transactions/transaction_liste.html"
        )
        self.assertNotIn(entree_autre, list(response.context["entrees"]))


class TestSelectionADS(ClientTestCase):
    def test_get_selection_ads(self):
        response = self.client.get(
            reverse(
                "app.transaction-choix-ads", kwargs={"manager_id": self.ads_manager.id}
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(
            response,
            "pages/ads_register/registre_transactions/transaction_selection_ads.html",
        )
        form = response.context["form"]
        self.assertIn(self.old_ads, list(form.fields["ads"].queryset))
        self.assertNotIn(self.new_ads, list(form.fields["ads"].queryset))
        self.assertNotIn(self.ads_other_manager, list(form.fields["ads"].queryset))

    def test_post_selection_ads_ok(self):
        response = self.client.post(
            reverse(
                "app.transaction-choix-ads", kwargs={"manager_id": self.ads_manager.id}
            ),
            data={"ads": self.old_ads.id},
        )

        self.assertEqual(EntreeRegistreTransaction.objects.count(), 1)
        entree = EntreeRegistreTransaction.objects.last()
        self.assertEqual(entree.ads, self.old_ads)
        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-documents",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )

    def test_post_selection_ads_not_ok(self):
        response = self.client.post(
            reverse(
                "app.transaction-choix-ads", kwargs={"manager_id": self.ads_manager.id}
            ),
            data={"ads": self.new_ads.id},
        )
        self.assertEqual(EntreeRegistreTransaction.objects.count(), 0)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(
            response.context["form"].errors["ads"],
            [
                (
                    "Sélectionnez un choix valide. "
                    "Ce choix ne fait pas partie de ceux disponibles."
                )
            ],
        )


class TestSelectionDocument(ClientTestCase):
    def setUp(self):
        super().setUp()
        self.entree = EntreeRegistreTransaction.objects.create(
            ads=self.old_ads, statut=EntreeRegistreTransaction.BROUILLON
        )

    def test_get_selection_document(self):
        response = self.client.get(
            reverse(
                "app.transaction-documents",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": self.entree.id},
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(
            response,
            "pages/ads_register/registre_transactions/transaction_documents.html",
        )

    def test_post_selection_document_draft_ok(self):
        entree = self.entree
        response = self.client.post(
            reverse(
                "app.transaction-documents",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            data={
                "demande_cession": "on",
                "justificatif_exploitation": "on",
                "piece_identite": "on",
                "justificatif_montant": "on",
                "kbis_ou_siren": "on",
                "attestation_aptitude_professionnelle": "on",
                "justificatif_liquidation_judiciaire": "on",
                "autres_documents": "on",
                "autres_documents_description": "Autre document",
                "documents_complet": "false",
                "action": "draft",
            },
        )
        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-documents",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        entree.refresh_from_db()
        assert entree.demande_cession
        assert entree.justificatif_exploitation
        assert entree.piece_identite
        assert entree.justificatif_montant
        assert entree.kbis_ou_siren
        assert entree.attestation_aptitude_professionnelle
        assert entree.justificatif_liquidation_judiciaire
        assert entree.autres_documents
        assert entree.autres_documents_description == "Autre document"
        assert not entree.documents_complet

    def test_post_selection_document_validate_ok(self):
        entree = self.entree
        response = self.client.post(
            reverse(
                "app.transaction-documents",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            data={
                "demande_cession": "on",
                "justificatif_exploitation": "on",
                "piece_identite": "on",
                "justificatif_montant": "on",
                "kbis_ou_siren": "on",
                "attestation_aptitude_professionnelle": "on",
                "justificatif_liquidation_judiciaire": "on",
                "autres_documents": "on",
                "autres_documents_description": "Autre document",
                "documents_complet": "true",
                "action": "validate",
            },
        )
        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-enregistrement",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        entree.refresh_from_db()
        assert entree.demande_cession
        assert entree.justificatif_exploitation
        assert entree.piece_identite
        assert entree.justificatif_montant
        assert entree.kbis_ou_siren
        assert entree.attestation_aptitude_professionnelle
        assert entree.justificatif_liquidation_judiciaire
        assert entree.autres_documents
        assert entree.autres_documents_description == "Autre document"
        assert entree.documents_complet


class TestEnregistrement(ClientTestCase):
    def setUp(self):
        super().setUp()
        self.entree = EntreeRegistreTransaction.objects.create(
            ads=self.old_ads,
            statut=EntreeRegistreTransaction.BROUILLON,
            documents_complet=True,
        )

    def test_get_enregistrement(self):
        response = self.client.get(
            reverse(
                "app.transaction-enregistrement",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": self.entree.id},
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(
            response,
            "pages/ads_register/registre_transactions/transaction_enregistrement.html",
        )

    def test_post_enregistrement_draft_ok(self):
        entree = self.entree
        response = self.client.post(
            reverse(
                "app.transaction-enregistrement",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            data={
                "date_transaction": date.today(),
                "montant_transaction": 8000,
                "ancien_exploitant": "Jane taxi",
                "nouvel_exploitant": "John taxi",
                "siret_nouvel_exploitant": "12345678912345",
                "action": "draft",
            },
        )

        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-enregistrement",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        entree.refresh_from_db()
        assert entree.date_transaction == date.today()
        assert entree.montant_transaction == 8000
        assert entree.ancien_exploitant == "Jane taxi"
        assert entree.nouvel_exploitant == "John taxi"
        assert entree.siret_nouvel_exploitant == "12345678912345"

    def test_post_enregistrement_validate_ok(self):
        entree = self.entree
        response = self.client.post(
            reverse(
                "app.transaction-enregistrement",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            data={
                "date_transaction": date.today(),
                "montant_transaction": 8000,
                "ancien_exploitant": "Jane taxi",
                "nouvel_exploitant": "John taxi",
                "siret_nouvel_exploitant": "12345678912345",
                "action": "validate",
            },
        )

        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-confirmation",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        entree.refresh_from_db()
        assert entree.date_transaction == date.today()
        assert entree.montant_transaction == 8000
        assert entree.ancien_exploitant == "Jane taxi"
        assert entree.nouvel_exploitant == "John taxi"
        assert entree.siret_nouvel_exploitant == "12345678912345"
        assert entree.statut == EntreeRegistreTransaction.ENREGISTREE


class TestConfirmation(ClientTestCase):
    def test_get_confirmation(self):
        entree = EntreeRegistreTransaction.objects.create(
            ads=self.old_ads,
            statut=EntreeRegistreTransaction.ENREGISTREE,
            documents_complet=True,
        )
        response = self.client.get(
            reverse(
                "app.transaction-confirmation",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": entree.id},
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(
            response,
            "pages/ads_register/registre_transactions/transaction_confirmation.html",
        )


class TestEdition(ClientTestCase):
    def setUp(self):
        super().setUp()
        self.entree = EntreeRegistreTransaction.objects.create(
            ads=self.old_ads,
            statut=EntreeRegistreTransaction.ENREGISTREE,
            documents_complet=True,
        )

    def test_get_edition(self):
        response = self.client.get(
            reverse(
                "app.transaction-edition",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": self.entree.id},
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(
            response,
            "pages/ads_register/registre_transactions/transaction_edition.html",
        )

    def test_post_edition_ok(self):
        entree = self.entree
        response = self.client.post(
            reverse(
                "app.transaction-edition",
                kwargs={"manager_id": self.ads_manager.id, "entree_id": self.entree.id},
            ),
            data={
                "ads": entree.ads.id,
                "date_transaction": date.today(),
                "montant_transaction": 8000,
                "ancien_exploitant": "Jane taxi",
                "nouvel_exploitant": "John taxi",
                "siret_nouvel_exploitant": "12345678912345",
                "action": "validate",
            },
        )

        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-liste",
                kwargs={"manager_id": self.ads_manager.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        entree.refresh_from_db()
        assert entree.date_transaction == date.today()
        assert entree.montant_transaction == 8000
        assert entree.ancien_exploitant == "Jane taxi"
        assert entree.nouvel_exploitant == "John taxi"
        assert entree.siret_nouvel_exploitant == "12345678912345"


class TestCreation(ClientTestCase):
    def test_get_creation(self):
        response = self.client.get(
            reverse(
                "app.transaction-creation",
                kwargs={"manager_id": self.ads_manager.id},
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(
            response,
            "pages/ads_register/registre_transactions/transaction_creation.html",
        )

    def test_post_creation_ok(self):
        response = self.client.post(
            reverse(
                "app.transaction-creation",
                kwargs={"manager_id": self.ads_manager.id},
            ),
            data={
                "ads": self.old_ads.id,
                "date_transaction": date.today(),
                "montant_transaction": 8000,
                "ancien_exploitant": "Jane taxi",
                "nouvel_exploitant": "John taxi",
                "siret_nouvel_exploitant": "12345678912345",
                "action": "validate",
            },
        )

        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.transaction-liste",
                kwargs={"manager_id": self.ads_manager.id},
            ),
            status_code=http.HTTPStatus.FOUND,
            target_status_code=http.HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        assert EntreeRegistreTransaction.objects.count() == 1
        entree = EntreeRegistreTransaction.objects.last()
        assert entree.ads == self.old_ads
        assert entree.date_transaction == date.today()
        assert entree.montant_transaction == 8000
        assert entree.ancien_exploitant == "Jane taxi"
        assert entree.nouvel_exploitant == "John taxi"
        assert entree.siret_nouvel_exploitant == "12345678912345"

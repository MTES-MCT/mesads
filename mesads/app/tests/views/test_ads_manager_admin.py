from datetime import date, datetime, timedelta
from http import HTTPStatus

import pytest
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail
from django.urls import reverse

from mesads.app.models import (
    ADS,
    ADSManager,
    ADSManagerRequest,
    DemandeGestionPrefecture,
)
from mesads.unittest import ClientTestCase

from ..factories import DemandeGestionPrefectureFactory


class TestADSManagerAdminRequestsView(ClientTestCase):
    def setUp(self):
        super().setUp()
        self.ads_manager_request = ADSManagerRequest.objects.create(
            user=self.create_user(),
            ads_manager=self.ads_manager_city35,
            statut=ADSManagerRequest.EN_ATTENTE,
        )

    def test_permissions(self):
        for client_name, client, expected_status in (
            ("admin", self.admin_client, 200),
            ("anonymous", self.anonymous_client, 404),
            ("auth", self.auth_client, 404),
            ("ads_manager 35", self.ads_manager_city35_client, 404),
            ("ads_manager_admin 35", self.ads_manager_administrator_35_client, 200),
        ):
            with self.subTest(client_name=client_name, expected_status=expected_status):
                resp = client.get(
                    f"/espace-prefecture/{self.ads_manager_administrator_35.prefecture_id}/demandes-gestion/"
                )
                self.assertEqual(resp.status_code, expected_status)

    def test_sort(self):
        for ads_manager in ADSManager.objects.all():
            ADSManagerRequest.objects.create(
                user=self.create_user(),
                ads_manager=ads_manager,
                statut=ADSManagerRequest.EN_ATTENTE,
            )
        resp = self.ads_manager_administrator_35_client.get(
            f"/espace-prefecture/{self.ads_manager_administrator_35.prefecture_id}/demandes-gestion/",
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.ads_manager_administrator_35_client.get(
            f"/espace-prefecture/{self.ads_manager_administrator_35.prefecture_id}/demandes-gestion/?sort=name",
        )
        self.assertEqual(resp.status_code, 200)


class TestExportPrefecture(ClientTestCase):
    def test_permissions(self):
        for client_name, client, expected_status in (
            ("admin", self.admin_client, 200),
            ("anonymous", self.anonymous_client, 404),
            ("auth", self.auth_client, 404),
            ("ads_manager 35", self.ads_manager_city35_client, 404),
            ("ads_manager_admin 35", self.ads_manager_administrator_35_client, 200),
        ):
            with self.subTest(client_name=client_name, expected_status=expected_status):
                resp = client.get(
                    f"/registre_ads/prefectures/{self.ads_manager_administrator_35.prefecture.id}/export"
                )
                self.assertEqual(resp.status_code, expected_status)

    def test_get_404(self):
        resp = self.ads_manager_administrator_35_client.get(
            "/registre_ads/prefectures/9999/export"
        )
        self.assertEqual(resp.status_code, 404)

    def test_export(self):
        ADS.objects.create(
            number="1",
            ads_manager=self.ads_manager_city35,
            accepted_cpam=True,
            ads_in_use=True,
        )
        ADS.objects.create(
            number="2",
            ads_manager=self.ads_manager_city35,
            ads_in_use=True,
        )
        ADS.objects.create(
            number="3",
            ads_manager=self.ads_manager_city35,
            ads_creation_date=datetime.now().date(),
            ads_in_use=True,
        )

        resp = self.ads_manager_administrator_35_client.get(
            f"/registre_ads/prefectures/{self.ads_manager_administrator_35.prefecture.id}/export"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_export_no_ads_declared(self):
        """Similar to test_export, but with no_ads_declared for the ADSManager."""
        self.ads_manager_city35.no_ads_declared = True
        self.ads_manager_city35.save()

        ADS.objects.create(
            number="1",
            ads_manager=self.ads_manager_city35,
            accepted_cpam=True,
            ads_in_use=True,
        )
        resp = self.ads_manager_administrator_35_client.get(
            f"/registre_ads/prefectures/{self.ads_manager_administrator_35.prefecture.id}/export"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_export_epci_delegate(self):
        """Similar to test_export, but with epci_delegate for the ADSManager."""
        self.ads_manager_city35.epci_delegate = self.fixtures_epci[0]
        self.ads_manager_city35.save()

        ADS.objects.create(
            number="1",
            ads_manager=self.ads_manager_city35,
            accepted_cpam=True,
            ads_in_use=True,
        )
        resp = self.ads_manager_administrator_35_client.get(
            f"/registre_ads/prefectures/{self.ads_manager_administrator_35.prefecture.id}/export"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


class TestADSManagerAdminUpdatesView(ClientTestCase):
    def test_updates(self):
        resp = self.ads_manager_administrator_35_client.get(
            f"/espace-prefecture/{self.ads_manager_administrator_35.prefecture.id}/changements"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["updates"], [])

        # Create ADS, and update it
        ads = ADS.objects.create(
            number="12346", ads_manager=self.ads_manager_city35, ads_in_use=True
        )
        resp = self.ads_manager_administrator_35_client.post(
            f"/registre_ads/gestion/{self.ads_manager_city35.id}/ads/{ads.id}",
            {
                "number": ads.id,
                "certify": "true",
                "ads_in_use": "false",
            },
        )
        self.assertEqual(resp.status_code, 302)

        resp = self.ads_manager_administrator_35_client.get(
            f"/espace-prefecture/{self.ads_manager_administrator_35.prefecture.id}/changements"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["updates"]), 1)
        self.assertEqual(len(resp.context["updates"][0]["history_entries"]), 1)

        # # Update the same ADS again
        resp = self.ads_manager_administrator_35_client.post(
            f"/registre_ads/gestion/{self.ads_manager_city35.id}/ads/{ads.id}",
            {
                "number": ads.id,
                "certify": "true",
                "ads_in_use": "true",
            },
        )
        self.assertEqual(resp.status_code, 302)

        resp = self.ads_manager_administrator_35_client.get(
            f"/espace-prefecture/{self.ads_manager_administrator_35.prefecture.id}/changements"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["updates"]), 1)
        self.assertEqual(len(resp.context["updates"][0]["history_entries"]), 2)


class TestAdsManagerAdministratorView(ClientTestCase):
    def test_get_context(self):
        response = self.ads_manager_administrator_35_client.get(
            reverse(
                "app.ads-manager-admin.gestionnaires",
                kwargs={
                    "prefecture_id": self.ads_manager_administrator_35.prefecture.id
                },
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            set([m.id for m in response.context["ads_managers"]]),
            set(
                ADSManager.objects.filter(
                    administrator=self.ads_manager_administrator_35
                ).values_list("id", flat=True)
            ),
        )

    def test_post_to_become_gestionnaire(self):
        response = self.ads_manager_administrator_35_client.post(
            reverse(
                "app.ads-manager-admin.gestionnaires",
                kwargs={
                    "prefecture_id": self.ads_manager_administrator_35.prefecture.id
                },
            ),
            data={"ads_manager_id": self.ads_manager_city35.id},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            ADSManagerRequest.objects.filter(
                user=self.ads_manager_administrator_35_user,
                ads_manager=self.ads_manager_city35,
                statut=ADSManagerRequest.ACCEPTE,
            ).count(),
            1,
        )


class TestDemandeGestionPrefecture(ClientTestCase):
    def setUp(self):
        super().setUp()
        self.client, self.user = self.create_client()
        self.administrator = self.ads_manager_administrator_35
        self.prefecture = self.ads_manager_administrator_35.prefecture

    def test_get_page_demande_gestion_prefecture(self):
        response = self.client.get(
            reverse("app.ads-manager-admin.demande_gestion_prefecture")
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(
            response, "pages/ads_register/demande_gestion_prefecture.html"
        )

    def test_post_page_demande_gestion_prefecture(self):
        assert (
            DemandeGestionPrefecture.objects.filter(
                user=self.user, administrator=self.administrator
            ).count()
            == 0
        )
        response = self.client.post(
            reverse("app.ads-manager-admin.demande_gestion_prefecture"),
            {
                "administrator": self.administrator.id,
                "statut_user": "Agent de contrôle",
            },
        )
        self.assertRedirects(
            response,
            expected_url=reverse(
                "app.homepage",
            ),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK,
            fetch_redirect_response=True,
        )
        assert (
            DemandeGestionPrefecture.objects.filter(
                user=self.user, administrator=self.administrator
            ).count()
            == 1
        )

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(
            email.subject, f"Mes ADS : Demande d'accès préfecture de {self.user.email}"
        )
        self.assertEqual(email.to, [settings.MESADS_CONTACT_EMAIL])


# --- ADSManagerRequestsChangeView ---------------------------------------------


@pytest.fixture
def administrateur_client(ads_manager_administrator, user_factory, client_factory):
    """Client connecté en tant que gestionnaire de la préfecture."""
    administrateur = user_factory()
    DemandeGestionPrefectureFactory(
        user=administrateur,
        administrator=ads_manager_administrator,
        statut=DemandeGestionPrefecture.ACCEPTE,
    )
    return client_factory(administrateur)


@pytest.fixture
def demande_factory(
    ads_manager_administrator, ads_manager_factory, ads_manager_request_factory
):
    """Demande d'accès sur une administration de la préfecture du fixture
    ads_manager_administrator."""

    def _demande_factory(**kwargs):
        return ads_manager_request_factory(
            manager_=ads_manager_factory(administrator=ads_manager_administrator),
            **kwargs,
        )

    return _demande_factory


def url_change(demande, action):
    return reverse(
        "app.ads-manager-admin-request-change",
        kwargs={
            "prefecture_id": demande.ads_manager.administrator.prefecture_id,
            "ads_manager_request_id": demande.id,
            "action": action,
        },
    )


def url_liste(ads_manager_administrator):
    return reverse(
        "app.ads-manager-admin.requests",
        kwargs={"prefecture_id": ads_manager_administrator.prefecture_id},
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "statut", [ADSManagerRequest.EN_ATTENTE, ADSManagerRequest.REFUSE]
)
def test_change_autoriser(
    administrateur_client,
    ads_manager_administrator,
    demande_factory,
    mailoutbox,
    statut,
):
    demande = demande_factory(statut=statut)

    response = administrateur_client.post(url_change(demande, "autoriser"))

    assert response.status_code == 302
    assert response.url == url_liste(ads_manager_administrator)
    demande.refresh_from_db()
    assert demande.statut == ADSManagerRequest.ACCEPTE
    assert demande.accepted_at == date.today()
    assert demande.expire_at == date.today() + relativedelta(years=2)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [demande.user.email]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "statut", [ADSManagerRequest.ACCEPTE, ADSManagerRequest.EXPIRE]
)
def test_change_autoriser_statut_invalide(
    administrateur_client, demande_factory, mailoutbox, statut
):
    demande = demande_factory(statut=statut)

    response = administrateur_client.post(url_change(demande, "autoriser"))

    assert response.status_code == 400
    demande.refresh_from_db()
    assert demande.statut == statut
    assert len(mailoutbox) == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "statut",
    [
        ADSManagerRequest.EN_ATTENTE,  # refus
        ADSManagerRequest.ACCEPTE,  # révocation
    ],
)
def test_change_refuser(
    administrateur_client,
    ads_manager_administrator,
    demande_factory,
    mailoutbox,
    statut,
):
    demande = demande_factory(statut=statut)

    response = administrateur_client.post(url_change(demande, "refuser"))

    assert response.status_code == 302
    assert response.url == url_liste(ads_manager_administrator)
    demande.refresh_from_db()
    assert demande.statut == ADSManagerRequest.REFUSE
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [demande.user.email]


@pytest.mark.django_db
def test_change_renouveler_acceptee_bientot_expiree(
    administrateur_client, ads_manager_administrator, demande_factory, mailoutbox
):
    expire_at = date.today() + timedelta(days=15)
    demande = demande_factory(
        statut=ADSManagerRequest.ACCEPTE,
        expire_at=expire_at,
        demande_renouvellement=True,
        notified=True,
    )

    response = administrateur_client.post(url_change(demande, "renouveler"))

    assert response.status_code == 302
    assert response.url == url_liste(ads_manager_administrator)
    demande.refresh_from_db()
    assert demande.statut == ADSManagerRequest.ACCEPTE
    # Les droits sont prolongés à partir de la date d'expiration actuelle
    assert demande.expire_at == expire_at + relativedelta(years=2)
    assert demande.last_renew == date.today()
    assert demande.demande_renouvellement is False
    assert demande.notified is False
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [demande.user.email]


@pytest.mark.django_db
def test_change_renouveler_expiree(administrateur_client, demande_factory):
    demande = demande_factory(
        statut=ADSManagerRequest.EXPIRE,
        expire_at=date.today() - timedelta(days=30),
        demande_renouvellement=True,
        notified=True,
    )

    response = administrateur_client.post(url_change(demande, "renouveler"))

    assert response.status_code == 302
    demande.refresh_from_db()
    assert demande.statut == ADSManagerRequest.ACCEPTE
    # Une demande expirée repart de la date du jour, pas de l'ancienne expiration
    assert demande.expire_at == date.today() + relativedelta(years=2)
    assert demande.last_renew == date.today()
    assert demande.demande_renouvellement is False
    assert demande.notified is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "statut, expire_dans_jours, demande_renouvellement",
    [
        # Pas de demande de renouvellement de l'utilisateur
        (ADSManagerRequest.ACCEPTE, 15, False),
        (ADSManagerRequest.EXPIRE, -30, False),
        # Acceptée mais expiration trop lointaine : pas encore renouvelable
        (ADSManagerRequest.ACCEPTE, 365, True),
        # Statuts non renouvelables
        (ADSManagerRequest.EN_ATTENTE, None, True),
        (ADSManagerRequest.REFUSE, None, True),
    ],
)
def test_change_renouveler_invalide(
    administrateur_client,
    demande_factory,
    statut,
    expire_dans_jours,
    demande_renouvellement,
):
    expire_at = (
        date.today() + timedelta(days=expire_dans_jours)
        if expire_dans_jours is not None
        else None
    )
    demande = demande_factory(
        statut=statut,
        expire_at=expire_at,
        demande_renouvellement=demande_renouvellement,
    )

    response = administrateur_client.post(url_change(demande, "renouveler"))

    assert response.status_code == 400
    demande.refresh_from_db()
    assert demande.statut == statut
    assert demande.expire_at == expire_at
    assert demande.last_renew is None


@pytest.mark.django_db
def test_change_action_invalide(administrateur_client, demande_factory):
    demande = demande_factory(statut=ADSManagerRequest.EN_ATTENTE)

    response = administrateur_client.post(url_change(demande, "xxx"))

    assert response.status_code == 400
    demande.refresh_from_db()
    assert demande.statut == ADSManagerRequest.EN_ATTENTE


@pytest.mark.django_db
def test_change_demande_inexistante(administrateur_client, ads_manager_administrator):
    url = reverse(
        "app.ads-manager-admin-request-change",
        kwargs={
            "prefecture_id": ads_manager_administrator.prefecture_id,
            "ads_manager_request_id": 999999,
            "action": "autoriser",
        },
    )

    response = administrateur_client.post(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_change_demande_autre_prefecture(
    administrateur_client,
    ads_manager_administrator,
    ads_manager_request_factory,
):
    """Un gestionnaire de préfecture ne peut pas modifier une demande d'une autre
    préfecture en mettant son propre prefecture_id dans l'URL."""
    demande_autre_prefecture = ads_manager_request_factory(
        statut=ADSManagerRequest.EN_ATTENTE
    )
    url = reverse(
        "app.ads-manager-admin-request-change",
        kwargs={
            "prefecture_id": ads_manager_administrator.prefecture_id,
            "ads_manager_request_id": demande_autre_prefecture.id,
            "action": "autoriser",
        },
    )

    response = administrateur_client.post(url)

    assert response.status_code == 404
    demande_autre_prefecture.refresh_from_db()
    assert demande_autre_prefecture.statut == ADSManagerRequest.EN_ATTENTE


@pytest.mark.django_db
def test_change_permissions(client, client_factory, user_factory, demande_factory):
    demande = demande_factory(statut=ADSManagerRequest.EN_ATTENTE)
    url = url_change(demande, "autoriser")

    # Anonyme
    assert client.post(url).status_code == 404
    # Utilisateur connecté sans droit sur la préfecture
    assert client_factory(user_factory()).post(url).status_code == 404
    # Le demandeur lui-même ne peut pas valider sa propre demande
    assert client_factory(demande.user).post(url).status_code == 404

    demande.refresh_from_db()
    assert demande.statut == ADSManagerRequest.EN_ATTENTE


@pytest.mark.django_db
def test_change_get_non_autorise(administrateur_client, demande_factory):
    demande = demande_factory(statut=ADSManagerRequest.EN_ATTENTE)

    response = administrateur_client.get(url_change(demande, "autoriser"))

    assert response.status_code == 405


# --- Boutons d'action dans ads_manager_admin_requests.html -------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "statut, expire_dans_jours, demande_renouvellement, actions_attendues",
    [
        (ADSManagerRequest.EN_ATTENTE, None, False, {"autoriser", "refuser"}),
        (ADSManagerRequest.REFUSE, None, False, {"autoriser"}),
        (ADSManagerRequest.ACCEPTE, 365, False, {"refuser"}),
        (ADSManagerRequest.ACCEPTE, 365, True, {"refuser"}),
        (ADSManagerRequest.ACCEPTE, 15, False, {"refuser"}),
        (ADSManagerRequest.ACCEPTE, 15, True, {"refuser", "renouveler"}),
        (ADSManagerRequest.EXPIRE, -30, False, set()),
        (ADSManagerRequest.EXPIRE, -30, True, {"renouveler"}),
    ],
)
def test_liste_boutons_actions(
    administrateur_client,
    ads_manager_administrator,
    demande_factory,
    statut,
    expire_dans_jours,
    demande_renouvellement,
    actions_attendues,
):
    expire_at = (
        date.today() + timedelta(days=expire_dans_jours)
        if expire_dans_jours is not None
        else None
    )
    demande = demande_factory(
        statut=statut,
        expire_at=expire_at,
        demande_renouvellement=demande_renouvellement,
    )

    response = administrateur_client.get(url_liste(ads_manager_administrator))

    assert response.status_code == 200
    content = response.content.decode()
    for action in ("autoriser", "refuser", "renouveler"):
        assert (url_change(demande, action) in content) == (
            action in actions_attendues
        ), action
    if expire_at:
        assert expire_at.strftime("%d/%m/%Y") in content


@pytest.mark.django_db
def test_liste_filtre_id(
    administrateur_client, ads_manager_administrator, demande_factory
):
    demande = demande_factory(statut=ADSManagerRequest.EN_ATTENTE)
    autre_demande = demande_factory(statut=ADSManagerRequest.EN_ATTENTE)

    response = administrateur_client.get(
        url_liste(ads_manager_administrator), {"id": demande.id}
    )

    assert response.status_code == 200
    assert list(response.context["ads_manager_requests"]) == [demande]
    assert response.context["selected_id"] == str(demande.id)
    assert autre_demande not in response.context["ads_manager_requests"]


@pytest.mark.django_db
def test_liste_filtre_id_autre_prefecture(
    administrateur_client, ads_manager_administrator, ads_manager_request_factory
):
    demande_autre_prefecture = ads_manager_request_factory(
        statut=ADSManagerRequest.EN_ATTENTE
    )

    response = administrateur_client.get(
        url_liste(ads_manager_administrator), {"id": demande_autre_prefecture.id}
    )

    assert response.status_code == 200
    assert list(response.context["ads_manager_requests"]) == []


@pytest.mark.django_db
@pytest.mark.parametrize("valeur", ["", "abc", "-1"])
def test_liste_filtre_id_invalide_ignore(
    administrateur_client, ads_manager_administrator, demande_factory, valeur
):
    demandes = {
        demande_factory(statut=ADSManagerRequest.EN_ATTENTE),
        demande_factory(statut=ADSManagerRequest.EN_ATTENTE),
    }

    response = administrateur_client.get(
        url_liste(ads_manager_administrator), {"id": valeur}
    )

    assert response.status_code == 200
    assert set(response.context["ads_manager_requests"]) == demandes
    assert "selected_id" not in response.context

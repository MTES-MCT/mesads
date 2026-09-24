from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from mesads.common.decorators import (
    is_administrator,
    is_inspecteur,
    is_manager,
    is_staff,
    profil_required,
)

from . import views

url_prefectures = [
    path(
        "espace-prefecture/<int:prefecture_id>/gestionnaires/",
        profil_required(is_staff, is_administrator)(
            views.ADSManagerAdministratorListeGestionnaires.as_view()
        ),
        name="app.ads-manager-admin.gestionnaires",
        # A GARDER
    ),
    path(
        "espace-prefecture/<int:prefecture_id>/demandes-gestion/",
        profil_required(is_staff, is_administrator)(
            views.ADSManagerAdminRequestsView.as_view()
        ),
        name="app.ads-manager-admin.requests",
        # A GARDER
    ),
    path(
        "espace-prefecture/<int:prefecture_id>/changements",
        profil_required(is_staff, is_administrator)(
            views.ADSManagerAdminUpdatesView.as_view()
        ),
        name="app.ads-manager-admin.updates",
        # A GARDER
    ),
    path(
        "registre_ads/prefectures/<int:prefecture_id>/export",
        profil_required(is_staff, is_administrator)(
            views.PrefectureExportView.as_view()
        ),
        name="app.exports.prefecture",
        # A GARDER
    ),
    path(
        "registre_ads/demande_gestion_prefecture/",
        login_required(views.DemandeGestionPrefectureView.as_view()),
        name="app.ads-manager-admin.demande_gestion_prefecture",
    ),
]

url_gestionnaire = [
    path(
        "registre_ads/",
        login_required(views.AdministrationsEnGestionView.as_view()),
        name="app.ads-manager.administrations",
    ),
    path(
        "registre_ads/demande_gestion_ads/",
        login_required(views.DemandeGestionADSView.as_view()),
        name="app.ads-manager.demande_gestion_ads",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSManagerView.as_view()
        ),
        name="app.ads-manager.detail",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/arretes",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSManagerArreteView.as_view()
        ),
        name="app.ads-manager.decree.detail",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/arretes/<int:arrete_id>/update/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSManagerArreteUpdateView.as_view()
        ),
        name="app.ads-manager.arrete.update",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/arretes/<int:arrete_id>/delete/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSManagerArreteDeleteView.as_view()
        ),
        name="app.ads-manager.arrete.delete",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/export",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSManagerExportView.as_view()
        ),
        name="app.exports.ads-manager",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/ads/<int:ads_id>",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSView.as_view()
        ),
        name="app.ads.detail",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/ads/<int:ads_id>/verification/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSVerificationView.as_view()
        ),
        name="app.ads.verification",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/ads/<int:ads_id>/verification-confirmation/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSVerificationConfirmationView.as_view()
        ),
        name="app.ads.verification-confirmation",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/ads/<int:ads_id>/delete",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSDeleteView.as_view()
        ),
        name="app.ads.delete",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/ads/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSCreateView.as_view()
        ),
        name="app.ads.create",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/ads/<int:ads_id>/history",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ADSHistoryView.as_view()
        ),
        name="app.ads.history",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/arretes-modeles",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ListeArretesFilesView.as_view()
        ),
        name="app.arretes-list",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/telechargement-arrete",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TelechargementArreteView.as_view()
        ),
        name="app.arrete-download",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionListView.as_view()
        ),
        name="app.transaction-liste",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/archives",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ArchiveTransactionListView.as_view()
        ),
        name="app.transaction-liste-archives",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/archives/<int:entree_id>",
        profil_required(is_staff, is_administrator, is_manager)(
            views.RestaurationTransactionView.as_view()
        ),
        name="app.transaction-restauration",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/statut",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ChangementStatutRegistreTransactionView.as_view()
        ),
        name="app.transaction-statut",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/creation",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionCreateView.as_view()
        ),
        name="app.transaction-creation",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/selection-ads",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionSelectionADSFormView.as_view()
        ),
        name="app.transaction-choix-ads",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>/documents",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionDocumentsFormView.as_view()
        ),
        name="app.transaction-documents",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>/enregistrement",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionEnregistrementFormView.as_view()
        ),
        name="app.transaction-enregistrement",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>/confirmation",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionConfirmationView.as_view()
        ),
        name="app.transaction-confirmation",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>",
        profil_required(is_staff, is_administrator, is_manager)(
            views.TransactionEditView.as_view()
        ),
        name="app.transaction-edition",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>/archivage",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ArchivageTransactionDeleteView.as_view()
        ),
        name="app.transaction-archivage",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>/arrete",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ArreteChangementTitulaireExportView.as_view()
        ),
        name="app.transaction-arrete",
    ),
    path(
        "registre_ads/gestion/<int:manager_id>/registre-transactions/<int:entree_id>/courrier-contact/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.DemandePiecesJustificativeWordExportView.as_view()
        ),
        name="app.transaction-courrier",
    ),
]

url_liste_attente = [
    path(
        "liste_attente/<int:manager_id>/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ListeAttenteView.as_view()
        ),
        name="app.liste_attente",
    ),
    path(
        "liste_attente/<int:manager_id>/archives/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.DemandeArchiveesView.as_view()
        ),
        name="app.liste_attente_archives",
    ),
    path(
        "liste_attente/<int:manager_id>/archives/modele-courrier/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ModeleCourrierArchivageView.as_view()
        ),
        name="app.liste_attente_archive_modele",
    ),
    path(
        "liste_attente/<int:manager_id>/attribution-ads/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.AttributionListeAttenteView.as_view()
        ),
        name="app.liste_attente_attribution",
    ),
    path(
        "liste_attente/<int:manager_id>/attribution-ads/<int:inscription_id>/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.InscriptionTraitementListeAttenteView.as_view()
        ),
        name="app.liste_attente_traitement_demande",
    ),
    path(
        "liste_attente/<int:manager_id>/attribution-ads/modele-courrier/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ModeleCourrierContactView.as_view()
        ),
        name="app.liste_attente_contact_modele",
    ),
    path(
        "liste_attente/<int:manager_id>/export/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ExportCSVInscriptionListeAttenteView.as_view()
        ),
        name="app.liste_attente_export",
    ),
    path(
        "liste_attente/<int:manager_id>/inscription/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.CreationInscriptionListeAttenteView.as_view()
        ),
        name="app.liste_attente_inscription",
    ),
    path(
        "liste_attente/<int:manager_id>/<int:inscription_id>/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ModificationInscriptionListeAttenteView.as_view()
        ),
        name="app.liste_attente_inscription_update",
    ),
    path(
        "liste_attente/<int:manager_id>/archivage/<int:inscription_id>/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ArchivageInscriptionListeAttenteView.as_view()
        ),
        name="app.liste_attente_inscription_archivage",
    ),
    path(
        "liste_attente/<int:manager_id>/archivage/<int:inscription_id>/restaurer/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.RestaurationInscriptionView.as_view()
        ),
        name="app.liste_attente_inscription_restaurer",
    ),
    path(
        "liste_attente/<int:manager_id>/archivage/confirmation/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ArchivageConfirmationView.as_view()
        ),
        name="app.liste_attente_inscription_archivage_confirmation",
    ),
    path(
        "liste_attente/<int:manager_id>/make-public/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ChangementStatutListeView.as_view()
        ),
        name="app.liste_attente_make_public",
    ),
    path(
        "liste_attente/<int:manager_id>/export/liste-publique/",
        profil_required(is_staff, is_administrator, is_manager)(
            views.ExportPDFListePubliqueView.as_view()
        ),
        name="app.liste_attente_publique_export_pdf",
    ),
]

url_consultation = [
    path(
        "registre_ads/consultation/recherche/",
        profil_required(is_staff, is_inspecteur)(
            views.ConsultationADSSearchView.as_view()
        ),
        name="app.consultation_search",
    ),
    path(
        "registre_ads/consultation/recherche/<int:ads_id>/",
        profil_required(is_staff, is_inspecteur)(views.ConsultationADSView.as_view()),
        name="app.consultation_ads",
    ),
    path(
        "registre_ads/consultation/recherche/<int:ads_id>/export/",
        profil_required(is_staff, is_inspecteur)(views.ExportADSPDFView.as_view()),
        name="app.consultation_ads_export",
    ),
]

url_commons = [
    path(
        "registre_ads/dashboards",
        staff_member_required(views.DashboardsView.as_view()),
        name="app.dashboards.list",
    ),
    path(
        "gestionnaire_ads/autocomplete",
        views.ADSManagerAutocompleteView.as_view(),
        name="app.autocomplete.ads-manager",
    ),
    path("note-service", views.NotationView.as_view(), name="app.note-service"),
]


url_public = [
    path("", views.HomepageView.as_view(), name="app.homepage"),
    path("faq", views.FAQView.as_view(), name="app.faq"),
    path(
        "mentions-legales",
        TemplateView.as_view(template_name="pages/mentions-legales.html"),
        name="app.legal",
    ),
    path(
        "suivi",
        TemplateView.as_view(template_name="pages/suivi.html"),
        name="app.suivi",
    ),
    path("chiffres-cles", views.StatsView.as_view(), name="app.stats"),
    path(
        "accessibilite",
        TemplateView.as_view(template_name="pages/accessibility.html"),
        name="app.accessibility",
    ),
    path(
        "cgu",
        TemplateView.as_view(template_name="pages/cgu.html"),
        name="app.cgu",
    ),
    path(
        "reglementation",
        views.ReglementationView.as_view(),
        name="app.reglementation",
    ),
    path(
        "plan-site",
        views.PlanSiteView.as_view(),
        name="app.plan_site",
    ),
    path(
        "listes-attente",
        views.ListesAttentesPubliquesView.as_view(),
        name="app.listes_attentes",
    ),
    path(
        "listes-attente/publique/<int:manager_id>/",
        views.ListeAttentePublique.as_view(),
        name="app.liste_attente_publique",
    ),
    path(
        "registres-transactions/",
        views.RegistresTransactionsPublicsView.as_view(),
        name="app.registres-transactions",
    ),
    path(
        "registres-transactions/<int:manager_id>/",
        views.RegistreTransactionsPublicView.as_view(),
        name="app.registre-transactions-public",
    ),
]


urlpatterns = (
    url_prefectures
    + url_gestionnaire
    + url_consultation
    + url_commons
    + url_public
    + url_liste_attente
)

from django.contrib.auth.decorators import login_required
from django.urls import path

from mesads.common.decorators import (
    is_administrator,
    is_inspecteur,
    is_proprietaire,
    is_staff,
    profil_required,
)

from . import views

urlpatterns = [
    path(
        "",
        views.IndexView.as_view(),
        name="vehicules-relais.index",
    ),
    path(
        "consulter",
        views.SearchView.as_view(),
        name="vehicules-relais.search",
    ),
    path(
        "consulter/vehicules/<str:numero>",
        views.VehiculeView.as_view(),
        name="vehicules-relais.vehicule",
    ),
    path(
        "proprietaire",
        login_required(views.ProprietaireListView.as_view()),
        name="vehicules-relais.proprietaire",
    ),
    path(
        "proprietaire/nouveau",
        login_required(views.ProprietaireCreateView.as_view()),
        name="vehicules-relais.proprietaire.new",
    ),
    path(
        "proprietaire/<int:proprietaire_id>",
        profil_required(is_staff, is_proprietaire)(
            views.ProprietaireDetailView.as_view()
        ),
        name="vehicules-relais.proprietaire.detail",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/supprimer",
        profil_required(is_staff, is_proprietaire)(
            views.ProprietaireDeleteView.as_view()
        ),
        name="vehicules-relais.proprietaire.delete",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/modifier",
        profil_required(is_staff, is_proprietaire)(
            views.ProprietaireEditView.as_view()
        ),
        name="vehicules-relais.proprietaire.edit",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/historique",
        profil_required(is_staff)(views.ProprietaireHistoryView.as_view()),
        name="vehicules-relais.proprietaire.history",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/nouveau_vehicule",
        profil_required(is_staff, is_proprietaire)(
            views.ProprietaireVehiculeCreateView.as_view()
        ),
        name="vehicules-relais.proprietaire.vehicule.new",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/vehicules/<str:vehicule_numero>",
        profil_required(is_staff, is_proprietaire, is_administrator)(
            views.ProprietaireVehiculeUpdateView.as_view()
        ),
        name="vehicules-relais.proprietaire.vehicule.edit",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/vehicules/<str:vehicule_numero>/supprimer",
        profil_required(is_staff, is_proprietaire, is_administrator)(
            views.ProprietaireVehiculeDeleteView.as_view()
        ),
        name="vehicules-relais.proprietaire.vehicule.delete",
    ),
    path(
        "proprietaire/<int:proprietaire_id>/vehicules/<str:vehicule_numero>/recepisse",
        profil_required(is_staff, is_proprietaire, is_administrator)(
            views.ProprietaireVehiculeRecepisseView.as_view()
        ),
        name="vehicules-relais.proprietaire.vehicule.recepisse",
    ),
    path(
        "departement/<int:prefecture_id>/vehicules-relais/",
        profil_required(is_staff, is_administrator)(
            views.RepertoireVehiculeRelaisDepartementView.as_view()
        ),
        name="vehicules-relais.vehicules_relais_departement",
    ),
    path(
        "departement/<int:prefecture_id>/vehicules-relais/export/",
        profil_required(is_staff, is_administrator)(
            views.PrefectureTaxisRelaisExportView.as_view()
        ),
        name="vehicules-relais.vehicules_relais_departement_export",
    ),
    path(
        "departement/vehicules-relais/history",
        profil_required(is_staff, is_administrator, is_inspecteur)(
            views.HistoriqueVehiculeRelaisDepartementView.as_view()
        ),
        name="vehicules-relais.vehicules_relais_history",
    ),
    path(
        "departement/<int:prefecture_id>/vehicules-relais/<str:numero>/",
        profil_required(is_staff, is_administrator, is_inspecteur)(
            views.VehiculeDepartementView.as_view()
        ),
        name="vehicules-relais.vehicule_relais_departement_detail",
    ),
    path(
        "departement/vehicules-relais/history/<str:vehicule_numero>/historique",
        profil_required(is_staff, is_administrator, is_inspecteur)(
            views.ProprietaireVehiculeHistoryView.as_view()
        ),
        name="vehicules-relais.vehicule_relais_departement_detail_history",
    ),
]

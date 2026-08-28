from .models import Vehicule


def get_taxis_relais_data_for_excel_export(prefecture):
    rows = []

    vehicules = Vehicule.objects.filter(departement=prefecture).select_related(
        "proprietaire", "commune_localisation"
    )

    for vehicule in vehicules:
        rows.append(
            [
                vehicule.numero,
                vehicule.proprietaire.nom,
                vehicule.immatriculation,
                vehicule.modele,
                vehicule.get_motorisation_display(),
                vehicule.date_mise_circulation,
                vehicule.nombre_places,
                vehicule.pmr,
                vehicule.commune_localisation.libelle
                if vehicule.commune_localisation
                else "",
            ]
        )

    headers = [
        "Numéro",
        "Propriétaire",
        "Immatriculation",
        "Modèle",
        "Motorisation",
        "Date de mise en circulation",
        "Nombre de places",
        "Véhicule PMR",
        "Commune",
    ]

    return headers, rows

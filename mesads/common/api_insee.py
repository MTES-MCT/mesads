import requests
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_siren(siren: str) -> None:
    siren = siren.strip().replace(" ", "")

    if len(siren) != 9:
        raise ValidationError(
            "Le numéro SIREN doit contenir exactement 9 chiffres.",
        )

    if not siren.isdigit():
        raise ValidationError(
            "Le numéro SIREN ne doit contenir que des chiffres.",
        )

    try:
        response = requests.get(
            f"https://api.insee.fr/api-sirene/3.11/siren/{siren}",
            headers={"X-INSEE-Api-Key-Integration": settings.INSEE_TOKEN},
            timeout=5,
        )

    except requests.Timeout as exc:
        raise ValidationError(
            (
                "La vérification du numéro SIREN a expiré. "
                "Veuillez réessayer ultérieurement."
            ),
        ) from exc

    except requests.ConnectionError as exc:
        raise ValidationError(
            ("Impossible de contacter le service de vérification des numéros SIREN."),
        ) from exc

    except requests.RequestException as exc:
        raise ValidationError(
            "Une erreur est survenue lors de la vérification du numéro SIREN.",
        ) from exc

    if response.status_code == 404:
        raise ValidationError(
            "Ce numéro SIREN n'existe pas.",
        )

    if response.status_code in (401, 403):
        raise ValidationError(
            "Le service de vérification des numéros SIREN est mal configuré.",
        )

    if response.status_code == 429:
        raise ValidationError(
            (
                "Le service de vérification des numéros SIREN reçoit trop "
                "de demandes. Veuillez réessayer ultérieurement."
            ),
        )

    if response.status_code >= 500:
        raise ValidationError(
            "Le service de vérification des numéros SIREN est indisponible.",
        )

    if not response.ok:
        raise ValidationError(
            "Le numéro SIREN n'a pas pu être vérifié.",
        )

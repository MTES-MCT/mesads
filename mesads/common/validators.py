import logging

from django.core.exceptions import ValidationError

from .services.antivirus import scan_file

logger = logging.getLogger(__name__)


def validate_file_antivirus(value):
    if not value:
        return

    try:
        result = scan_file(value)

    except Exception:
        logger.exception("Erreur lors de l'analyse antivirus")
        raise ValidationError(
            "Le service d'analyse antivirus est temporairement indisponible.",
            code="antivirus_unavailable",
        )
    finally:
        value.seek(0)

    status, signature = result.get("stream", (None, None))

    if status == "FOUND":
        logger.warning("Menace détectée : %s", signature)
        raise ValidationError(
            "Le fichier contient une menace et a été refusé.",
            code="virus_detected",
        )

    if status != "OK":
        logger.error("Résultat antivirus inattendu : %s", result)
        raise ValidationError(
            "Impossible de vérifier la sécurité du fichier.",
            code="antivirus_error",
        )

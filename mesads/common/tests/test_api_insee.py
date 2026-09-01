from unittest.mock import Mock, patch

import pytest
import requests
from django.core.exceptions import ValidationError

from mesads.common.api_insee import validate_siren

REQUESTS_GET_PATH = "mesads.common.api_insee.requests.get"


@patch(REQUESTS_GET_PATH)
def test_validate_siren_accepts_existing_siren(mock_get, settings):
    settings.INSEE_TOKEN = "fake-token"

    response = Mock()
    response.status_code = 200
    response.ok = True
    mock_get.return_value = response

    validate_siren("123456789")

    mock_get.assert_called_once_with(
        "https://api.insee.fr/api-sirene/3.11/siren/123456789",
        headers={"X-INSEE-Api-Key-Integration": "fake-token"},
        timeout=5,
    )


@pytest.mark.parametrize(
    ("siren", "expected_message"),
    [
        (
            "12345678",
            "Le numéro SIREN doit contenir exactement 9 chiffres.",
        ),
        (
            "1234567890",
            "Le numéro SIREN doit contenir exactement 9 chiffres.",
        ),
        (
            "",
            "Le numéro SIREN doit contenir exactement 9 chiffres.",
        ),
        (
            "12345ABCD",
            "Le numéro SIREN ne doit contenir que des chiffres.",
        ),
    ],
)
@patch(REQUESTS_GET_PATH)
def test_validate_siren_rejects_invalid_format(
    mock_get,
    siren,
    expected_message,
):
    with pytest.raises(ValidationError) as exc_info:
        validate_siren(siren)

    assert exc_info.value.messages == [expected_message]
    mock_get.assert_not_called()


@pytest.mark.parametrize(
    ("exception", "expected_message"),
    [
        (
            requests.Timeout(),
            (
                "La vérification du numéro SIREN a expiré. "
                "Veuillez réessayer ultérieurement."
            ),
        ),
        (
            requests.ConnectionError(),
            "Impossible de contacter le service de vérification des numéros SIREN.",
        ),
        (
            requests.RequestException(),
            "Une erreur est survenue lors de la vérification du numéro SIREN.",
        ),
    ],
)
@patch(REQUESTS_GET_PATH)
def test_validate_siren_handles_request_errors(
    mock_get,
    exception,
    expected_message,
):
    mock_get.side_effect = exception

    with pytest.raises(ValidationError) as exc_info:
        validate_siren("123456789")

    assert exc_info.value.messages == [expected_message]


@pytest.mark.parametrize(
    ("status_code", "expected_message"),
    [
        (404, "Ce numéro SIREN n'existe pas."),
        (401, "Le service de vérification des numéros SIREN est mal configuré."),
        (
            429,
            (
                "Le service de vérification des numéros SIREN reçoit trop "
                "de demandes. Veuillez réessayer ultérieurement."
            ),
        ),
        (500, "Le service de vérification des numéros SIREN est indisponible."),
    ],
)
@patch(REQUESTS_GET_PATH)
def test_validate_siren_handles_status_code(
    mock_get,
    status_code,
    expected_message,
):
    response = Mock()
    response.status_code = status_code
    response.ok = True
    mock_get.return_value = response

    with pytest.raises(ValidationError) as exc_info:
        validate_siren("123456789")

    assert exc_info.value.messages == [expected_message]

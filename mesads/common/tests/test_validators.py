from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from mesads.common.validators import validate_file_antivirus


@pytest.fixture
def test_file():
    return SimpleUploadedFile(
        "document.pdf",
        b"Contenu de test",
        content_type="application/pdf",
    )


def test_antivirus_clean_file(test_file):
    with patch(
        "mesads.common.validators.scan_file",
        return_value={"stream": ("OK", None)},
    ):
        validate_file_antivirus(test_file)


def test_antivirus_infected_file(test_file):
    with patch(
        "mesads.common.validators.scan_file",
        return_value={"stream": ("FOUND", "Eicar-Test-Signature")},
    ):
        with pytest.raises(ValidationError) as exc:
            validate_file_antivirus(test_file)

    assert exc.value.error_list[0].code == "virus_detected"


def test_antivirus_unavailable(test_file):
    with patch(
        "mesads.common.validators.scan_file",
        side_effect=ConnectionError("ClamAV unavailable"),
    ):
        with pytest.raises(ValidationError) as exc:
            validate_file_antivirus(test_file)

    assert exc.value.error_list[0].code == "antivirus_unavailable"

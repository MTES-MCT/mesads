import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from ..validators import validate_file_size, validate_file_type


@pytest.mark.parametrize(
    "filename",
    [
        "document.exe",
        "document.php",
        "document.html",
        "document.txt",
        "document.doc",
    ],
)
def test_validate_file_type_invalid_extension(filename):
    file = SimpleUploadedFile(
        filename,
        b"some content",
    )

    with pytest.raises(ValidationError):
        validate_file_type(file)


def test_validate_file_type_invalid_content():
    file = SimpleUploadedFile(
        "document.pdf",
        b"This is not a PDF",
    )

    with pytest.raises(
        ValidationError,
        match="Le contenu du fichier ne correspond pas",
    ):
        validate_file_type(file)


@pytest.mark.parametrize(
    ("size", "valid"),
    [
        (1024, True),
        (5 * 1024 * 1024, True),
        (10 * 1024 * 1024, True),
        (10 * 1024 * 1024 + 1, False),
    ],
)
def test_validate_file_size(size, valid):
    file = SimpleUploadedFile(
        name="document.pdf",
        content=b"x" * size,
    )

    if valid:
        validate_file_size(file)
    else:
        with pytest.raises(ValidationError):
            validate_file_size(file)

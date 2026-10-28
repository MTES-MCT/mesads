from pathlib import Path
from zipfile import BadZipFile, ZipFile

import puremagic
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mio


def validate_file_size(value):
    if value.size > MAX_FILE_SIZE:
        raise ValidationError(
            "Le fichier ne doit pas dépasser 10 Mo.",
            code="file_too_large",
        )


ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
}

validate_file_extension = FileExtensionValidator(
    allowed_extensions=[extension.lstrip(".") for extension in ALLOWED_MIME_TYPES],
)


def validate_file_type(value):
    validate_file_extension(value)

    extension = Path(value.name).suffix.lower()
    position = value.tell()

    try:
        value.seek(0)

        try:
            mime_type = puremagic.from_stream(
                value,
                mime=True,
            )
        except puremagic.PureError:
            raise ValidationError("Impossible d'identifier le format du fichier.")

        if extension == ".docx" and mime_type == "application/zip":
            try:
                value.seek(0)
                with ZipFile(value) as archive:
                    names = set(archive.namelist())
                    valid_docx = (
                        "[Content_Types].xml" in names and "word/document.xml" in names
                    )
            except BadZipFile:
                valid_docx = False

            if valid_docx:
                return

        if mime_type != ALLOWED_MIME_TYPES[extension]:
            raise ValidationError(
                "Le contenu du fichier ne correspond pas à son extension."
            )
    finally:
        value.seek(position)

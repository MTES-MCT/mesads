from clamav_client.clamd import ClamdNetworkSocket
from django.conf import settings


def scan_file(file):
    client = ClamdNetworkSocket(
        host=settings.CLAMAV_HOST,
        port=settings.CLAMAV_PORT,
        timeout=30,
    )

    file.seek(0)
    try:
        return client.instream(file)
    finally:
        file.seek(0)

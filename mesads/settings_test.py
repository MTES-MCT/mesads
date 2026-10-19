"""Test settings.

Make sure to reset production data that might have been retrieved from the
environment. We do not want to store files in S3 or send emails in tests.
"""

from .settings import *  # noqa


INSEE_TOKEN = None

EMAIL_HOST = None
EMAIL_PORT = None
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None
EMAIL_USE_TLS = None

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "mesads.middleware.BackwardCompatibilityURLMiddleware",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Configuration OIDC réservée aux tests.
OIDC_RP_CLIENT_ID = "test-client-id"
OIDC_RP_CLIENT_SECRET = "test-client-secret"

OIDC_OP_JWKS_ENDPOINT = "https://oidc.example.test/jwks"

OIDC_OP_AUTHORIZATION_ENDPOINT = "https://oidc.example.test/authorize"

OIDC_OP_TOKEN_ENDPOINT = "https://oidc.example.test/token"

OIDC_OP_USER_ENDPOINT = "https://oidc.example.test/userinfo"

OIDC_OP_LOGOUT_ENDPOINT = "https://oidc.example.test/logout"

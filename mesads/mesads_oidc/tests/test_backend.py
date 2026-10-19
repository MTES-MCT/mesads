from types import SimpleNamespace
from unittest.mock import patch

import pytest
from mozilla_django_oidc.auth import (
    OIDCAuthenticationBackend as MozillaOIDCAuthenticationBackend,
)

from mesads.mesads_oidc.backends import OIDCAuthenticationBackend
from mesads.mesads_oidc.mfa import MFA_ACR_VALUES


@pytest.fixture
def backend():
    backend = OIDCAuthenticationBackend()
    backend.request = SimpleNamespace(
        admin_mfa_requested=False,
    )
    return backend


@pytest.mark.parametrize("acr", sorted(MFA_ACR_VALUES))
def test_verify_token_with_mfa(backend, acr):
    payload = {"acr": acr}

    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value=payload,
    ):
        result = backend.verify_token(
            "fake-token",
            nonce="fake-nonce",
        )

    assert result == payload
    assert backend.request.oidc_verified_acr == acr


def test_verify_token_without_mfa_on_classic_login(backend):
    payload = {"acr": "eidas1"}

    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value=payload,
    ):
        result = backend.verify_token(
            "fake-token",
            nonce="fake-nonce",
        )

    assert result == payload
    assert backend.request.oidc_verified_acr == "eidas1"


@pytest.mark.parametrize("acr", sorted(MFA_ACR_VALUES))
def test_verify_token_admin_with_mfa(backend, acr):
    backend.request.admin_mfa_requested = True

    payload = {"acr": acr}

    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value=payload,
    ):
        result = backend.verify_token(
            "fake-token",
            nonce="fake-nonce",
        )

    assert result == payload


@pytest.mark.parametrize("acr", ["eidas0", "eidas1", None])
def test_verify_token_admin_without_mfa(backend, acr):
    backend.request.admin_mfa_requested = True

    payload = {"acr": acr}

    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value=payload,
    ):
        result = backend.verify_token(
            "fake-token",
            nonce="fake-nonce",
        )

    assert result is None


def test_verify_token_invalid_token(backend):
    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value=None,
    ):
        result = backend.verify_token(
            "invalid-token",
            nonce="fake-nonce",
        )

    assert result is None


def test_verify_token_userinfo_jwt(backend):
    backend.request.admin_mfa_requested = True

    payload = {
        "sub": "123456",
        "email": "test@example.com",
    }

    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value=payload,
    ):
        result = backend.verify_token("userinfo-jwt")

    assert result == payload
    assert not hasattr(
        backend.request,
        "oidc_verified_acr",
    )

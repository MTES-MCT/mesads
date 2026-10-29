from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
import requests
from mozilla_django_oidc.auth import (
    OIDCAuthenticationBackend as MozillaOIDCAuthenticationBackend,
)

from mesads.mesads_oidc.backends import OIDCAuthenticationBackend
from mesads.mesads_oidc.mfa import MFA_ACR_VALUES
from mesads.users.models import User


@pytest.fixture
def backend():
    instance = OIDCAuthenticationBackend()
    instance.request = SimpleNamespace(session={})
    return instance


@pytest.fixture
def claims():
    return {
        "sub": "7396c91e-b9f2-4f9d-8547-5e9b3332725b",
        "email": "agent@example.com",
        "given_name": "Alice",
        "usual_name": "Martin",
        "uid": "agent-123",
        "idp_id": "550e8400-e29b-41d4-a716-446655440000",
        "siret": "12345678901234",
        "chorusdt": "matricule-123",
    }


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


@pytest.mark.parametrize("acr", ["eidas0", "eidas1", None])
def test_verify_token_without_mfa(backend, acr):
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


def test_verify_token_without_acr(backend):
    with patch.object(
        MozillaOIDCAuthenticationBackend,
        "verify_token",
        return_value={"sub": "agent-123"},
    ):
        assert backend.verify_token("fake-token", nonce="fake-nonce") is None


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


def test_get_userinfo_json(backend, claims):
    response = Mock()
    response.json.return_value = claims

    with patch(
        "mesads.mesads_oidc.backends.requests.get", return_value=response
    ) as get:
        result = backend.get_userinfo(
            "access-token", "id-token", {"sub": claims["sub"]}
        )

    assert result == claims
    response.raise_for_status.assert_called_once_with()
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer access-token"}


def test_get_userinfo_jwt(backend, claims):
    response = Mock(text="signed-userinfo")
    response.json.side_effect = requests.exceptions.JSONDecodeError("invalid", "jwt", 0)

    with (
        patch("mesads.mesads_oidc.backends.requests.get", return_value=response),
        patch.object(backend, "verify_token", return_value=claims) as verify,
    ):
        result = backend.get_userinfo(
            "access-token", "id-token", {"sub": claims["sub"]}
        )

    assert result == claims
    verify.assert_called_once_with("signed-userinfo")


def test_get_userinfo_http_error(backend):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("Unauthorized")

    with patch("mesads.mesads_oidc.backends.requests.get", return_value=response):
        with pytest.raises(requests.HTTPError):
            backend.get_userinfo("access-token", "id-token", {})


def test_get_data_for_user_create_and_update(backend, claims):
    assert backend.get_data_for_user_create_and_update(claims) == {
        "email": claims["email"],
        "first_name": "Alice",
        "last_name": "Martin",
        "proconnect_sub": claims["sub"],
        "proconnect_uid": claims["uid"],
        "proconnect_idp_id": claims["idp_id"],
        "proconnect_siret": claims["siret"],
        "proconnect_chorusdt": claims["chorusdt"],
    }


def test_get_data_for_user_with_optional_claims_missing(backend):
    data = backend.get_data_for_user_create_and_update({"sub": "subject"})

    assert data["first_name"] == ""
    assert data["last_name"] == ""
    assert data["proconnect_uid"] == ""
    assert data["email"] is None


@pytest.mark.django_db
def test_filter_users_by_claims(backend, user_factory, claims):
    user = user_factory(email=claims["email"], proconnect_sub=claims["sub"])
    user_factory()

    assert list(backend.filter_users_by_claims(claims)) == [user]


@pytest.mark.django_db
def test_filter_users_does_not_match_email_alone(backend, user_factory, claims):
    user_factory(email=claims["email"], proconnect_sub=None)

    assert not backend.filter_users_by_claims(claims).exists()


@pytest.mark.parametrize("sub", [None, ""])
@pytest.mark.django_db
def test_filter_users_without_sub(backend, user_factory, sub):
    user_factory(email="agent@example.com", proconnect_sub=None)
    result = backend.filter_users_by_claims({"sub": sub, "email": "agent@example.com"})

    assert not result.exists()


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, True),
        ({"sub": None}, False),
        ({"sub": ""}, False),
        ({"email": None}, False),
        ({"email": ""}, False),
    ],
)
def test_verify_claims(backend, claims, changes, expected):
    claims.update(changes)

    with patch.object(
        MozillaOIDCAuthenticationBackend, "verify_claims", return_value=True
    ):
        assert backend.verify_claims(claims) is expected


def test_verify_claims_rejected_by_parent(backend, claims):
    with patch.object(
        MozillaOIDCAuthenticationBackend, "verify_claims", return_value=False
    ):
        assert backend.verify_claims(claims) is False


@pytest.mark.django_db
def test_create_user(backend, claims):
    user = backend.create_user(claims)

    assert user.pk is not None
    user.refresh_from_db()
    assert user.email == claims["email"]
    assert user.first_name == claims["given_name"]
    assert user.last_name == claims["usual_name"]
    assert str(user.proconnect_sub) == claims["sub"]
    assert user.proconnect_uid == claims["uid"]
    assert str(user.proconnect_idp_id) == claims["idp_id"]
    assert User.objects.count() == 1
    assert backend.request.session == {}


@pytest.mark.django_db
@pytest.mark.parametrize("known_sub", [False, True])
def test_create_user_with_existing_email(backend, user_factory, claims, known_sub):
    user_factory(
        email=claims["email"],
        proconnect_sub="11111111-1111-4111-8111-111111111111" if known_sub else None,
    )

    assert backend.create_user(claims) is None
    assert backend.request.session["oidc_account_conflict"] is True
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_create_user_with_existing_email_case_insensitive(
    backend, user_factory, claims
):
    user_factory(email=claims["email"].upper(), proconnect_sub=None)

    assert backend.create_user(claims) is None
    assert backend.request.session["oidc_account_conflict"] is True
    assert User.objects.count() == 1


@pytest.fixture
def existing_user(user_factory, claims):
    return user_factory(
        email=claims["email"],
        first_name="Old name",
        last_name="Old surname",
        proconnect_sub=claims["sub"],
        proconnect_uid=claims["uid"],
        proconnect_idp_id=claims["idp_id"],
        proconnect_siret="",
        proconnect_chorusdt="",
    )


@pytest.mark.django_db
def test_update_user(backend, existing_user, claims):
    result = backend.update_user(existing_user, claims)

    assert result is existing_user
    existing_user.refresh_from_db()
    assert existing_user.first_name == "Alice"
    assert existing_user.last_name == "Martin"
    assert existing_user.proconnect_siret == claims["siret"]
    assert existing_user.proconnect_chorusdt == claims["chorusdt"]
    assert existing_user.proconnect_sub == UUID(claims["sub"])
    assert existing_user.proconnect_uid == claims["uid"]
    assert existing_user.proconnect_idp_id == UUID(claims["idp_id"])
    assert backend.request.session == {}


@pytest.mark.django_db
def test_update_user_with_new_available_email(backend, existing_user, claims):
    claims["email"] = "new-email@example.com"

    assert backend.update_user(existing_user, claims) is existing_user
    existing_user.refresh_from_db()
    assert existing_user.email == claims["email"]
    assert backend.request.session == {}


@pytest.mark.django_db
def test_update_user_with_existing_email(backend, user_factory, existing_user, claims):
    original_email = existing_user.email
    claims["email"] = "other@example.com"
    user_factory(email=claims["email"])

    assert backend.update_user(existing_user, claims) is None
    assert backend.request.session["oidc_account_conflict"] is True
    existing_user.refresh_from_db()
    assert existing_user.email == original_email
    assert existing_user.first_name == "Old name"


@pytest.mark.parametrize(
    ("field", "new_value"),
    [
        ("sub", "11111111-1111-4111-8111-111111111111"),
        ("uid", "another-agent"),
        ("idp_id", "22222222-2222-4222-8222-222222222222"),
    ],
)
@pytest.mark.django_db
def test_update_user_with_identity_conflict(
    backend, existing_user, claims, field, new_value
):
    original_sub = str(existing_user.proconnect_sub)
    original_uid = existing_user.proconnect_uid
    original_idp_id = str(existing_user.proconnect_idp_id)
    claims[field] = new_value

    assert backend.update_user(existing_user, claims) is None
    assert backend.request.session["oidc_account_conflict"] is True
    existing_user.refresh_from_db()
    assert existing_user.first_name == "Old name"
    assert str(existing_user.proconnect_sub) == original_sub
    assert existing_user.proconnect_uid == original_uid
    assert str(existing_user.proconnect_idp_id) == original_idp_id


@pytest.mark.django_db
def test_update_user_preserves_empty_claims(backend, existing_user, claims):
    claims.update(given_name="", usual_name="", siret="")

    assert backend.update_user(existing_user, claims) is existing_user
    existing_user.refresh_from_db()
    assert existing_user.first_name == "Old name"
    assert existing_user.last_name == "Old surname"


def test_get_username(backend, claims):
    assert backend.get_username(claims) == claims["email"]
    assert backend.get_username({}) is None

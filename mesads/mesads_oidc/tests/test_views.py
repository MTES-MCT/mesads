import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)

from mesads.mesads_oidc.mfa import MFA_ACR_VALUES
from mesads.mesads_oidc.views import (
    AdminOIDCAuthenticationRequestView,
    ProConnectCallbackView,
)


@pytest.fixture
def request_with_session():
    def create(path, params=None):
        request = RequestFactory().get(
            path,
            data=params or {},
        )

        middleware = SessionMiddleware(lambda request: None)
        middleware.process_request(request)

        return request

    return create


@pytest.fixture
def callback_view(request_with_session):
    request = request_with_session("/oidc/callback/")

    view = ProConnectCallbackView()
    view.request = request
    view.user = SimpleNamespace(pk=123)

    return view


def test_admin_oidc_authentication_extra_params(request_with_session):
    request = request_with_session("/oidc/admin/authenticate/")

    with patch.object(
        OIDCAuthenticationRequestView,
        "get_extra_params",
        return_value={"acr_values": "eidas1"},
    ):
        view = AdminOIDCAuthenticationRequestView()
        params = view.get_extra_params(request)

    assert "acr_values" not in params
    assert "claims" in params

    claims = json.loads(params["claims"])
    acr = claims["id_token"]["acr"]

    assert acr["essential"] is True
    assert set(acr["values"]) == MFA_ACR_VALUES


def test_admin_oidc_authentication_stores_mfa_state(request_with_session):
    request = request_with_session("/oidc/admin/authenticate/")

    request.session["oidc_states"] = {
        "test-state": {
            "nonce": "test-nonce",
        }
    }

    with patch.object(
        OIDCAuthenticationRequestView,
        "get",
        return_value=HttpResponseRedirect(
            "https://proconnect.example/auth?state=test-state"
        ),
    ):
        response = AdminOIDCAuthenticationRequestView().get(request)

    assert response.status_code == 302

    assert request.session["oidc_states"]["test-state"]["admin_mfa"] is True

    assert request.session.modified is True


@pytest.mark.parametrize(
    ("admin_mfa", "expected"),
    [
        (True, True),
        (False, False),
        (None, False),
    ],
)
def test_callback_identifies_admin_mfa(
    request_with_session,
    admin_mfa,
    expected,
):
    request = request_with_session(
        "/oidc/callback/",
        {"state": "test-state"},
    )

    request.session["oidc_states"] = {
        "test-state": {
            "nonce": "test-nonce",
            "admin_mfa": admin_mfa,
        }
    }

    with patch.object(
        OIDCAuthenticationCallbackView,
        "get",
        return_value=HttpResponseRedirect("/"),
    ):
        response = ProConnectCallbackView().get(request)

    assert response.status_code == 302
    assert request.admin_mfa_requested is expected


def test_callback_with_unknown_state(request_with_session):
    request = request_with_session(
        "/oidc/callback/",
        {"state": "unknown-state"},
    )

    request.session["oidc_states"] = {
        "other-state": {
            "admin_mfa": True,
        }
    }

    with patch.object(
        OIDCAuthenticationCallbackView,
        "get",
        return_value=HttpResponseRedirect("/"),
    ):
        response = ProConnectCallbackView().get(request)

    assert response.status_code == 302
    assert request.admin_mfa_requested is False


def test_callback_without_state(request_with_session):
    request = request_with_session("/oidc/callback/")

    request.session["oidc_states"] = {}

    with patch.object(
        OIDCAuthenticationCallbackView,
        "get",
        return_value=HttpResponseRedirect("/"),
    ):
        response = ProConnectCallbackView().get(request)

    assert response.status_code == 302
    assert request.admin_mfa_requested is False


@pytest.mark.parametrize("acr", sorted(MFA_ACR_VALUES))
def test_callback_stores_mfa(callback_view, acr):
    callback_view.request.oidc_verified_acr = acr

    with patch.object(
        OIDCAuthenticationCallbackView,
        "login_success",
        return_value=HttpResponseRedirect("/"),
    ):
        response = callback_view.login_success()

    assert response.status_code == 302

    mfa = callback_view.request.session["admin_mfa"]

    assert mfa["user_id"] == "123"
    assert mfa["acr"] == acr


@pytest.mark.parametrize(
    "acr",
    ["eidas0", "eidas1", None],
)
def test_callback_without_mfa(callback_view, acr):
    callback_view.request.oidc_verified_acr = acr

    with patch.object(
        OIDCAuthenticationCallbackView,
        "login_success",
        return_value=HttpResponseRedirect("/"),
    ):
        response = callback_view.login_success()

    assert response.status_code == 302
    assert "admin_mfa" not in callback_view.request.session


def test_callback_clears_previous_mfa(callback_view):
    request = callback_view.request

    request.session["admin_mfa"] = {
        "user_id": "123",
        "acr": "eidas1-mfa",
    }

    request.oidc_verified_acr = "eidas1"

    with patch.object(
        OIDCAuthenticationCallbackView,
        "login_success",
        return_value=HttpResponseRedirect("/"),
    ):
        response = callback_view.login_success()

    assert response.status_code == 302
    assert "admin_mfa" not in request.session


def test_callback_replaces_previous_mfa(callback_view):
    request = callback_view.request

    request.session["admin_mfa"] = {
        "user_id": "999",
        "acr": "eidas0-mfa",
    }

    request.oidc_verified_acr = "eidas2"

    with patch.object(
        OIDCAuthenticationCallbackView,
        "login_success",
        return_value=HttpResponseRedirect("/"),
    ):
        response = callback_view.login_success()

    assert response.status_code == 302

    mfa = request.session["admin_mfa"]

    assert mfa["user_id"] == "123"
    assert mfa["acr"] == "eidas2"


def test_callback_without_acr_attribute(callback_view):
    request = callback_view.request

    with patch.object(
        OIDCAuthenticationCallbackView,
        "login_success",
        return_value=HttpResponseRedirect("/"),
    ):
        response = callback_view.login_success()

    assert response.status_code == 302
    assert "admin_mfa" not in request.session

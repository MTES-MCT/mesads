import pytest
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, override_settings

from mesads.mesads_oidc.views import ProConnectCallbackView


@pytest.mark.parametrize("account_conflict", [True, False])
@override_settings(LOGIN_REDIRECT_URL_FAILURE="/login/")
def test_login_failure(account_conflict):
    request = RequestFactory().get("/oidc/callback/")
    request.session = {"oidc_account_conflict": account_conflict}
    request._messages = FallbackStorage(request)

    view = ProConnectCallbackView()
    view.request = request

    response = view.login_failure()

    assert response.status_code == 302
    assert response.url == "/login/"
    assert "oidc_account_conflict" not in request.session

    messages = list(get_messages(request))

    if account_conflict:
        assert len(messages) == 1
        assert "Veuillez contacter l'assistance MesADS" in str(messages[0])
    else:
        assert messages == []

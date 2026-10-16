import json
from urllib.parse import parse_qs, urlsplit

from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)

from .mfa import MFA_ACR_VALUES


class AdminOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    def get_extra_params(self, request):
        params = super().get_extra_params(request).copy()
        params.pop("acr_values", None)
        params["claims"] = json.dumps(
            {
                "id_token": {
                    "acr": {
                        "essential": True,
                        "values": sorted(MFA_ACR_VALUES),
                    }
                }
            }
        )

        return params

    def get(self, request):
        response = super().get(request)

        state = parse_qs(urlsplit(response["Location"]).query)["state"][0]

        request.session["oidc_states"][state]["admin_mfa"] = True
        request.session.modified = True

        return response


class ProConnectCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request):
        state = request.GET.get("state")

        state_data = request.session.get("oidc_states", {}).get(state, {})

        request.admin_mfa_requested = state_data.get("admin_mfa") is True

        return super().get(request)

    def login_success(self):
        response = super().login_success()

        acr = getattr(
            self.request,
            "oidc_verified_acr",
            None,
        )
        self.request.session.pop("admin_mfa", None)

        if acr in MFA_ACR_VALUES:
            self.request.session["admin_mfa"] = {
                "user_id": str(self.user.pk),
                "acr": acr,
            }

        return response

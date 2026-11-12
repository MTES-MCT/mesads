import json
from urllib.parse import parse_qs, urlsplit

from django.contrib import messages
from mozilla_django_oidc.views import (
    OIDCAuthenticationCallbackView,
    OIDCAuthenticationRequestView,
)

from .mfa import MFA_ACR_VALUES


class AdminOIDCAuthenticationRequestView(OIDCAuthenticationRequestView):
    """Parcours d'authentification réservé à l'admin Django : on exige de
    ProConnect une authentification multi-facteurs."""

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

    def login_failure(self):
        if self.request.session.pop("oidc_account_conflict", False):
            messages.error(
                self.request,
                "Un compte MesADS existe déjà avec cette adresse "
                "électronique, mais il n'est pas encore associé "
                "à votre identité ProConnect. "
                "Veuillez contacter l'assistance MesADS "
                "pour récupérer votre compte.",
            )

        return super().login_failure()

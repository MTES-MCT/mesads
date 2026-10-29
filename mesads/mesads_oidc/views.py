from django.contrib import messages
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView


class ProConnectCallbackView(OIDCAuthenticationCallbackView):
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

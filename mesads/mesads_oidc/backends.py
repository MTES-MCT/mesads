import requests
from mozilla_django_oidc.auth import (
    OIDCAuthenticationBackend as MozillaOIDCAuthenticationBackend,
)

from .mfa import MFA_ACR_VALUES


class OIDCAuthenticationBackend(MozillaOIDCAuthenticationBackend):
    def verify_token(self, token, **kwargs):
        payload = super().verify_token(token, **kwargs)

        if payload is None:
            return None

        # On vérifie la MFA uniquement sur l'ID Token.
        if "nonce" in kwargs and payload.get("acr") not in MFA_ACR_VALUES:
            return None

        return payload

    def get_userinfo(self, access_token, id_token, payload):
        # Surcharge de la récupération des informations utilisateur:
        # le décodage JSON du contenu JWT pose problème avec ProConnect
        # qui le retourne en format JWT (content-type: application/jwt)
        # d'où ce petit hack.
        # Inspiré de : https://github.com/numerique-gouv/people/blob/b637774179d94cecb0ef2454d4762750a6a5e8c0/src/backend/core/authentication/backends.py#L47C1-L47C57
        user_response = requests.get(
            self.OIDC_OP_USER_ENDPOINT,
            headers={"Authorization": "Bearer {0}".format(access_token)},
            verify=self.get_settings("OIDC_VERIFY_SSL", True),
            timeout=self.get_settings("OIDC_TIMEOUT", None),
            proxies=self.get_settings("OIDC_PROXY", None),
        )
        user_response.raise_for_status()

        try:
            # cas où le type du token JWT est `application/json`
            return user_response.json()
        except requests.exceptions.JSONDecodeError:
            # sinon, on présume qu'il s'agit d'un token JWT au format `application/jwt`
            # comme c'est le cas pour ProConnect.
            return self.verify_token(user_response.text)

    def get_data_for_user_create_and_update(self, claims):
        return {
            "email": claims.get("email"),
            "first_name": claims.get("given_name", ""),
            "last_name": claims.get("usual_name", ""),
            "proconnect_sub": claims.get("sub"),
            "proconnect_uid": claims.get("uid", ""),
            "proconnect_idp_id": claims.get("idp_id"),
            "proconnect_siret": claims.get("siret", ""),
            "proconnect_chorusdt": claims.get("chorusdt", ""),
        }

    def filter_users_by_claims(self, claims):
        sub = claims.get("sub")

        if not sub:
            return self.UserModel.objects.none()

        return self.UserModel.objects.filter(proconnect_sub=sub)

    def verify_claims(self, claims):
        return (
            super().verify_claims(claims)
            and bool(claims.get("sub"))
            and bool(claims.get("email"))
        )

    def create_user(self, claims):
        email = claims.get("email")

        if self.UserModel.objects.filter(email__iexact=email).exists():
            self.request.session["oidc_account_conflict"] = True
            return None

        return self.UserModel.objects.create_user(
            **self.get_data_for_user_create_and_update(claims)
        )

    def update_user(self, user, claims):
        email = claims.get("email")

        if (
            self.UserModel.objects.filter(email__iexact=email)
            .exclude(pk=user.pk)
            .exists()
        ):
            self.request.session["oidc_account_conflict"] = True
            return None

        if (
            str(user.proconnect_sub) != claims.get("sub")
            or (user.proconnect_uid and user.proconnect_uid != claims.get("uid"))
            or (
                user.proconnect_idp_id
                and str(user.proconnect_idp_id) != claims.get("idp_id")
            )
        ):
            self.request.session["oidc_account_conflict"] = True
            return None

        data = self.get_data_for_user_create_and_update(claims)

        for key in ("proconnect_sub", "proconnect_uid", "proconnect_idp_id"):
            data.pop(key, None)

        for key, value in data.items():
            if value:
                setattr(user, key, value)

        user.save()
        return user

    def get_username(self, claims):
        return claims.get("email")

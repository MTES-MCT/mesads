from urllib.parse import urlencode

from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


class MesADSAdminSite(AdminSite):
    @staticmethod
    def has_valid_mfa(request):
        if not request.user.is_authenticated:
            return False

        mfa = request.session.get("admin_mfa")

        if not isinstance(mfa, dict):
            return False

        if mfa.get("user_id") != str(request.user.pk):
            return False

        return True

    def has_permission(self, request):
        return super().has_permission(request) and self.has_valid_mfa(request)

    def login(self, request, extra_context=None):
        next_url = request.GET.get(
            "next",
            reverse("admin:index"),
        )

        if not url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = reverse("admin:index")

        url = reverse("oidc_admin_authenticate")

        if not request.user.is_authenticated:
            return HttpResponseRedirect(f"{url}?{urlencode({'next': next_url})}")

        if not request.user.is_active or not request.user.is_staff:
            raise PermissionDenied

        if self.has_valid_mfa(request):
            return HttpResponseRedirect(next_url)

        return HttpResponseRedirect(f"{url}?{urlencode({'next': next_url})}")

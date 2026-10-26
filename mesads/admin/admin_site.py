from urllib.parse import urlencode

from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


class MesADSAdminSite(AdminSite):
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

        if not request.user.is_authenticated:
            url = reverse("oidc_authentication_init")
            return HttpResponseRedirect(f"{url}?{urlencode({'next': next_url})}")

        if not self.has_permission(request):
            raise PermissionDenied

        return HttpResponseRedirect(next_url)

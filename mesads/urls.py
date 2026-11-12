import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path
from markdownx.views import ImageUploadView, MarkdownifyView

from .admin_views import (
    ExportListeAttenteDataExcel,
    ExportRegistreTransactionDataExcel,
    StatistiquesView,
)
from .app import views
from .mesads_oidc.views import AdminOIDCAuthenticationRequestView

urlpatterns = [
    path("api/", include("mesads.api.urls")),
    path("auth/", include("mesads.users.urls")),
    path("fradm/", include("mesads.fradm.urls")),
    path(
        "admin/statistiques/",
        admin.site.admin_view(StatistiquesView.as_view()),
        name="admin-statistiques",
    ),
    path(
        "admin/statistiques/export-data-liste-attente",
        admin.site.admin_view(ExportListeAttenteDataExcel.as_view()),
        name="admin-statistiques-export-data-liste-attente",
    ),
    path(
        "admin/statistiques/export-data-registre-transaction",
        admin.site.admin_view(ExportRegistreTransactionDataExcel.as_view()),
        name="admin-statistiques-export-data-registre-transaction",
    ),
    path("admin/", admin.site.urls),
    path("", include("mesads.app.urls")),
    path("relais/", include("mesads.vehicules_relais.urls")),
    path(
        "markdownx/upload/",
        staff_member_required(ImageUploadView.as_view()),
        name="markdownx_upload",
    ),
    path(
        "markdownx/markdownify/",
        staff_member_required(MarkdownifyView.as_view()),
        name="markdownx_markdownify",
    ),
    path(
        "oidc/admin/authenticate/",
        AdminOIDCAuthenticationRequestView.as_view(),
        name="oidc_admin_authenticate",
    ),
    path("oidc/", include("mozilla_django_oidc.urls")),
]

if settings.DEBUG:
    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


handler500 = lambda request: views.HTTP500View.as_view()(request)  # noqa

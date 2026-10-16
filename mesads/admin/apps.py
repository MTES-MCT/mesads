from django.contrib.admin.apps import AdminConfig


class MesADSAdminConfig(AdminConfig):
    default_site = "mesads.admin.admin_site.MesADSAdminSite"

from django.views.generic import TemplateView

from mesads.app.models import DemandeGestionPrefecture


class PermissionsUserListView(TemplateView):
    template_name = "pages/permissions/permissions_user.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        permissions_prefecture = DemandeGestionPrefecture.objects.filter(
            user=self.request.user,
            statut__in=[
                DemandeGestionPrefecture.ACCEPTE,
                DemandeGestionPrefecture.EXPIRE,
            ],
        )
        context["permissions_prefecture"] = permissions_prefecture
        return context

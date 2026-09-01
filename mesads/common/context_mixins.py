from django.shortcuts import get_object_or_404

from mesads.app.models import ADSManager


class ADSManagerMixin:
    ads_manager_url_kwarg = "manager_id"
    ads_manager = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.ads_manager = get_object_or_404(
            ADSManager,
            pk=self.kwargs[self.ads_manager_url_kwarg],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = self.ads_manager
        return context

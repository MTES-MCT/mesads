from django.shortcuts import get_object_or_404

from mesads.app.models import ADSManager


class ADSManagerContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs.get("manager_id")
        )
        return context

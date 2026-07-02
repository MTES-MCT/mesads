from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    ListView,
    TemplateView,
    UpdateView,
)

from ..forms import (
    TransactionADSForm,
    TransactionDocumentsForm,
    TransactionEnregistrementForm,
    TransactionUpdateForm,
)
from ..models import ADSManager, EntreeRegistreTransaction


class TransactionSelectionADSFormView(CreateView):
    form_class = TransactionADSForm
    model = EntreeRegistreTransaction
    template_name = (
        "pages/ads_register/registre_transactions/transaction_selection_ads.html"
    )

    def get_success_url(self):
        return reverse(
            "app.transaction-documents",
            kwargs={
                "manager_id": get_object_or_404(
                    ADSManager, pk=self.kwargs["manager_id"]
                ).id,
                "entree_id": self.object.id,
            },
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {"ads_manager": get_object_or_404(ADSManager, pk=self.kwargs["manager_id"])}
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        return context


class TransactionDocumentsFormView(UpdateView):
    model = EntreeRegistreTransaction
    form_class = TransactionDocumentsForm
    pk_url_kwarg = "entree_id"
    template_name = (
        "pages/ads_register/registre_transactions/transaction_documents.html"
    )

    def get_success_url(self):
        return reverse(
            "app.transaction-enregistrement"
            if self.object.documents_complet
            else "app.transaction-documents",
            kwargs={
                "manager_id": get_object_or_404(
                    ADSManager, pk=self.kwargs["manager_id"]
                ).id,
                "entree_id": self.object.id,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        return context


class TransactionEnregistrementFormView(UpdateView):
    model = EntreeRegistreTransaction
    form_class = TransactionEnregistrementForm
    pk_url_kwarg = "entree_id"
    template_name = (
        "pages/ads_register/registre_transactions/transaction_enregistrement.html"
    )

    def get_initial(self):
        initial = super().get_initial()
        initial["ancien_exploitant"] = (
            self.object.ancien_exploitant
            if self.object.ancien_exploitant
            else self.object.ads.owner_name
        )
        return initial

    def form_valid(self, form):
        action = form.data.get("action")
        if action is None or action not in ["draft", "validate"]:
            return self.form_invalid(form)

        self.object = form.save()
        if action == "validate":
            self.object.statut = EntreeRegistreTransaction.ENREGISTREE
            self.object.save()

        return_url = (
            reverse("app.transaction-enregistrement", kwargs=self.kwargs)
            if action == "draft"
            else reverse("app.transaction-confirmation", kwargs=self.kwargs)
        )  # todo: replace by the next step url

        return HttpResponseRedirect(return_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        context["entree"] = get_object_or_404(
            EntreeRegistreTransaction, pk=self.kwargs["entree_id"]
        )
        return context


class TransactionConfirmationView(TemplateView):
    template_name = (
        "pages/ads_register/registre_transactions/transaction_confirmation.html"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        context["entree"] = get_object_or_404(
            EntreeRegistreTransaction, pk=self.kwargs["entree_id"]
        )
        return context


class TransactionListView(ListView):
    template_name = "pages/ads_register/registre_transactions/transaction_liste.html"
    context_object_name = "entrees"

    def get_queryset(self):
        return EntreeRegistreTransaction.objects.filter(
            ads__ads_manager__id=self.kwargs["manager_id"]
        ).order_by("-date_transaction")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        return context


class TransactionEditView(UpdateView):
    model = EntreeRegistreTransaction
    form_class = TransactionUpdateForm
    pk_url_kwarg = "entree_id"
    template_name = "pages/ads_register/registre_transactions/transaction_edition.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {"ads_manager": get_object_or_404(ADSManager, pk=self.kwargs["manager_id"])}
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        context["entree"] = get_object_or_404(
            EntreeRegistreTransaction, pk=self.kwargs["entree_id"]
        )
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            ("L'entrée du registre a bien été modifiée."),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "app.transaction-liste",
            kwargs={"manager_id": self.object.ads.ads_manager.id},
        )


class TransactionCreateView(CreateView):
    model = EntreeRegistreTransaction
    form_class = TransactionUpdateForm
    template_name = "pages/ads_register/registre_transactions/transaction_creation.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {"ads_manager": get_object_or_404(ADSManager, pk=self.kwargs["manager_id"])}
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, pk=self.kwargs["manager_id"]
        )
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            ("L'entrée du registre a bien été créée."),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "app.transaction-liste",
            kwargs={"manager_id": self.object.ads.ads_manager.id},
        )

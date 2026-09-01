from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.db.models import Case, Count, F, Q, Value, When
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)
from docxtpl import DocxTemplate

from mesads.common.context_mixins import ADSManagerMixin

from ..forms import (
    AdministrationSearchForm,
    TransactionADSForm,
    TransactionDocumentsForm,
    TransactionEnregistrementForm,
    TransactionUpdateForm,
)
from ..models import ADSManager, EntreeRegistreTransaction


class TransactionSelectionADSFormView(ADSManagerMixin, CreateView):
    form_class = TransactionADSForm
    model = EntreeRegistreTransaction
    template_name = (
        "pages/ads_register/registre_transactions/transaction_selection_ads.html"
    )

    def get_success_url(self):
        return reverse(
            "app.transaction-documents",
            kwargs={
                "manager_id": get_object_or_404(ADSManager, pk=self.ads_manager.id).id,
                "entree_id": self.object.id,
            },
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            (f"Dossier de cession pour l'ADS {self.object.ads.number} créé."),
        )
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"ads_manager": self.ads_manager})
        return kwargs


class TransactionDocumentsFormView(ADSManagerMixin, UpdateView):
    model = EntreeRegistreTransaction
    form_class = TransactionDocumentsForm
    pk_url_kwarg = "entree_id"
    template_name = (
        "pages/ads_register/registre_transactions/transaction_documents.html"
    )

    def form_valid(self, form):
        response = super().form_valid(form)
        action = self.request.POST.get("action")
        messages.success(
            self.request,
            ("Les informations sur les pièces du dossier ont bien été enregistrées.")
            if action == "validate"
            else "Le brouillon a bien été enregistré",
        )
        return response

    def get_success_url(self):
        action = self.request.POST.get("action")
        return (
            reverse(
                "app.transaction-enregistrement",
                kwargs={
                    "manager_id": get_object_or_404(
                        ADSManager, pk=self.ads_manager.id
                    ).id,
                    "entree_id": self.object.id,
                },
            )
            if action == "validate"
            else reverse(
                "app.transaction-liste",
                kwargs={
                    "manager_id": get_object_or_404(
                        ADSManager, pk=self.ads_manager.id
                    ).id,
                },
            )
        )


class TransactionEnregistrementFormView(ADSManagerMixin, UpdateView):
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

        messages.success(
            self.request,
            ("Les informations de l'entrée du registre ont bien été enregistrées.")
            if action == "validate"
            else "Le brouillon a bien été enregistré",
        )

        return_url = (
            reverse(
                "app.transaction-liste",
                kwargs={"manager_id": self.kwargs.get("manager_id")},
            )
            if action == "draft"
            else reverse("app.transaction-confirmation", kwargs=self.kwargs)
        )

        return HttpResponseRedirect(return_url)


class TransactionConfirmationView(ADSManagerMixin, DetailView):
    model = EntreeRegistreTransaction
    pk_url_kwarg = "entree_id"
    template_name = (
        "pages/ads_register/registre_transactions/transaction_confirmation.html"
    )


class TransactionListView(ADSManagerMixin, ListView):
    template_name = "pages/ads_register/registre_transactions/transaction_liste.html"
    context_object_name = "entrees"

    def get_queryset(self):
        return (
            EntreeRegistreTransaction.objects.filter(
                ads__ads_manager__id=self.ads_manager.id
            )
            .select_related("ads")
            .order_by("-date_transaction")
        )


class TransactionEditView(ADSManagerMixin, UpdateView):
    model = EntreeRegistreTransaction
    form_class = TransactionUpdateForm
    pk_url_kwarg = "entree_id"
    template_name = "pages/ads_register/registre_transactions/transaction_edition.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"ads_manager": self.ads_manager})
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request,
            ("L'entrée du registre a bien été modifiée."),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "app.transaction-liste",
            kwargs={"manager_id": self.ads_manager.id},
        )


class TransactionCreateView(ADSManagerMixin, CreateView):
    model = EntreeRegistreTransaction
    form_class = TransactionUpdateForm
    template_name = "pages/ads_register/registre_transactions/transaction_creation.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"ads_manager": self.ads_manager})
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request,
            ("L'entrée du registre a bien été créée."),
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "app.transaction-liste",
            kwargs={"manager_id": self.ads_manager.id},
        )


class ChangementStatutRegistreTransactionView(ADSManagerMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        registre_transaction_public = self.request.POST.get(
            "registre_transaction_public"
        )
        ads_manager = self.ads_manager
        ads_manager.registre_transaction_public = registre_transaction_public == "1"
        ads_manager.save()
        messages.success(
            request,
            (
                "Le registre des transactions a été rendu public"
                if ads_manager.registre_transaction_public is True
                else "Le registre des transactions a été rendu privé"
            ),
        )

        return HttpResponseRedirect(
            redirect_to=reverse(
                "app.transaction-liste", kwargs={"manager_id": ads_manager.id}
            )
        )


class ArreteChangementTitulaireExportView(View):
    def get(self, request, *args, **kwargs):
        entree = get_object_or_404(
            EntreeRegistreTransaction, pk=self.kwargs["entree_id"]
        )
        context = {
            "numero_ads": entree.ads.number,
            "titulaire": entree.nouvel_exploitant,
            "commune": entree.ads.ads_manager.content_object.text(),
        }
        template = DocxTemplate(
            Path(settings.BASE_DIR)
            / "mesads"
            / "app"
            / "docs"
            / "template_arrete_changement_titulaire.docx"
        )

        template.render(context)

        buffer = BytesIO()
        template.save(buffer)
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename="arrete.docx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )


class DemandePiecesJustificativeWordExportView(View):
    def get(self, request, *args, **kwargs):
        entree = get_object_or_404(
            EntreeRegistreTransaction, pk=self.kwargs["entree_id"]
        )
        context = {
            "numero_ads": entree.ads.number,
        }
        template = DocxTemplate(
            Path(settings.BASE_DIR)
            / "mesads"
            / "docs"
            / "courrier_contact_cession.docx"
        )

        template.render(context)

        buffer = BytesIO()
        template.save(buffer)
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename="courrier_type_demande_cession.docx",
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )


class RegistresTransactionsPublicsView(ListView):
    template_name = (
        "pages/ads_register/registre_transactions/registres_transactions_publics.html"
    )
    model = ADSManager
    paginate_by = 50
    context_object_name = "ads_managers"

    def get_form(self):
        return AdministrationSearchForm(self.request.GET)

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(registre_transaction_public=True)
            .order_by("administrator")
        )

        form = self.get_form()
        if form.is_valid():
            departement = form.cleaned_data["departement"]
            if departement:
                qs = qs.filter(administrator__prefecture=departement)
            commune = form.cleaned_data["commune"]
            if commune:
                qs = qs.annotate(
                    name_search=Case(
                        When(content_type__model="epci", then=F("epci__name")),
                        When(
                            content_type__model="prefecture",
                            then=F("prefecture__libelle"),
                        ),
                        When(content_type__model="aeroport", then=F("aeroport__name")),
                        When(content_type__model="commune", then=F("commune__libelle")),
                        default=Value(""),
                    )
                )
                for word in commune.split(" "):
                    qs = qs.filter(name_search__unaccent__icontains=word)

            qs = qs.annotate(
                nombre_entrees_registre=Count(
                    "ads__transactions",
                    filter=Q(
                        ads__transactions__statut=EntreeRegistreTransaction.ENREGISTREE,
                    ),
                )
            )

            if form.is_filled():
                return qs

        return ADSManager.objects.none()

    def get_extra_query_params(self, form):
        extra_query_params = ""
        if form.is_valid():
            if form.cleaned_data.get("departement"):
                extra_query_params = (
                    f"{extra_query_params}&"
                    f"departement={form.cleaned_data.get('departement').id}"
                )
            if form.cleaned_data.get("commune"):
                extra_query_params = (
                    f"{extra_query_params}&commune={form.cleaned_data.get('commune')}"
                )
        return extra_query_params

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        context["form"] = form
        context["extra_query_params"] = self.get_extra_query_params(form)
        return context


class RegistreTransactionsPublicView(ListView):
    template_name = (
        "pages/ads_register/registre_transactions/registre_transactions_public.html"
    )
    model = EntreeRegistreTransaction
    paginate_by = 50
    context_object_name = "entrees"
    ordering = ["-date_transaction"]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(
            ads__ads_manager__id=self.kwargs["manager_id"],
            statut=EntreeRegistreTransaction.ENREGISTREE,
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ads_manager"] = get_object_or_404(
            ADSManager, id=self.kwargs["manager_id"], registre_transaction_public=True
        )
        return context

from django.contrib import admin
from django.db.models import F, Q
from django.db.models.functions import Collate
from django.utils import timezone

from mesads.app.models import DemandeAccesLectureSeule
from mesads.app.services.permissions import log_demande_acces_change

from .demande_gestion_prefecture import AdministratorSelectFilter


@admin.register(DemandeAccesLectureSeule)
class DemandeAccesLectureSeuleAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user"]
    list_display = ("user", "prefecture", "statut", "created_at")

    search_fields = ("user__email",)

    list_filter = ("statut", AdministratorSelectFilter)

    @admin.display(description="Préfecture")
    def prefecture(self, obj):
        return obj.administrator.prefecture

    def save_model(self, request, obj, form, change):
        old_statut = None
        if obj.pk and change:
            old_obj = self.model.objects.get(pk=obj.pk)
            old_statut = old_obj.statut
            if (
                old_obj.statut != DemandeAccesLectureSeule.ACCEPTE
                and obj.statut == DemandeAccesLectureSeule.ACCEPTE
            ):
                obj.accepted_at = timezone.now()

        super().save_model(request, obj, form, change)

        log_demande_acces_change(
            obj, old_statut=old_statut, actor=request.user, request=request
        )

        # TODO: Envoyer un mail de confirmation à l'utilisateur lorsque la
        # demande est acceptée, si on déploie la fonctionnalité au niveau national.

    def delete_model(self, request, obj):
        log_demande_acces_change(
            obj,
            old_statut=obj.statut,
            deleted=True,
            actor=request.user,
            request=request,
        )
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset.select_related("user", "administrator__prefecture"):
            log_demande_acces_change(
                obj,
                old_statut=obj.statut,
                deleted=True,
                actor=request.user,
                request=request,
            )
        super().delete_queryset(request, queryset)

    def get_search_results(self, request, queryset, search_term):
        """The field Users.email uses a non-deterministic collation, which makes
        it impossible to perform a LIKE query on it.

        By overriding this method, we can specify the collation to use for the search.
        """
        use_distinct = True
        queryset = queryset.annotate(collated_email=Collate(F("user__email"), "C"))
        queryset = queryset.filter(
            Q(
                collated_email__icontains=search_term,
            )
            | Q(administrator__prefecture__libelle=search_term)
        )
        return (
            queryset,
            use_distinct,
        )

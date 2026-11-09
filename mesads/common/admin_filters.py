from datetime import date

from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ERROR_FLAG


class DateRangeFilter(admin.FieldListFilter):
    """Filtre de l'admin Django sur une plage de dates (bornes incluses), avec
    deux champs « du » et « au ».

    Fonctionne sur un `DateField` ou un `DateTimeField` (dans ce cas, la date est
    évaluée dans le fuseau horaire courant).

    Utilisation : `list_filter = (("created_at", DateRangeFilter),)`
    """

    template = "admin/filters/date_range.html"

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.is_datetime = field.get_internal_type() == "DateTimeField"
        self.lookup_gte = f"{field_path}__gte"
        self.lookup_lte = f"{field_path}__lte"
        super().__init__(field, request, params, model, model_admin, field_path)

        # Le constructeur parent a extrait nos paramètres de la requête, sous
        # forme de listes : on ne garde que la dernière valeur, si elle est
        # renseignée.
        for param, value in list(self.used_parameters.items()):
            if isinstance(value, list):
                value = value[-1] if value else ""
            if value:
                self.used_parameters[param] = value
            else:
                del self.used_parameters[param]

    def expected_parameters(self):
        return [self.lookup_gte, self.lookup_lte]

    def has_output(self):
        return True

    def queryset(self, request, queryset):
        filters = {}
        for param, value in self.used_parameters.items():
            try:
                parsed = date.fromisoformat(value)
            except ValueError as e:
                raise IncorrectLookupParameters(e)
            lookup = param
            if self.is_datetime:
                # `created_at__gte` -> `created_at__date__gte`
                field_path, _, operator = param.rpartition("__")
                lookup = f"{field_path}__date__{operator}"
            filters[lookup] = parsed
        return queryset.filter(**filters)

    def choices(self, changelist):
        # Un seul « choix », qui transmet au template ce dont le formulaire a
        # besoin : les autres paramètres de la liste (filtres, recherche, tri)
        # sont conservés en champs cachés.
        own_params = {*self.expected_parameters(), ERROR_FLAG}
        yield {
            "selected": bool(self.used_parameters),
            "value_gte": self.used_parameters.get(self.lookup_gte, ""),
            "value_lte": self.used_parameters.get(self.lookup_lte, ""),
            "hidden_params": [
                (name, value)
                for name, value in changelist.params.items()
                if name not in own_params
            ],
            "reset_query_string": changelist.get_query_string(
                remove=self.expected_parameters()
            ),
        }

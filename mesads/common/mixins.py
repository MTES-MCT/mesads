from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Manager to add a soft delete feature to a model.

    This manager overrides the `get_queryset` method to filter out objects that
    have a `deleted_at` field set.
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteMixin(models.Model):
    """Mixin to add a soft delete feature to a model.

    This mixin adds a `deleted_at` field to the model, and overrides the
    `delete` method to set the field to True instead of actually deleting the
    object.
    """

    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Date de suppression",
        help_text=(
            "Date de suppression de l'objet. "
            "Si cette date est renseignée, l'objet est considéré comme supprimé."
        ),
    )

    with_deleted = models.Manager()
    objects = SoftDeleteManager()

    class Meta:
        default_manager_name = "objects"
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, using=None, keep_parents=False):
        """Supprime réellement l'objet."""
        return super().delete(
            using=using,
            keep_parents=keep_parents,
        )


class SmartValidationMixin:
    """Override clean() to only validate fields that have changed."""

    SMART_VALIDATION_WATCHED_FIELDS = None

    def __init__(self, *args, **kwargs):
        """Store the initial value for the watched fields."""
        assert self.SMART_VALIDATION_WATCHED_FIELDS
        super().__init__(*args, **kwargs)
        self.__smart_validation_initial_values = {
            name: getattr(self, name)
            for name in self.SMART_VALIDATION_WATCHED_FIELDS.keys()
        }

    def clean(self, *args, **kwargs):
        """If any of the watched fields changed, revalidate it."""
        super().clean(*args, **kwargs)
        for key, initial_value in self.__smart_validation_initial_values.items():
            if getattr(self, key) != initial_value:
                validator = self.SMART_VALIDATION_WATCHED_FIELDS[key]
                try:
                    validator(self, getattr(self, key))
                except Exception as exc:
                    raise ValidationError({key: exc})


class CharFieldsStripperMixin:
    """Strip all char fields."""

    def clean(self, *args, **kwargs):
        for field in self._meta.fields:
            if isinstance(field, models.CharField):
                value = getattr(self, field.name)
                # Usually our CharFields are not nullable, but make sure we
                # don't attempt to strip None.
                if value is not None:
                    stripped = self.strip(value)
                    setattr(self, field.name, stripped)
        return super().clean(*args, **kwargs)

    def strip(self, value):
        value = value.strip()
        if value == "-":
            value = ""
        return value

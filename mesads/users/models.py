from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.contrib.auth.models import (
    AbstractUser,
    UserManager,
)
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserQuerySet(models.QuerySet):
    @staticmethod
    def permission_mesads_q():
        """Condition vraie si l'utilisateur a au moins une permission sur
        MesADS (admin, gestionnaire ADS, gestionnaire de préfecture, inspecteur,
        propriétaire de véhicule relais)."""
        ADSManagerRequest = apps.get_model("app", "ADSManagerRequest")
        DemandeAccesLectureSeule = apps.get_model("app", "DemandeAccesLectureSeule")
        DemandeGestionPrefecture = apps.get_model("app", "DemandeGestionPrefecture")
        Proprietaire = apps.get_model("vehicules_relais", "Proprietaire")

        user = OuterRef("pk")
        return (
            Q(is_staff=True)
            | Q(is_superuser=True)
            | Q(Exists(ADSManagerRequest.objects.filter(user=user, accepted=True)))
            | Q(
                Exists(
                    DemandeAccesLectureSeule.objects.filter(
                        user=user, statut=DemandeAccesLectureSeule.ACCEPTE
                    )
                )
            )
            | Q(
                Exists(
                    DemandeGestionPrefecture.objects.filter(
                        user=user, statut=DemandeGestionPrefecture.ACCEPTE
                    )
                )
            )
            | Q(Exists(Proprietaire.objects.filter(users=user)))
        )

    def with_permission_mesads(self):
        return self.filter(self.permission_mesads_q())

    def without_permission_mesads(self):
        return self.exclude(self.permission_mesads_q())


class EmailUserManager(UserManager.from_queryset(UserQuerySet)):
    """Custom manager for users, similar to UserManager, but using email only
    for authentication."""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'adresse email doit être renseignée")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields["is_staff"] is not True:
            raise ValueError("Le superuser doit avoir is_staff=True")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """This model is a copy of django.contrib.auth.models.AbstractUser, except
    username is removed, email is unique and we set the custom manager to
    EmailUserManager.

    The goal is to remain compatible with django admin, but have email
    authentication instead of username authentication.
    """

    username = None
    email = models.EmailField(
        _("email address"),
        db_collation="case_insensitive",
        unique=True,
        error_messages={
            "unique": "Un utilisateur avec cet email existe déjà.",
        },
    )

    proconnect_sub = models.UUIDField(
        "Identifiant unique proconnect", null=True, blank=True, unique=True
    )
    proconnect_uid = models.CharField("ID chez le FI", default="", blank=True)
    proconnect_idp_id = models.UUIDField("Identifiant du FI", null=True, blank=True)
    proconnect_siret = models.CharField(
        "SIRET",
        default="",
        blank=True,
    )
    proconnect_chorusdt = models.CharField(
        "Entité ministérielle / Matricule Agent",
        default="",
        blank=True,
    )
    proconnect_link_allowed = models.BooleanField(
        "Autoriser le rattachement ProConnect par email",
        default=False,
        help_text=(
            "Si coché, la prochaine connexion ProConnect avec l'adresse email de "
            "ce compte y sera rattachée, même si le compte n'a pas encore "
            "d'identifiant ProConnect. Ne cocher qu'après avoir vérifié l'identité "
            "de l'utilisateur. L'autorisation est automatiquement retirée une fois "
            "le rattachement effectué."
        ),
    )

    delete_notification_sent_at = models.DateTimeField(
        verbose_name="Date d'envoi de notification préalable à la suppression",
        null=True,
        blank=True,
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = EmailUserManager()

    @property
    def has_permission_mesads(self):
        return User.objects.filter(pk=self.pk).with_permission_mesads().exists()

    @property
    def prefecture_consultation(self):
        demande = self.demandes_acces_lecture_seule.filter(statut="ACCEPTE").first()
        return demande.administrator.prefecture if demande else None

    def show_notation(self) -> bool:
        note_utilisateur = NoteUtilisateur.objects.filter(user=self).first()
        today = timezone.now().date()
        one_month_ago = today - relativedelta(months=1)
        six_months_ago = today - relativedelta(months=6)
        if note_utilisateur:
            if note_utilisateur.derniere_note is None:
                if note_utilisateur.dernier_affichage is None:
                    return True
                else:
                    return note_utilisateur.dernier_affichage < one_month_ago
            else:
                if note_utilisateur.derniere_note < six_months_ago:
                    return note_utilisateur.dernier_affichage < one_month_ago
                else:
                    return False

        else:
            if UserAuditEntry.objects.filter(user=self, action="login").count() > 1:
                return True
            else:
                return False


class UserAuditEntry(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    action = models.CharField(max_length=64, null=False, blank=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="audit_entries", null=True
    )
    ip = models.GenericIPAddressField(null=True)
    body = models.TextField(null=False, blank=True)

    class Meta:
        verbose_name = "Historique des connexions"
        verbose_name_plural = "Historiques des connexions"


class PermissionAuditEntry(models.Model):
    """Journal des changements de permissions et d'identité des utilisateurs."""

    class Action(models.TextChoices):
        PROCONNECT_LINK_ALLOWED = (
            "proconnect_link_allowed",
            "Rattachement ProConnect par email autorisé",
        )
        PROCONNECT_LINK_REVOKED = (
            "proconnect_link_revoked",
            "Rattachement ProConnect par email révoqué",
        )
        PROCONNECT_LINKED = (
            "proconnect_linked",
            "Compte rattaché à ProConnect par email",
        )

    created_at = models.DateTimeField("Date", auto_now_add=True, db_index=True)
    action = models.CharField("Action", max_length=64, choices=Action.choices)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="permission_audit_entries",
        verbose_name="Utilisateur concerné",
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Auteur",
        help_text="Vide si l'action a été réalisée automatiquement par l'application.",
    )
    ip = models.GenericIPAddressField("Adresse IP", null=True, blank=True)
    details = models.JSONField("Détails", default=dict, blank=True)

    class Meta:
        verbose_name = "Historique des changements de permissions"
        verbose_name_plural = "Historiques des changements de permissions"
        ordering = ("-created_at",)


class NoteUtilisateur(models.Model):
    MINIMUM_NOTE = 1
    MAXIMUM_NOTE = 5

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="note")
    dernier_affichage = models.DateField(
        verbose_name="Date du dernier affichage du composant de notation", null=True
    )
    derniere_note = models.DateField(
        verbose_name="Date de la dernière notation", null=True
    )

    note_facilite = models.PositiveSmallIntegerField(
        verbose_name="Note de facilité d'usage (sur 5)",
        null=True,
        validators=[MinValueValidator(MINIMUM_NOTE), MaxValueValidator(MAXIMUM_NOTE)],
    )

    note_qualite = models.PositiveSmallIntegerField(
        verbose_name="Note de qualité de service (sur 5)",
        null=True,
        validators=[MinValueValidator(MINIMUM_NOTE), MaxValueValidator(MAXIMUM_NOTE)],
    )

    class Meta:
        verbose_name = "Note de l'utilisateur"
        verbose_name_plural = "Notes des utilisateurs"

import factory

from ..models import NoteUtilisateur, User, UserAuditEntry


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")

    class Params:
        superuser = factory.Trait(
            is_superuser=True,
            is_staff=True,
        )


class UserAuditEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserAuditEntry


class NoteUtilisateurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NoteUtilisateur

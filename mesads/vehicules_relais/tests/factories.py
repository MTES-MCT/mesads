import factory

from mesads.fradm.tests.factories import PrefectureFactory
from mesads.vehicules_relais.models import Proprietaire, Vehicule


class ProprietaireFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proprietaire

    nom = factory.Faker("last_name", locale="fr_FR")


class VehiculeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicule

    proprietaire = factory.SubFactory(ProprietaireFactory)
    departement = factory.SubFactory(PrefectureFactory)
    numero = factory.Sequence(lambda n: f"{n}")

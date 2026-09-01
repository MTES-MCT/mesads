from django.db import models
from solo.models import SingletonModel


class NewsLetter(models.Model):
    newsletter_date = models.DateField(verbose_name="Date d'envoi")

    newsletter = models.FileField(
        verbose_name="Newsletter (format PDF)", upload_to="newsletters/"
    )

    class Meta:
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"

    def __str__(self):
        return f"Newsletter du {self.newsletter_date.strftime('%d/%m/%Y')}"


class BandeauInformation(SingletonModel):
    visible = models.BooleanField(verbose_name="Visibilité bandeau", default=False)
    titre = models.CharField(
        verbose_name="Titre", max_length=128, default="", blank=True
    )
    message = models.TextField(verbose_name="Message", default="", blank=True)

    class Meta:
        verbose_name = "Bandeau d'information"

    def __str__(self):
        return "Bandeau d'information"

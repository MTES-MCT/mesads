from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import BandeauInformation, NewsLetter

admin.site.register(NewsLetter)
admin.site.register(BandeauInformation, SingletonModelAdmin)

from django.contrib import admin
from .models import Beneficiaire, Aidant, Experimentation, Fichier

admin.site.register(Beneficiaire)
admin.site.register(Aidant)
admin.site.register(Experimentation)
admin.site.register(Fichier)
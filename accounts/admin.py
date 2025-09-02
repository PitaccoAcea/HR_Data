from django.contrib import admin

from .models import Utente, GruppoAutorizzativo, UtenteGruppo


admin.site.register(Utente)
admin.site.register(GruppoAutorizzativo)
admin.site.register(UtenteGruppo)

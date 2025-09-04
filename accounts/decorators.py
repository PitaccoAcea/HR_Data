# accounts/decorators.py
# Decoratore per limitare l’accesso a utenti appartenenti a uno o più gruppi applicativi.
# Funziona con autenticazione integrata (REMOTE_USER) e gruppi salvati nel DB del sito.

from functools import wraps
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

def gruppo_richiesto(*nomi_gruppo, allow_superuser=False):
    """
    Esempi:
        @gruppo_richiesto("admin")
        @gruppo_richiesto("admin", "hr_manager")
        @gruppo_richiesto("admin", allow_superuser=True)

    :param nomi_gruppo: uno o più nomi di gruppo (accounts_gruppoautorizzativo.nome)
    :param allow_superuser: se True, lascia passare superuser (se lo gestisci nel tuo modello)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # 1) Estrai lo username da REMOTE_USER (ACEA\mrossi -> mrossi)
            raw_username = (request.META.get("REMOTE_USER") or "").strip()
            username = raw_username.split("\\")[-1] if raw_username else ""

            # Se non abbiamo username, neghiamo l’accesso
            if not username:
                return render(request, "403.html")

            # 2) Import "lazy" per evitare problemi di import circolari
            from .models import Utente, UtenteGruppo

            # 3) Recupera l'utente app dal DB
            try:
                utente = Utente.objects.get(username=username)
            except Utente.DoesNotExist:
                # Non censire utente = niente accesso
                return render(request, "403.html")

            # 4) Opzionale: superuser bypass (se nel tuo modello gestisci questo flag)
            if allow_superuser and getattr(utente, "is_superuser", False):
                return view_func(request, *args, **kwargs)

            # 5) Recupera i gruppi dell’utente
            gruppi_utente = set(
                UtenteGruppo.objects.filter(utente=utente).values_list("gruppo__nome", flat=True)
            )

            # 6) Verifica appartenenza ad almeno uno dei gruppi richiesti
            richiesti = set(nomi_gruppo)
            if not richiesti.intersection(gruppi_utente):
                return render(request, "403.html")

            # OK, l'utente è autorizzato
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

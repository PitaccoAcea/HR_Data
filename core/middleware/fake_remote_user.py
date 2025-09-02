from django.contrib.auth import get_user_model, login
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from accounts.models import Utente, GruppoAutorizzativo, UtenteGruppo

User = get_user_model()

class FakeRemoteUserMiddleware(MiddlewareMixin):
    """
    Middleware per simulare REMOTE_USER in sviluppo (DEBUG=True)
    """
    def process_request(self, request):
        if settings.DEBUG:
            fake_username = "TI\\a37400c"
            request.META["REMOTE_USER"] = fake_username

            # Crea utente Django (se necessario)
            user, _ = User.objects.get_or_create(username=fake_username, defaults={
                "is_active": True,
                "first_name": "Fake",
                "last_name": "Dev",
            })

            request.user = user
            request.session["_auth_user_id"] = user.pk
            request.session["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
            request.session["_auth_user_hash"] = user.get_session_auth_hash()

            # Crea utente "interno" nella nostra tabella Utente (se non esiste)
            utente, _ = Utente.objects.get_or_create(username=fake_username, defaults={
                "cognome": "Dev",
                "nome": "Fake",
                "attivo": True
            })

            # Crea gruppo admin se non esiste
            gruppo_admin, _ = GruppoAutorizzativo.objects.get_or_create(nome="admin")

            # Associa utente al gruppo admin (se non già associato)
            UtenteGruppo.objects.get_or_create(
                utente=utente,
                gruppo=gruppo_admin,
            )

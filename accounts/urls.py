from django.urls import path
from . import views
from .views import toggle_attivo


urlpatterns = [
path("gestione-utenti/", views.gestione_utenti, name="gestione_utenti"),
path('info-utenti/', views.info_utenti, name='info_utenti'),
path('toggle-attivo/<int:utente_id>/', toggle_attivo, name='toggle_attivo'),
path('gestione-gruppi/', views.gestione_gruppi, name='gestione_gruppi'),
]
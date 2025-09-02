from django.urls import path
from . import views


urlpatterns = [
path("gestione-utenti/", views.gestione_utenti, name="gestione_utenti"),
]
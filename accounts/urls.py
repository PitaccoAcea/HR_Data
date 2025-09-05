from django.urls import path
from . import views
from .views import toggle_attivo


urlpatterns = [
path("gestione-utenti/", views.gestione_utenti, name="gestione_utenti"),
path('info-utenti/', views.info_utenti, name='info_utenti'),
path('toggle-attivo/<int:utente_id>/', toggle_attivo, name='toggle_attivo'),
path('gestione-gruppi/', views.gestione_gruppi, name='gestione_gruppi'),
path('menu/', views.menu_gestione, name='menu_gestione'),
path('menu/nuovo/', views.menu_voce_edit, name='menu_voce_new'),
path('menu/edit/<int:voce_id>/', views.menu_voce_edit, name='menu_voce_edit'),
path('menu/delete/<int:voce_id>/', views.menu_voce_delete, name='menu_voce_delete'),
path('menu/toggle/<int:voce_id>/', views.menu_toggle_active, name='menu_toggle_active'),
path('menu/reorder/', views.menu_reorder, name='menu_reorder'),
path('menu/preview/', views.menu_preview, name='menu_preview'),
]
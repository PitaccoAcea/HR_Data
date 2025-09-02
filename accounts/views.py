import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ldap3 import Server, Connection, NTLM, ALL
from .models import Utente, GruppoAutorizzativo, UtenteGruppo
from .forms import CercaUtenteLDAPForm, AssociaGruppoForm


LDAP_SERVER = 'LDAP://DC=aceaspa,DC=it'
BASE_DN = 'DC=aceaspa,DC=it'


@login_required
def gestione_utenti(request):
    context = {}
    username_remoto = request.META.get("REMOTE_USER", "")

    # Controllo gruppo autorizzato
    try:
        utente = Utente.objects.get(username=username_remoto)
        gruppi = UtenteGruppo.objects.filter(utente=utente).values_list('gruppo__nome', flat=True)
        if "admin" not in gruppi:
            return render(request, "403.html")
    except Utente.DoesNotExist:
        return render(request, "403.html")

    # Form ricerca LDAP
    ldap_results = []
    if request.method == "POST" and 'cerca' in request.POST:
        form = CercaUtenteLDAPForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            ldap_results = cerca_ldap(query)
    else:
        form = CercaUtenteLDAPForm()

    # Lista utenti locali + gruppi
    utenti = Utente.objects.all().order_by("cognome", "nome")
    associa_form = AssociaGruppoForm()

    context.update({
        "form": form,
        "ldap_results": ldap_results,
        "utenti": utenti,
        "associa_form": associa_form,
    })
    return render(request, "accounts/gestione_utenti.html", context)


def cerca_ldap(query):
    from ldap3 import Server, Connection, ALL

    server = Server('aceaspa.it', get_info=ALL)

    try:
        conn = Connection(server, auto_bind=True)  # bind anonimo e sicuro
    except Exception as e:
        print("Errore di connessione LDAP:", e)
        return []

    # Filtro per displayName con wildcard finale come in C#
    filtro = f"(displayName={query.strip()}*)"

    try:
        conn.search(
            search_base='DC=aceaspa,DC=it',
            search_filter=filtro,
            attributes=["displayName", "mail"]
        )
        print(f"LDAP risultati trovati: {len(conn.entries)}")
    except Exception as e:
        print("Errore durante la ricerca LDAP:", e)
        return []

    risultati = []
    for e in conn.entries:
        risultati.append({
            "displayName": str(e.displayName),
            "email": str(e.mail) if e.mail else "",
        })

    return risultati

    
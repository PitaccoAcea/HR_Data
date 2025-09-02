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
    server = Server('aceaspa.it', get_info=ALL)

    # Bind anonimo, visto che è supportato
    conn = Connection(server, auto_bind=True)

    filtro = f"(&(objectClass=user)(|(sn=*{query}*)(givenName=*{query}*)))"
    conn.search(
        search_base=BASE_DN,
        search_filter=filtro,
        attributes=["sAMAccountName", "givenName", "sn", "mail"]
    )

    risultati = []
    for e in conn.entries:
        risultati.append({
            "username": str(e.sAMAccountName),
            "nome": str(e.givenName),
            "cognome": str(e.sn),
            "email": str(e.mail) if e.mail else "",
        })
    return risultati

    
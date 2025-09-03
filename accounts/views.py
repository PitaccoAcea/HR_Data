import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ldap3 import Server, Connection, SASL, GSSAPI, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
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


def cerca_ldap(query: str, attributi=None, max_risultati=50):
    """
    Esegue una ricerca LDAP utilizzando l'autenticazione integrata Windows (GSSAPI).
    
    :param query: stringa da cercare nel displayName (wildcard automatica).
    :param attributi: lista di attributi da recuperare.
    :param max_risultati: numero massimo di risultati da restituire.
    :return: lista di dizionari con i dati LDAP trovati.
    """
    if attributi is None:
        attributi = ["displayName", "mail", "sAMAccountName"]

    filtro = f'(displayName=*{query}*)'
    risultati = []

    try:
        server = Server('ahinfrapdc01gcp.aceaspa.it', get_info=ALL)
        conn = Connection(
            server,
            authentication=SASL,
            sasl_mechanism=GSSAPI,
            auto_bind=True
        )

        conn.search(
            search_base='DC=aceaspa,DC=it',
            search_filter=filtro,
            search_scope=SUBTREE,
            attributes=attributi,
            size_limit=max_risultati
        )

        for entry in conn.entries:
            item = {}
            for attr in attributi:
                val = entry[attr].value
                item[attr] = val if val is not None else ""
            risultati.append(item)

        conn.unbind()

    except LDAPException as e:
        print(f"Errore LDAP: {e}")
    except Exception as ex:
        print(f"Errore generale nella ricerca LDAP: {ex}")

    return risultati


    
    
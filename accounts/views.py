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


# def cerca_ldap(query):
#     from ldap3 import Server, Connection, ALL

#     server = Server('aceaspa.it', get_info=ALL)

#     try:
#         conn = Connection(server, auto_bind=True)  # bind anonimo e sicuro
#     except Exception as e:
#         print("Errore di connessione LDAP:", e)
#         return []

#     # Filtro per displayName con wildcard finale come in C#
#     #filtro = f"(displayName={query.strip()}*)"
#     filtro = f"(&(objectClass=user)(displayName={query.strip()}*))"

#     try:
#         conn.search(
#             search_base='DC=aceaspa,DC=it',
#             search_filter=filtro,
#             attributes=["displayName", "mail"]
#         )
#         print(f"LDAP risultati trovati: {len(conn.entries)}")
#     except Exception as e:
#         print("Errore durante la ricerca LDAP:", e)
#         return []

#     risultati = []
#     for e in conn.entries:
#         risultati.append({
#             "displayName": str(e.displayName),
#             "email": str(e.mail) if e.mail else "",
#         })

#     return risultati

def cerca_ldap(query):
    from ldap3 import Server, Connection, ALL, SUBTREE, NTLM
    import os
    
    # Equivalente di ConfigurationManager.AppSettings.Get("ADPath")
    # Se non hai il path specifico, usa il domain controller
    ad_path = "aceaspa.it"  # o il path specifico dal tuo config
    
    server = Server(ad_path, get_info=ALL)

    try:
        # Equivalente di AuthenticationType = AuthenticationTypes.Secure
        # auto_bind=True con NTLM dovrebbe usare le credenziali dell'utente corrente
        conn = Connection(
            server, 
            auto_bind=True,
            authentication=NTLM,  # Equivalente di Secure authentication
            raise_exceptions=True
        )
    except Exception as e:
        print("Errore di connessione LDAP:", e)
        return []

    # Filtro identico al C#
    filtro = f"(displayName=*{query.strip()}*)"

    try:
        # Parametri corrispondenti al C#
        conn.search(
            search_base='DC=aceaspa,DC=it',  # Equivalente del root path
            search_filter=filtro,
            search_scope=SUBTREE,  # SearchScope.Subtree
            attributes=["displayName", "mail"],  # PropertiesToLoad
            size_limit=100,  # SizeLimit = 100
            time_limit=30  # ClientTimeout = 30 secondi
        )
        
        print(f"LDAP risultati trovati: {len(conn.entries)}")
        
    except Exception as e:
        print("Errore durante la ricerca LDAP:", e)
        return []

    # Costruisci la lista risultati come il C#
    risultati = []
    for entry in conn.entries:
        if entry.displayName:
            # Il C# aggiunge ogni displayName alla lista
            display_name = str(entry.displayName)
            email = str(entry.mail) if entry.mail else ""
            
            risultati.append({
                "displayName": display_name,
                "email": email,
            })

    conn.unbind()
    
    # Ordina per displayName (equivalente del SortOption in C#)
    risultati.sort(key=lambda x: x["displayName"])
    
    return risultati
    
    
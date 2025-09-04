import os
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ldap3 import Server, Connection, SASL, GSSAPI, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
from .models import Utente, GruppoAutorizzativo, UtenteGruppo
from .forms import CercaUtenteLDAPForm, AssociaGruppoForm, GruppoAutorizzativoForm
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django import template
from urllib.parse import urlencode
from .decorators import gruppo_richiesto
register = template.Library()


LDAP_SERVER = 'LDAP://DC=aceaspa,DC=it'
BASE_DN = 'DC=aceaspa,DC=it'


@login_required
@gruppo_richiesto("admin")
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

from ldap3 import Server, Connection, ALL, SUBTREE, SASL, GSSAPI
from ldap3.core.exceptions import LDAPException
from datetime import datetime

def cerca_ldap_completo(query: str, attributi=None, max_risultati=50, filtro_personalizzato=None):
    """
    Esegue una ricerca LDAP completa con tutti i principali attributi Active Directory.
    
    :param query: stringa da cercare (usata in displayName, cn, sAMAccountName se filtro_personalizzato è None)
    :param attributi: lista di attributi da recuperare (se None, usa attributi predefiniti completi)
    :param max_risultati: numero massimo di risultati da restituire
    :param filtro_personalizzato: filtro LDAP personalizzato (se specificato, ignora query)
    :return: lista di dizionari con i dati LDAP trovati
    """
    
    # Attributi completi Active Directory
    if attributi is None:
        attributi = [
            # Identificativi di base
            "displayName",           # Nome completo visualizzato
            "cn",                   # Common Name
            "sAMAccountName",       # Username di login
            "userPrincipalName",    # UPN (email di login)
            "distinguishedName",    # DN completo
            "objectGUID",           # GUID univoco
            
            # Informazioni personali
            "givenName",            # Nome
            "sn",                   # Cognome  
            "initials",             # Iniziali
            "title",                # Titolo/Ruolo
            "description",          # Descrizione
            
            # Contatti
            "mail",                 # Email principale
            "proxyAddresses",       # Tutti gli indirizzi email
            "telephoneNumber",      # Telefono principale
            "mobile",               # Cellulare
            "facsimileTelephoneNumber", # Fax
            "homePhone",            # Telefono casa
            "pager",                # Cercapersone
            "ipPhone",              # Telefono IP
            
            # Indirizzo
            "streetAddress",        # Indirizzo
            "l",                    # Città (locality)
            "st",                   # Stato/Provincia
            "postalCode",           # CAP
            "c",                    # Paese (country)
            "co",                   # Paese (nome completo)
            "countryCode",          # Codice paese
            
            # Organizzazione
            "company",              # Azienda
            "department",           # Dipartimento
            "division",             # Divisione
            "ou",                   # Organizational Unit
            "manager",              # Manager (DN)
            "directReports",        # Dipendenti diretti (DN)
            "employeeID",           # ID Dipendente
            "employeeType",         # Tipo dipendente
            "employeeNumber",       # Numero dipendente
            
            # Informazioni tecniche
            "lastLogon",            # Ultimo login
            "lastLogonTimestamp",   # Timestamp ultimo login
            "pwdLastSet",           # Data cambio password
            "accountExpires",       # Scadenza account
            "userAccountControl",   # Controllo account (attivo/disattivo)
            "badPwdCount",          # Conteggio password errate
            "logonCount",           # Conteggio login
            "lockoutTime",          # Tempo di blocco
            
            # Appartenenza gruppi
            "memberOf",             # Gruppi di appartenenza
            "primaryGroupID",       # ID gruppo primario
            
            # Informazioni aggiuntive
            "info",                 # Note/Informazioni
            "comment",              # Commenti
            "wWWHomePage",          # Homepage
            "url",                  # URL
            "whenCreated",          # Data creazione
            "whenChanged",          # Data ultima modifica
            "adminDisplayName",     # Nome admin
            "extensionAttribute1",  # Attributi estesi personalizzati
            "extensionAttribute2",
            "extensionAttribute3",
            "extensionAttribute4",
            "extensionAttribute5",
            
            # Certificati e sicurezza
            "userCertificate",      # Certificato utente
            "userSMIMECertificate", # Certificato S/MIME
            
            # Terminal Services / Remote Desktop
            "msDS-User-Account-Control-Computed", # Controlli account computati
            "msTSAllowLogon",       # Permessi Terminal Server
            
            # Exchange (se presente)
            "mailNickname",         # Alias Exchange
            "msExchMailboxGuid",    # GUID mailbox Exchange
            "msExchRecipientDisplayType", # Tipo destinatario Exchange
        ]
    
    # Costruzione del filtro
    if filtro_personalizzato:
        filtro = filtro_personalizzato
    else:
        # Ricerca in multipli campi con OR
        query_clean = query.strip()
        filtro = f"""(&(objectClass=user)
                     (|(displayName=*{query_clean}*)
                       (cn=*{query_clean}*)
                       (sAMAccountName=*{query_clean}*)
                       (givenName=*{query_clean}*)
                       (sn=*{query_clean}*)
                       (mail=*{query_clean}*)
                       (userPrincipalName=*{query_clean}*)))"""
    
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
                try:
                    val = entry[attr].value
                    
                    # Gestione speciale per alcuni tipi di attributi
                    if attr in ['lastLogon', 'lastLogonTimestamp', 'pwdLastSet', 'accountExpires', 'lockoutTime', 'whenCreated', 'whenChanged']:
                        # Conversione timestamp Windows/LDAP in formato leggibile
                        if val and val != 0:
                            if isinstance(val, datetime):
                                item[attr] = val.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                item[attr] = str(val)
                        else:
                            item[attr] = ""
                    
                    elif attr == 'userAccountControl':
                        # Decodifica UserAccountControl
                        if val:
                            uac_flags = []
                            if val & 0x0002: uac_flags.append("ACCOUNT_DISABLED")
                            if val & 0x0008: uac_flags.append("HOMEDIR_REQUIRED") 
                            if val & 0x0010: uac_flags.append("LOCKOUT")
                            if val & 0x0020: uac_flags.append("PASSWD_NOTREQD")
                            if val & 0x0040: uac_flags.append("PASSWD_CANT_CHANGE")
                            if val & 0x0080: uac_flags.append("ENCRYPTED_TEXT_PASSWORD_ALLOWED")
                            if val & 0x0100: uac_flags.append("TEMP_DUPLICATE_ACCOUNT")
                            if val & 0x0200: uac_flags.append("NORMAL_ACCOUNT")
                            if val & 0x0800: uac_flags.append("INTERDOMAIN_TRUST_ACCOUNT")
                            if val & 0x1000: uac_flags.append("WORKSTATION_TRUST_ACCOUNT")
                            if val & 0x2000: uac_flags.append("SERVER_TRUST_ACCOUNT")
                            if val & 0x10000: uac_flags.append("DONT_EXPIRE_PASSWD")
                            if val & 0x20000: uac_flags.append("MNS_LOGON_ACCOUNT")
                            if val & 0x40000: uac_flags.append("SMARTCARD_REQUIRED")
                            if val & 0x80000: uac_flags.append("TRUSTED_FOR_DELEGATION")
                            if val & 0x100000: uac_flags.append("NOT_DELEGATED")
                            if val & 0x200000: uac_flags.append("USE_DES_KEY_ONLY")
                            if val & 0x400000: uac_flags.append("DONT_REQUIRE_PREAUTH")
                            if val & 0x800000: uac_flags.append("PASSWORD_EXPIRED")
                            if val & 0x1000000: uac_flags.append("TRUSTED_TO_AUTHENTICATE_FOR_DELEGATION")
                            
                            item[attr] = f"{val} ({', '.join(uac_flags)})"
                            item[f"{attr}_raw"] = val
                            item["account_active"] = not bool(val & 0x0002)  # Non è disabilitato
                        else:
                            item[attr] = ""
                            item["account_active"] = False
                    
                    # elif attr in ['memberOf', 'directReports', 'proxyAddresses']:
                    #     # Attributi multi-valore
                    #     if val:
                    #         if isinstance(val, list):
                    #             item[attr] = val
                    #             item[f"{attr}_count"] = len(val)
                    #         else:
                    #             item[attr] = [str(val)]
                    #             item[f"{attr}_count"] = 1
                    #     else:
                    #         item[attr] = []
                    #         item[f"{attr}_count"] = 0

                    elif attr == 'memberOf':
                        # Estrai i nomi leggibili dei gruppi da DN
                        def estrai_nome_gruppo(dn):
                            try:
                                return dn.split(',')[0].replace('CN=', '')
                            except:
                                return dn

                        gruppi = []
                        if val:
                            if isinstance(val, list):
                                gruppi = [estrai_nome_gruppo(g) for g in val]
                            else:
                                gruppi = [estrai_nome_gruppo(str(val))]

                        item['memberOf'] = gruppi
                        item['memberOf_count'] = len(gruppi)
                    
                    elif attr == 'manager' and val:
                        # Estrai solo il nome del manager dal DN
                        item[attr] = str(val)
                        # Estrai il CN dal DN del manager
                        try:
                            cn_part = str(val).split(',')[0]
                            if cn_part.startswith('CN='):
                                item['manager_name'] = cn_part[3:]
                            else:
                                item['manager_name'] = cn_part
                        except:
                            item['manager_name'] = str(val)
                    
                    else:
                        # Attributi standard
                        item[attr] = str(val) if val is not None else ""
                        
                except Exception as attr_error:
                    # Se c'è un errore con un singolo attributo, continua con gli altri
                    item[attr] = f"ERRORE: {attr_error}"
            
            # Aggiungi informazioni calcolate
            item['full_name'] = f"{item.get('givenName', '')} {item.get('sn', '')}".strip()
            item['is_person'] = bool(item.get('givenName') or item.get('sn'))
            
            risultati.append(item)
        
        conn.unbind()
        
    except LDAPException as e:
        print(f"Errore LDAP: {e}")
    except Exception as ex:
        print(f"Errore generale nella ricerca LDAP: {ex}")
    
    return risultati


def cerca_ldap_semplice(query: str, max_risultati=50):
    """
    Versione semplificata per ricerche veloci con solo i campi principali
    """
    attributi_base = [
    "displayName", "givenName", "sn", "sAMAccountName", 
    "mail", "userPrincipalName", "title", "department", 
    "company", "telephoneNumber", "mobile", "manager",
    "userAccountControl"  # NECESSARIO per account_active
]

    
    return cerca_ldap_completo(query, attributi_base, max_risultati)


def cerca_utente_per_username(username: str):
    """
    Cerca un utente specifico per sAMAccountName
    """
    filtro = f"(sAMAccountName={username})"
    risultati = cerca_ldap_completo("", filtro_personalizzato=filtro, max_risultati=1)
    return risultati[0] if risultati else None


def cerca_utenti_attivi(query: str, max_risultati=50):
    """
    Cerca solo utenti attivi (non disabilitati)
    """
    filtro = f"""(&(objectClass=user)
                 (!(userAccountControl:1.2.840.113556.1.4.803:=2))
                 (|(displayName=*{query.strip()}*)
                   (cn=*{query.strip()}*)
                   (sAMAccountName=*{query.strip()}*)
                   (givenName=*{query.strip()}*)
                   (sn=*{query.strip()}*)))"""
    
    return cerca_ldap_completo("", filtro_personalizzato=filtro, max_risultati=max_risultati)


# Esempio di utilizzo
if __name__ == "__main__":
    # Test con tutti gli attributi
    print("=== RICERCA COMPLETA ===")
    risultati = cerca_ldap_completo("mario", max_risultati=3)
    
    for i, utente in enumerate(risultati, 1):
        print(f"\n--- UTENTE {i} ---")
        print(f"Nome: {utente.get('displayName')}")
        print(f"Email: {utente.get('mail')}")
        print(f"Username: {utente.get('sAMAccountName')}")
        print(f"Dipartimento: {utente.get('department')}")
        print(f"Telefono: {utente.get('telephoneNumber')}")
        print(f"Account attivo: {utente.get('account_active')}")
        print(f"Manager: {utente.get('manager_name')}")
        print(f"Gruppi: {utente.get('memberOf_count', 0)}")
    
    print("\n=== RICERCA SEMPLICE ===")
    risultati_semplici = cerca_ldap_semplice("admin", max_risultati=2)
    
    for utente in risultati_semplici:
        print(f"{utente.get('displayName')} - {utente.get('mail')} - {utente.get('sAMAccountName')}")


@login_required
@gruppo_richiesto("admin")
def info_utenti(request):
    query = request.GET.get('query', '').strip()
    max_risultati = int(request.GET.get('max_risultati', 50))
    solo_attivi = request.GET.get('solo_attivi') == 'on'
    dettagli_completi = request.GET.get('dettagli_completi') == 'on'
    
    risultati = []
    errore = None
    tempo_ricerca = 0
    
    if query:
        try:
            start_time = time.time()
            
            if solo_attivi:
                risultati = cerca_utenti_attivi(query, max_risultati)
            else:
                if dettagli_completi:
                    risultati = cerca_ldap_completo(query, max_risultati=max_risultati)
                else:
                    risultati = cerca_ldap_semplice(query, max_risultati)
            
            tempo_ricerca = time.time() - start_time
            
        except Exception as e:
            errore = str(e)
    
    # Recupera gli utenti dal database per confronto
    utenti_db = {}
    if risultati:
        # Estrai gli username dai risultati LDAP
        usernames = [u.get('sAMAccountName') for u in risultati if u.get('sAMAccountName')]
        # Recupera tutti gli utenti del DB con questi username in una sola query
        utenti_db_query = Utente.objects.filter(username__in=usernames)
        # Crea un dizionario username -> utente per accesso veloce
        utenti_db = {u.username: u for u in utenti_db_query}

# POI MODIFICA IL context AGGIUNGENDO utenti_db:
    context = {
        'query': query,
        'risultati': risultati,
        'max_risultati': str(max_risultati),
        'solo_attivi': solo_attivi,
        'dettagli_completi': dettagli_completi,
        'tempo_ricerca': tempo_ricerca,
        'errore': errore,
        'utenti_db': utenti_db,  # ← AGGIUNGI QUESTA RIGA
    }
    
    return render(request, 'accounts/info_utenti.html', context)

# @login_required
# def gestione_gruppi(request):
#     username = request.GET.get("username")
#     nome = request.GET.get("name", "")
    
#     if not username:
#         messages.error(request, "Username non specificato.")
#         return redirect("info_utenti")

#     # Recupera l'utente se esiste o lo crea (senza gruppo)
#     utente, created = Utente.objects.get_or_create(username=username, defaults={"nome": nome})
    
#     gruppi_disponibili = GruppoAutorizzativo.objects.all()
#     gruppi_associati = set(UtenteGruppo.objects.filter(utente=utente).values_list("gruppo_id", flat=True))

#     if request.method == "POST":
#         gruppi_selezionati = request.POST.getlist("gruppi")
        
#         # Aggiorna associazioni
#         UtenteGruppo.objects.filter(utente=utente).delete()
#         for gid in gruppi_selezionati:
#             gruppo = GruppoAutorizzativo.objects.get(id=gid)
#             UtenteGruppo.objects.create(utente=utente, gruppo=gruppo)
        
#         messages.success(request, "Associazioni aggiornate.")
#         return redirect("gestione_gruppi")  # reload

#     context = {
#         "utente": utente,
#         "gruppi_disponibili": gruppi_disponibili,
#         "gruppi_associati": gruppi_associati,
#     }

#     return render(request, "accounts/gestione_gruppi.html", context)

@login_required
@gruppo_richiesto("admin")
def gestione_gruppi(request):
    username = request.GET.get("username")
    display_name = request.GET.get("name", username)
    #utente = get_object_or_404(Utente, username=username)
        # Cerca utente, oppure crea se non esiste
    try:
        utente = Utente.objects.get(username=username)
    except Utente.DoesNotExist:
        # Prova a prenderlo da LDAP
        dati_ldap = cerca_utente_per_username(username)
        if dati_ldap:
            utente = Utente.objects.create(
                username=username,
                nome=dati_ldap.get("givenName", ""),
                cognome=dati_ldap.get("sn", ""),
                email=dati_ldap.get("mail", ""),
                attivo=True,
            )
        else:
            raise Http404("Utente non trovato in LDAP")

    # Tutti i gruppi
    gruppi = GruppoAutorizzativo.objects.all().order_by("nome")

    # Gruppi selezionati
    gruppi_assoc = UtenteGruppo.objects.filter(utente=utente).values_list("gruppo_id", flat=True)

    if request.method == "POST":
        # Associazione utente-gruppi
        if 'associa' in request.POST:
            gruppi_selezionati = request.POST.getlist("gruppi")
            # Elimina tutte le associazioni precedenti
            UtenteGruppo.objects.filter(utente=utente).delete()

            # Aggiungi quelle selezionate nel form
            for id_gruppo in gruppi_selezionati:
                try:
                    gruppo = GruppoAutorizzativo.objects.get(id=id_gruppo)
                    UtenteGruppo.objects.create(utente=utente, gruppo=gruppo)
                except GruppoAutorizzativo.DoesNotExist:
                    continue
            #return redirect(request.path + f"?username={username}&name={display_name}")
            return redirect(f"{reverse('info_utenti')}?query={username}")

        # Crea nuovo gruppo
        elif 'crea_gruppo' in request.POST:
            nuovo_nome = request.POST.get("nome", "").strip()
            if nuovo_nome:
                GruppoAutorizzativo.objects.get_or_create(nome=nuovo_nome)
            return redirect(request.path + f"?username={username}&name={display_name}")

        # Modifica gruppo
        elif 'modifica_gruppo' in request.POST:
            gruppo_id = request.POST.get("gruppo_id")
            nuovo_nome = request.POST.get("nuovo_nome", "").strip()
            if gruppo_id and nuovo_nome:
                gruppo = get_object_or_404(GruppoAutorizzativo, id=gruppo_id)
                gruppo.nome = nuovo_nome
                gruppo.save()
            return redirect(request.path + f"?username={username}&name={display_name}")

        # Elimina gruppo
        elif 'elimina_gruppo' in request.POST:
            gruppo_id = request.POST.get("gruppo_id")
            if gruppo_id:
                gruppo = get_object_or_404(GruppoAutorizzativo, id=gruppo_id)
                gruppo.delete()
            return redirect(request.path + f"?username={username}&name={display_name}")

    form = AssociaGruppoForm(initial={"gruppi": gruppi_assoc})
    gruppo_form = GruppoAutorizzativoForm()

    context = {
        "gruppi": gruppi,
        "gruppi_assoc": list(gruppi_assoc),  # cast a lista per il template
        "gruppo_form": gruppo_form,
        "display_name": display_name,
    }
    return render(request, "accounts/gestione_gruppi.html", context)


@require_POST
@login_required
def toggle_attivo(request, utente_id):
    utente = get_object_or_404(Utente, id=utente_id)
    utente.attivo = not utente.attivo
    utente.save()

    username = request.POST.get('username', '')
    query = request.POST.get('query', '')
    max_risultati = request.POST.get('max_risultati', '50')
    solo_attivi = request.POST.get('solo_attivi') == 'on'
    dettagli_completi = request.POST.get('dettagli_completi') == 'on'

    redirect_params = {
        'query': query,
        'max_risultati': max_risultati,
        'username_modificato': username,
    }
    if solo_attivi:
        redirect_params['solo_attivi'] = 'on'
    if dettagli_completi:
        redirect_params['dettagli_completi'] = 'on'

    return redirect(f"{reverse('info_utenti')}?{urlencode(redirect_params)}")


@register.filter
def keyvalue(dict_data, key):
    """Permette di accedere alle chiavi del dizionario nel template"""
    if hasattr(dict_data, 'get'):
        return dict_data.get(key)
    return None


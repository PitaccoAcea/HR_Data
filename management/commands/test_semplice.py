print("=== INIZIO TEST ===")

try:
    from ldap3 import Server, Connection, ALL, SUBTREE
    print("✓ Importazione ldap3 riuscita")
except Exception as e:
    print(f"✗ Errore importazione: {e}")
    exit()

try:
    print("Tentativo connessione a aceaspa.it...")
    server = Server('aceaspa.it', get_info=ALL)
    print(f"✓ Server creato: {server}")
except Exception as e:
    print(f"✗ Errore creazione server: {e}")
    exit()

try:
    print("Tentativo auto_bind...")
    conn = Connection(server, auto_bind=True)
    print(f"✓ Connessione riuscita: {conn.bound}")
except Exception as e:
    print(f"✗ Errore connessione: {e}")
    exit()

try:
    print("Tentativo ricerca semplice...")
    conn.search(
        search_base='DC=aceaspa,DC=it',
        search_filter='(objectClass=user)',
        search_scope=SUBTREE,
        size_limit=1  # Solo 1 risultato per test
    )
    print(f"✓ Ricerca completata. Risultati: {len(conn.entries)}")
    
    if conn.entries:
        entry = conn.entries[0]
        print(f"Primo utente trovato: {entry.entry_dn}")
    else:
        print("✗ Nessun utente trovato")
        
except Exception as e:
    print(f"✗ Errore ricerca: {e}")

try:
    conn.unbind()
    print("✓ Connessione chiusa")
except:
    pass

print("=== FINE TEST ===")
def test_filtri_diversi(query="a"):  # Usa "a" come test
    from ldap3 import Server, Connection, ALL, SUBTREE
    
    server = Server('aceaspa.it', get_info=ALL)
    conn = Connection(server, auto_bind=True)
    
    print(f"=== TESTING CON QUERY: '{query}' ===\n")
    
    # Lista di filtri da testare
    filtri_da_testare = [
        f"(displayName={query}*)",
        f"(displayName=*{query}*)",
        f"(name={query}*)",
        f"(cn={query}*)",
        f"(sAMAccountName={query}*)",
        f"(&(objectClass=user)(displayName={query}*))",
        f"(&(objectClass=person)(displayName={query}*))",
        f"(&(objectCategory=person)(objectClass=user)(displayName={query}*))",
    ]
    
    for i, filtro in enumerate(filtri_da_testare, 1):
        print(f"--- FILTRO {i}: {filtro} ---")
        
        try:
            conn.search(
                search_base='DC=aceaspa,DC=it',
                search_filter=filtro,
                search_scope=SUBTREE,
                attributes=["displayName", "mail", "sAMAccountName", "cn", "name"],
                size_limit=10
            )
            
            print(f"Risultati trovati: {len(conn.entries)}")
            
            for entry in conn.entries[:3]:  # Primi 3 risultati
                display = entry.displayName if entry.displayName else "N/A"
                sam = entry.sAMAccountName if entry.sAMAccountName else "N/A"
                print(f"  - DisplayName: {display} | SAM: {sam}")
                
        except Exception as e:
            print(f"ERRORE: {e}")
        
        print()  # Riga vuota
    
    conn.unbind()

if __name__ == "__main__":
    # Testa con diverse lettere
    test_filtri_diversi("a")
    print("\n" + "="*50 + "\n")
    test_filtri_diversi("m")
    print("\n" + "="*50 + "\n")
    test_filtri_diversi("mario")  # Sostituisci con un nome che sai esistere
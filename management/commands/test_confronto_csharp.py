def test_esatto_come_csharp(query):
    from ldap3 import Server, Connection, ALL, SUBTREE
    
    server = Server('aceaspa.it', get_info=ALL)
    conn = Connection(server, auto_bind=True)
    
    print(f"=== TEST IDENTICO AL C# ===")
    print(f"Query ricercata: '{query}'")
    print(f"Server: aceaspa.it")
    print(f"Connection status: {conn.bound}")
    print(f"User: {conn.user}")
    
    # Filtro IDENTICO al C#: (displayName=query*)
    filtro = f"(displayName={query.strip()}*)"
    print(f"Filtro applicato: {filtro}")
    print(f"Search base: DC=aceaspa,DC=it")
    print(f"Search scope: SUBTREE")
    print()
    
    try:
        result = conn.search(
            search_base='DC=aceaspa,DC=it',
            search_filter=filtro,
            search_scope=SUBTREE,
            attributes=["displayName", "mail"],
            size_limit=100,
            time_limit=30
        )
        
        print(f"Search executed: {result}")
        print(f"Entries found: {len(conn.entries)}")
        print(f"Connection result: {conn.result}")
        
        if conn.result['result'] != 0:
            print(f"LDAP Error Code: {conn.result['result']}")
            print(f"LDAP Error Message: {conn.result['message']}")
            print(f"LDAP Error Description: {conn.result['description']}")
        
        print("\n--- RISULTATI TROVATI ---")
        for i, entry in enumerate(conn.entries, 1):
            print(f"{i}. DN: {entry.entry_dn}")
            print(f"   displayName: {entry.displayName}")
            print(f"   mail: {entry.mail}")
            print()
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    conn.unbind()

def test_multiple_queries():
    # Lista di query da testare
    test_queries = ["a", "mario", "admin", "test"]  # Aggiungi nomi che sai esistere
    
    for query in test_queries:
        print(f"{'='*60}")
        test_esatto_come_csharp(query)
        print()

if __name__ == "__main__":
    test_multiple_queries()
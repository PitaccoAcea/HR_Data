def test_domain_controller():
    from ldap3 import Server, Connection, ALL
    
    server = Server('aceaspa.it', get_info=ALL)
    
    print("=== INFORMAZIONI SERVER ===")
    print(f"Server: {server}")
    print(f"Host: {server.host}")
    print(f"Port: {server.port}")
    print()
    
    try:
        conn = Connection(server, auto_bind=True)
        
        print("=== CONNECTION INFO ===")
        print(f"Bound: {conn.bound}")
        print(f"User: {conn.user}")
        print(f"Server: {conn.server}")
        print(f"Strategy: {conn.strategy}")
        print(f"Authentication: {conn.authentication}")
        print()
        
        if server.info:
            print("=== SERVER INFO ===")
            print(f"DSA info: {server.info}")
            if hasattr(server.info, 'naming_contexts'):
                print(f"Naming contexts: {server.info.naming_contexts}")
            if hasattr(server.info, 'supported_controls'):
                print(f"Supported controls: {len(server.info.supported_controls)} controls")
            if hasattr(server.info, 'supported_extensions'):
                print(f"Supported extensions: {len(server.info.supported_extensions)} extensions")
        
        print("\n=== TEST CONNESSIONE BASE ===")
        # Test semplice per vedere se la connessione funziona
        result = conn.search(
            search_base='',
            search_filter='(objectClass=*)',
            search_scope='BASE',
            attributes=['*']
        )
        
        print(f"Root DSE search result: {result}")
        print(f"Entries found: {len(conn.entries)}")
        
        if conn.entries:
            print("\n--- ROOT DSE ATTRIBUTES ---")
            root_dse = conn.entries[0]
            for attr in root_dse.entry_attributes:
                value = getattr(root_dse, attr, None)
                print(f"{attr}: {value}")
        
        conn.unbind()
        
    except Exception as e:
        print(f"ERRORE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_domain_controller()
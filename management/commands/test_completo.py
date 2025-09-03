import sys
import traceback

def run_all_tests():
    print("INIZIO TEST DIAGNOSTICI LDAP")
    print("=" * 60)
    
    # Test 1: Info server
    print("\n1. TEST INFORMAZIONI SERVER")
    print("-" * 30)
    try:
        from test_server_info import test_domain_controller
        test_domain_controller()
    except Exception as e:
        print(f"ERRORE nel test server: {e}")
        traceback.print_exc()
    
    # Test 2: Utenti generici
    print("\n\n2. TEST RICERCA UTENTI GENERICI")
    print("-" * 30)
    try:
        from test_ldap import debug_ad_completo
        debug_ad_completo()
    except Exception as e:
        print(f"ERRORE nel test utenti: {e}")
        traceback.print_exc()
    
    # Test 3: Filtri diversi
    print("\n\n3. TEST FILTRI DIVERSI")
    print("-" * 30)
    try:
        from test_filtri import test_filtri_diversi
        test_filtri_diversi("a")
    except Exception as e:
        print(f"ERRORE nel test filtri: {e}")
        traceback.print_exc()
    
    # Test 4: Confronto C#
    print("\n\n4. TEST CONFRONTO CON C#")
    print("-" * 30)
    try:
        from test_confronto_csharp import test_esatto_come_csharp
        test_esatto_come_csharp("a")
    except Exception as e:
        print(f"ERRORE nel test C#: {e}")
        traceback.print_exc()
    
    print("\n\nFINE TEST DIAGNOSTICI")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
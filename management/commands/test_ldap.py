from django.core.management.base import BaseCommand
from ldap3 import Server, Connection, ALL, SUBTREE

class Command(BaseCommand):
    help = 'Test LDAP connection'

    def handle(self, *args, **options):
        server = Server('aceaspa.it', get_info=ALL)
        conn = Connection(server, auto_bind=True)
        
        self.stdout.write("=== TEST: Cerca TUTTI gli utenti (primi 5) ===")
        conn.search(
            search_base='DC=aceaspa,DC=it',
            search_filter='(objectClass=user)',
            search_scope=SUBTREE,
            attributes=['*'],
            size_limit=5
        )
        
        self.stdout.write(f"Trovati {len(conn.entries)} utenti")
        
        for i, entry in enumerate(conn.entries):
            self.stdout.write(f"\n--- UTENTE {i+1} ---")
            self.stdout.write(f"DN: {entry.entry_dn}")
            
            for attr_name in entry.entry_attributes:
                attr_value = getattr(entry, attr_name, None)
                if attr_value:
                    self.stdout.write(f"{attr_name}: {attr_value}")
        
        conn.unbind()
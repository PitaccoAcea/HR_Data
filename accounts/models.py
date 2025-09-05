from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
import re

class Utente(models.Model):
    username = models.CharField(max_length=100, unique=True) # es: TI\\a37400c
    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    attivo = models.BooleanField(default=True)


def __str__(self):
    return f"{self.cognome} {self.nome} ({self.username})"


class GruppoAutorizzativo(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Gruppo Autorizzativo"
        verbose_name_plural = "Gruppi Autorizzativi"


def __str__(self):
    return self.nome



class UtenteGruppo(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    gruppo = models.ForeignKey(GruppoAutorizzativo, on_delete=models.CASCADE)


class Meta:
    unique_together = ('utente', 'gruppo')


def __str__(self):
    return f"{self.utente.username} → {self.gruppo.nome}"

class MenuVoce(models.Model):
    titolo = models.CharField(max_length=100, verbose_name="Titolo")
    url = models.CharField(
        max_length=255, 
        verbose_name="URL",
        help_text="Inserisci un URL relativo (/path/), assoluto (https://...) o nome view Django (app:view)"
    )
    id_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Voce Padre",
        related_name='figli'
    )
    ordine = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Ordine",
        help_text="Ordine di visualizzazione (0 = primo)"
    )
    icona = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Icona",
        help_text="Classe CSS per l'icona (es: 'fas fa-home' per Font Awesome, 'bi-house' per Bootstrap Icons)"
    )
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Note",
        help_text="Note interne per la gestione"
    )
    attivo = models.BooleanField(
        default=True,
        verbose_name="Attivo",
        help_text="Deseleziona per nascondere la voce dal menù"
    )
    
    # Relazione many-to-many con i gruppi
    gruppi_autorizzati = models.ManyToManyField(
        GruppoAutorizzativo,
        blank=True,
        verbose_name="Gruppi Autorizzati",
        help_text="Gruppi che possono vedere questa voce di menù. Lascia vuoto per tutti.",
        related_name='menu_voci'
    )

    class Meta:
        verbose_name = "Voce di Menù"
        verbose_name_plural = "Voci di Menù"
        ordering = ['ordine', 'titolo']
        indexes = [
            models.Index(fields=['attivo', 'ordine']),
            models.Index(fields=['id_padre', 'ordine']),
        ]

    def __str__(self):
        if self.id_padre:
            return f"{self.id_padre.titolo} → {self.titolo}"
        return self.titolo

    def get_url(self):
        """
        Risolve l'URL in base al tipo:
        - Se inizia con http:// o https:// → URL assoluto
        - Se inizia con / → URL relativo
        - Altrimenti → Nome view Django
        """
        if not self.url:
            return "#"
        
        # URL assoluto
        if self.url.startswith(('http://', 'https://')):
            return self.url
        
        # URL relativo
        if self.url.startswith('/'):
            return self.url
        
        # Nome view Django
        try:
            return reverse(self.url)
        except:
            # Se la view non esiste, ritorna l'URL originale
            return self.url

    def get_livello(self):
        """Calcola il livello di profondità della voce"""
        livello = 0
        padre = self.id_padre
        while padre:
            livello += 1
            padre = padre.id_padre
        return livello

    def get_figli_attivi(self):
        """Ritorna i figli attivi ordinati"""
        return self.figli.filter(attivo=True).order_by('ordine', 'titolo')

    def ha_figli(self):
        """Controlla se ha figli attivi"""
        return self.figli.filter(attivo=True).exists()

    def is_dropdown(self):
        """Alias per ha_figli() per template"""
        return self.ha_figli()

    def get_icona_html(self):
        """Genera HTML per l'icona"""
        if not self.icona:
            return ""
        
        # Font Awesome
        if self.icona.startswith(('fa-', 'fas ', 'far ', 'fab ', 'fal ', 'fat ')):
            if not self.icona.startswith(('fas ', 'far ', 'fab ', 'fal ', 'fat ')):
                return f'<i class="fas {self.icona}"></i>'
            return f'<i class="{self.icona}"></i>'
        
        # Bootstrap Icons
        if self.icona.startswith('bi-'):
            return f'<i class="bi {self.icona}"></i>'
        
        # Classe personalizzata
        return f'<i class="{self.icona}"></i>'

    @classmethod
    def get_menu_tree(cls, user=None):
        """
        Ritorna l'albero del menù per l'utente specificato
        """
        # Ottieni tutti i menù di primo livello (senza padre)
        menu_items = cls.objects.filter(
            attivo=True,
            id_padre__isnull=True
        ).order_by('ordine', 'titolo')
        
        if user and user.is_authenticated:
            # Filtra in base ai gruppi dell'utente
            user_groups = user.gruppi.all() if hasattr(user, 'gruppi') else []
            
            def filter_by_permissions(items):
                filtered_items = []
                for item in items:
                    # Se non ha gruppi specificati, è visibile a tutti
                    if not item.gruppi_autorizzati.exists():
                        # Filtra ricorsivamente i figli
                        item._figli_filtered = filter_by_permissions(item.get_figli_attivi())
                        filtered_items.append(item)
                    else:
                        # Controlla se l'utente ha almeno uno dei gruppi autorizzati
                        if any(group in user_groups for group in item.gruppi_autorizzati.all()):
                            item._figli_filtered = filter_by_permissions(item.get_figli_attivi())
                            filtered_items.append(item)
                
                return filtered_items
            
            return filter_by_permissions(menu_items)
        
        # Se non c'è utente, ritorna solo gli elementi senza gruppi specificati
        def get_public_items(items):
            public_items = []
            for item in items:
                if not item.gruppi_autorizzati.exists():
                    item._figli_filtered = get_public_items(item.get_figli_attivi())
                    public_items.append(item)
            return public_items
        
        return get_public_items(menu_items)

    def clean(self):
        """Validazione personalizzata"""
        from django.core.exceptions import ValidationError
        
        # Evita cicli infiniti nel menù
        if self.id_padre:
            padre = self.id_padre
            while padre:
                if padre.pk == self.pk:
                    raise ValidationError("Non puoi creare un ciclo nel menù!")
                padre = padre.id_padre

    @property
    def figli_filtered(self):
        return self._figli_filtered
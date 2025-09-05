from django.db import migrations, models
import django.db.models.deletion
import django.core.validators

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Modifica con il nome della tua ultima migrazione
    ]

    operations = [
        migrations.CreateModel(
            name='MenuVoce',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titolo', models.CharField(max_length=100, verbose_name='Titolo')),
                ('url', models.CharField(help_text='Inserisci un URL relativo (/path/), assoluto (https://...) o nome view Django (app:view)', max_length=255, verbose_name='URL')),
                ('ordine', models.PositiveIntegerField(default=0, help_text='Ordine di visualizzazione (0 = primo)', validators=[django.core.validators.MinValueValidator(0)], verbose_name='Ordine')),
                ('icona', models.CharField(blank=True, help_text="Classe CSS per l'icona (es: 'fas fa-home' per Font Awesome, 'bi-house' per Bootstrap Icons)", max_length=50, null=True, verbose_name='Icona')),
                ('note', models.TextField(blank=True, help_text='Note interne per la gestione', null=True, verbose_name='Note')),
                ('attivo', models.BooleanField(default=True, help_text='Deseleziona per nascondere la voce dal menù', verbose_name='Attivo')),
                ('id_padre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='figli', to='accounts.menuvoce', verbose_name='Voce Padre')),
                ('gruppi_autorizzati', models.ManyToManyField(blank=True, help_text='Gruppi che possono vedere questa voce di menù. Lascia vuoto per tutti.', related_name='menu_voci', to='accounts.gruppoautorizzativo', verbose_name='Gruppi Autorizzati')),
            ],
            options={
                'verbose_name': 'Voce di Menù',
                'verbose_name_plural': 'Voci di Menù',
                'ordering': ['ordine', 'titolo'],
            },
        ),
        migrations.AddIndex(
            model_name='menuvoce',
            index=models.Index(fields=['attivo', 'ordine'], name='accounts_men_attivo_b8b9c4_idx'),
        ),
        migrations.AddIndex(
            model_name='menuvoce',
            index=models.Index(fields=['id_padre', 'ordine'], name='accounts_men_id_padr_f9d2a1_idx'),
        ),
        # Inserimento dati di esempio
        migrations.RunSQL(
            """
            INSERT INTO accounts_menuvoce (titolo, url, ordine, icona, attivo, id_padre_id) VALUES
            ('Home', '/', 0, 'fas fa-home', 1, NULL),
            ('Utenti', '/accounts/info-utenti/', 1, 'fas fa-users', 1, NULL),
            ('Amministrazione', '#', 2, 'fas fa-cogs', 1, NULL);
            """,
            reverse_sql="DELETE FROM accounts_menuvoce WHERE url IN ('/', '/accounts/info-utenti/', '#');"
        ),
    ]
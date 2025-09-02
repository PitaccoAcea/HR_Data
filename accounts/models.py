from django.db import models

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
    descrizione = models.TextField(blank=True)


def __str__(self):
    return self.nome


class UtenteGruppo(models.Model):
    utente = models.ForeignKey(Utente, on_delete=models.CASCADE)
    gruppo = models.ForeignKey(GruppoAutorizzativo, on_delete=models.CASCADE)


class Meta:
    unique_together = ('utente', 'gruppo')


def __str__(self):
    return f"{self.utente.username} → {self.gruppo.nome}"

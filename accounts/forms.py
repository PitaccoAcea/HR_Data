from django import forms
from .models import Utente, GruppoAutorizzativo


class CercaUtenteLDAPForm(forms.Form):
    query = forms.CharField(label="Cerca utente LDAP", max_length=100)


class AssociaGruppoForm(forms.Form):
    utente_id = forms.IntegerField(widget=forms.HiddenInput())
    gruppo = forms.ModelChoiceField(queryset=GruppoAutorizzativo.objects.all())
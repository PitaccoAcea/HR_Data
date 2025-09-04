from django import template

register = template.Library()

@register.filter
def keyvalue(dict_data, key):
    """Permette di accedere alle chiavi del dizionario nel template"""
    if hasattr(dict_data, 'get'):
        return dict_data.get(key)
    return None
from django import template
from ..models import MenuVoce

register = template.Library()

@register.inclusion_tag('accounts/menu_dynamic.html', takes_context=True)
def render_menu(context):
    """
    Template tag per renderizzare il menù dinamico
    Usage: {% load menu_tags %} {% render_menu %}
    """
    request = context.get('request')
    user = request.user if request else None
    
    menu_items = MenuVoce.get_menu_tree(user)
    
    return {
        'menu_items': menu_items,
        'request': request,
        'user': user
    }

@register.inclusion_tag('accounts/menu_breadcrumb.html', takes_context=True)
def render_breadcrumb(context):
    """
    Template tag per renderizzare il breadcrumb basato sul menù
    Usage: {% load menu_tags %} {% render_breadcrumb %}
    """
    request = context.get('request')
    user = request.user if request else None
    current_path = request.path if request else '/'
    
    # Trova la voce di menù corrispondente al path corrente
    menu_items = MenuVoce.get_menu_tree(user)
    breadcrumb = []
    
    def find_in_menu(items, path, parents=[]):
        for item in items:
            current_parents = parents + [item]
            if item.get_url() == path:
                return current_parents
            
            # Cerca nei figli se esistono
            if hasattr(item, '_figli_filtered'):
                result = find_in_menu(item._figli_filtered, path, current_parents)
                if result:
                    return result
            elif item.ha_figli():
                result = find_in_menu(item.get_figli_attivi(), path, current_parents)
                if result:
                    return result
        return None
    
    breadcrumb = find_in_menu(menu_items, current_path)
    
    return {
        'breadcrumb': breadcrumb or [],
        'request': request
    }

@register.filter
def get_menu_level_class(level):
    """
    Ritorna la classe CSS per il livello del menù
    """
    level_classes = {
        0: 'menu-level-0',
        1: 'menu-level-1', 
        2: 'menu-level-2',
        3: 'menu-level-3'
    }
    return level_classes.get(level, f'menu-level-{level}')

@register.filter
def menu_icon_html(icona):
    """
    Genera HTML per l'icona del menù
    """
    if not icona:
        return ""
    
    # Font Awesome
    if icona.startswith(('fa-', 'fas ', 'far ', 'fab ', 'fal ', 'fat ')):
        if not icona.startswith(('fas ', 'far ', 'fab ', 'fal ', 'fat ')):
            return f'<i class="fas {icona}"></i>'
        return f'<i class="{icona}"></i>'
    
    # Bootstrap Icons
    if icona.startswith('bi-'):
        return f'<i class="bi {icona}"></i>'
    
    # Classe personalizzata
    return f'<i class="{icona}"></i>'
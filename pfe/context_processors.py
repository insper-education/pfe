#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Setembro de 2025
"""

from .support import get_navigation_items

def navigation_menu(request):
    if not request.user.is_authenticated:
        return {"nav_menu_items": []}
    
    menu_items = get_navigation_items()

    # Filtrando itens visíveis para o usuário atual (mesmo código da view do index)
    visible_items = []
    for item in menu_items:
        visible = False
        
        # Itens visíveis para todos
        if item.get("visible_to_all"):
            visible = True
        
        # Itens baseados em atributos do usuário
        if "visible_for_type" in item:
            for attr in item["visible_for_type"]:
                if hasattr(request.user, attr) and getattr(request.user, attr):
                    visible = True
                    break
        
        # Itens baseados em permissões
        if "visible_for_permission" in item:
            for perm in item["visible_for_permission"]:
                if request.user.has_perm(f"{item.get('app', 'projetos')}.{perm}"):
                    visible = True
                    break

        if visible:
            visible_items.append(item)
    
    return {"nav_menu_items": visible_items}

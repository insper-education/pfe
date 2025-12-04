#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Setembro de 2025
"""

import logging

# Get an instance of a logger
logger = logging.getLogger("django")

def get_navigation_items():
    """
    Retorna a definição única de itens de navegação
    usados tanto para cards quanto para menu hambúrguer
    """
     # Definição dos cards organizados por grupos
    cards = [
        # Calendário (sempre visível)
        {
            "title": {"pt": "Calendário Geral", "en": "General Calendar"},
            "icon": "fas fa-calendar-alt",
            "url": "calendario",
            "direct_link": True,
            "visible_to_all": True,
            "group": "calendario"
        },
        
        # Áreas principais
        {
            "title": {"pt": "Área dos Estudantes", "en": "Students Area"},
            "icon": "fas fa-user-graduate",
            "url": "estudantes",
            "highlight_for": "eh_estud",
            "visible_for_type": ["eh_admin", "eh_estud"],
            "group": "usuarios"
        },
        {
            "title": {"pt": "Área dos Parceiros", "en": "Partners Area"},
            "icon": "fas fa-handshake",
            "url": "organizacoes",
            "highlight_for": "eh_parc",
            "visible_for_type": ["eh_admin", "eh_parc", "membro_comite"],
            "group": "usuarios"
        },
        {
            "title": {"pt": "Área dos Professores", "en": "Professors Area"},
            "icon": "fas fa-chalkboard-teacher",
            "url": "professores",
            "highlight_for": "eh_prof",
            "visible_for_permission": ["change_professor"],
            "app": "users",
            "group": "usuarios"
        },
        {
            "title": {"pt": "Área da Coordenação", "en": "Coordination Area"},
            "icon": "fas fa-user-tie",
            "url": "coordenacao",
            "visible_for_type": ["eh_admin"],
            "app": "users",
            "group": "usuarios"
        },
        
        # Áreas administrativas
        {
            "title": {"pt": "Área Acadêmica", "en": "Academic Area"},
            "icon": "fas fa-book",
            "url": "academica",
            "visible_for_permission": ["change_exame"],
            "visible_for_type": ["membro_comite"],
            "app": "academica",
            "group": "admin"
        },
        {
            "title": {"pt": "Área Operacional", "en": "Operational Area"},
            "icon": "fas fa-clipboard-list",
            "url": "operacional",
            "visible_for_type": ["eh_admin", "membro_operacional", "membro_tecnico"],
            "group": "admin"
        },
        {
            "title": {"pt": "Área Administrativa", "en": "Administrative Area"},
            "icon": "fas fa-user-cog",
            "url": "administracao",
            "visible_for_type": ["eh_admin"],
            "app": "users",
            "group": "admin"
        },
        
        # Áreas de gestão de projetos
        {
            "title": {"pt": "Propostas", "en": "Proposals"},
            "icon": "fas fa-file-contract",
            "url": "propostas",
            "visible_for_type": ["membro_comite", "membro_operacional", "eh_admin"],
            "group": "projects"
        },
        {
            "title": {"pt": "Projetos", "en": "Projects"},
            "icon": "fas fa-sitemap",
            "url": "projetos",
            "visible_for_permission": ["view_projeto"],
            "app": "projetos",
            "group": "projects"
        },
        
        # Documentação (sempre visível)
        {
            "title": {"pt": "Documentações", "en": "Documentation"},
            "icon": "fas fa-folder-open",
            "url": "documentos",
            "visible_to_all": True,
            "group": "docs"
        }
    ]
    return cards

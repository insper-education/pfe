#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 30 de Agosto de 2022
"""

from projetos.models import Projeto, Proposta, AreaDeInteresse

from django import template
register = template.Library()

@register.filter
def numero_areas(area, projetos):
    """Filtra e conta os projetos por área."""
    
    propostas = [p.proposta.id for p in projetos]
    propostas_projetos = Proposta.objects.filter(id__in=propostas)
    areas = AreaDeInteresse.objects.filter(proposta__in=propostas_projetos, area=area)
    return areas.count()

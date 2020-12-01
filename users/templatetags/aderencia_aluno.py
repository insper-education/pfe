#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Novembro de 2019
"""

from django import template
register = template.Library()

from projetos.models import Area, AreaDeInteresse

@register.simple_tag
def mede_aderencia(estudante, proposta):
    """ Mede a aderência das áreas de interesse de um estudante em relação a uma proposta de projeto. """
    areas_proposta = AreaDeInteresse.objects.filter(proposta=proposta).values_list('area', flat=True)
    area_comuns = AreaDeInteresse.objects.filter(usuario=estudante.user, area__in=areas_proposta).count()
    if areas_proposta:
        return int( (100 * area_comuns) / len(areas_proposta) )
    else:
        return 0

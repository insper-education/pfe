#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 18 de Outubro de 2019
Baseado em:
 https://stackoverflow.com/questions/19598213/generating-a-date-relative-to-another-date-in-django-template
"""

import datetime

from django import template
register = template.Library()

@register.filter
def dias(value, days):
    """Permite adicionar uma quantidade de dias em uma data nos arquivos de template."""
    if value:
        return value + datetime.timedelta(days=days)
    return 0  # Se a data for nula, retorna 0


@register.filter
def dif_dias_hoje(value):
    """Calcula a diferença de uma data para hoje."""
    if value:
        diferenca = (value - datetime.date.today()).days
        return int(diferenca)
    return 0  # Se a data for nula, retorna 0
    

@register.filter
def dif_diashoras_hoje(value):
    """Calcula a diferença de uma data com hora para hoje."""
    if value:
        diferenca = (value - datetime.datetime.now()).days
        return int(diferenca)
    return 0  # Se a data for nula, retorna 0


@register.filter
def diff_days(value, data):
    """Calcula a diferença entre duas datas em dias."""
    if value:
        diferenca = (value.date() - data).days
        return int(diferenca)
    return 0  # Se a data for nula, retorna 0

@register.filter
def dif_agora(value):
    """Calcula a diferença de um momento com agora em segundos."""
    if value:
        return (value - datetime.datetime.now()).total_seconds()
        
    return 0  # Se a data for nula, retorna 0

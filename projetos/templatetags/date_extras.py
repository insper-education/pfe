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
def plus_days(value, days):
    """Permite adicionar uma quantidade de dias em uma data nos arquivos de template."""
    return value + datetime.timedelta(days=days)

@register.filter
def dif_dias_hoje(value):
    """Calcula a diferença de uma data para hoje."""
    diferenca = (value - datetime.date.today()).days
    return int(diferenca)

@register.filter
def dif_diashoras_hoje(value):
    """Calcula a diferença de uma data com hora para hoje."""
    diferenca = (value - datetime.datetime.now()).days
    return int(diferenca)

@register.filter
def diff_days(value, data):
    """Calcula a diferença entre duas datas em dias."""
    diferenca = (value.date() - data).days
    return int(diferenca)

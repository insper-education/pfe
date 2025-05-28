#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Maio de 2025
"""

from django import template
register = template.Library()

@register.filter
def range_d(number, change=0):
    """
    Retorna uma lista de números de 0 até o número especificado, com um incremento opcional.
    Se o número for negativo, retorna uma lista vazia.
    """
    if number < 0:
        return []
    return list(range(0, number + change))

#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 13 de Junho de 2021
"""

from django import template
register = template.Library()

@register.filter
def index(sequence, position):
    """Retorna o uma posição de uma lista."""
    if position < len(sequence):
        return sequence[position]
    else:
        return None

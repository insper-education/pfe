#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 20 de Novembro de 2023
"""

from django import template
register = template.Library()

@register.filter
def empty_zip(value):
    if len(list(value)) > 0:
        return False
    return True

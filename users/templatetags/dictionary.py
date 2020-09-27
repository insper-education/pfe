#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Setembro de 2020
"""

from django import template
register = template.Library()

@register.filter
def dict_key(d, k):
    '''Returns the given key from a dictionary.'''
    return d[k]

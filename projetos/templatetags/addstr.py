#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 24 de Fevereiro de 2022
"""

from urllib import parse

from django import template

register = template.Library()

@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

@register.filter
def int_range(value):
    return range(value, 0, -1)

@register.filter
def to_int(value):
    return int(value)
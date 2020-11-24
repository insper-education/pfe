#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Novembro de 2020
"""

from django import template
register = template.Library()

@register.simple_tag
def define(val=None):
  return val

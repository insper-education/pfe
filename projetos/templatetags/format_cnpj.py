#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2020
"""

from django import template
register = template.Library()

@register.filter
def cnpj(value):
    """Formata o texto do CNPJ."""
    return "%s.%s.%s/%s-%s" % (value[0:2], value[2:5], value[5:8], value[8:12], value[12:14])

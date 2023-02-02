#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 28 de Novembro de 2019
"""

from urllib import parse

from django import template
register = template.Library()

@register.filter
def parse_quote(value):
    """Remove e-comercial e outros simbolos que podem comprometer a montagem da URL."""
    return parse.quote(str(value))

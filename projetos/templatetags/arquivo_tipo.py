#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Abril de 2021
"""

from django import template
register = template.Library()

@register.filter
def get_tipo(value):
    """Retorna a string do tipo de arquivo."""
    return str(value).split(".")[-1]
    
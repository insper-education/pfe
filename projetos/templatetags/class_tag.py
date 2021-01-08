#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 24 de Abril de 2020
"""

from django import template
register = template.Library()

@register.filter
def get_class(value):
    """Retorna o nome da classe do objeto."""
    return value.__class__.__name__
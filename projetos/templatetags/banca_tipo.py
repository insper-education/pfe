#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Dezembro de 2020
"""

from projetos.models import Banca

from django import template
register = template.Library()

@register.filter
def get_banca(value):
    """Retorna a string do tipo de banca."""
    TIPOS = dict(Banca.TIPO_DE_BANCA)
    if value in TIPOS:
        return TIPOS[value]
    else:
        return "Tipo de banca não definido"
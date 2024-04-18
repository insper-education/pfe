#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Abril de 2024
"""

from django import template
register = template.Library()

@register.filter
def get_exame(colunas, exame):
    coluna = colunas.filter(exame=exame).last()
    if coluna:
        return coluna.coluna
    return None
    

#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 6 de Abril de 2023
"""

from estudantes.models import Pares

from django import template
register = template.Library()

@register.filter
def aval_pares(alocacao, momento):
    """Retorna se a alocação tem alguma avaliação de pares do tipo."""

    if momento=="intermediaria":
        tipo=0
    else:
        tipo=1

    par = Pares.objects.filter(alocacao_de=alocacao, tipo=tipo).first()
    if par:
        return True
    else:
        return False

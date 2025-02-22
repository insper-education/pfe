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

@register.filter
def puxa_pares(alocacao, momento=None):
    """Retorna avaliações de pares de uma alocação."""
    pares = Pares.objects.filter(alocacao_para=alocacao)
    resultado = {
        "entrega": {"f": 0, "d": 0},
        "iniciativa": {"f": 0, "d": 0},
        "comunicacao": {"f": 0, "d": 0},
    }
    for par in pares:
        entrega = par.entrega + 1
        
        iniciativa = par.iniciativa + 1
        if iniciativa==5:
            iniciativa=3
        elif iniciativa==3:
            iniciativa=4
        elif iniciativa==4:
            iniciativa=5

        comunicacao = par.comunicacao + 1

        if entrega > 3:
            resultado["entrega"]["f"] += entrega
        elif entrega < 3:
            resultado["entrega"]["d"] += entrega
        if iniciativa > 3:
            resultado["iniciativa"]["f"] += iniciativa
        elif iniciativa < 3:
            resultado["iniciativa"]["d"] += iniciativa
        if comunicacao > 3:
            resultado["comunicacao"]["f"] += comunicacao
        elif comunicacao < 3:
            resultado["comunicacao"]["d"] += comunicacao
    return resultado

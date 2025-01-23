#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from projetos.models import Avaliacao2
from academica.support_notas import converte_letra

from django import template
register = template.Library()


def get_oas(avaliacoes):
    """Retorna Objetivos de Aprendizagem da alocação no semestre."""
    oas = {}
    for avaliacao in avaliacoes:
        if avaliacao.objetivo not in oas:
            oas[avaliacao.objetivo] = {"conceito": []}
        exame = avaliacao.exame
        nota = avaliacao.nota
        peso = avaliacao.peso
        if nota is not None and peso is not None:
            oas[avaliacao.objetivo]["conceito"].append( (exame, converte_letra(nota), float(nota), float(peso)) )
    for oa in oas:
        notas = oas[oa]["conceito"]
        val = 0
        pes = 0
        cor = "black"
        for exame, _, nota, peso in notas:
            if exame.periodo_para_rubricas == 2:  # (2, "Final"),
                if nota < 5:
                    cor = "darkorange"
            val += nota * peso
            pes += peso
        if pes:
            val = val/pes
        if val < 5:
            cor = "red"
        oas[oa]["media"] = (converte_letra(val), val, cor)
        oas[oa]["peso"] = pes

    return oas

@register.filter
def get_oas_i(alocacao):
    avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame__grupo=False)
    return get_oas(avaliacoes)

# ESSE CODIGO ESTA ERRADO, POIS NAO TRATA BANCAS, E OUTRAS REPETICOES DE AVALIACOES
@register.filter
def get_oas_g(alocacao):
    avaliacoes = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame__grupo=True)
    return get_oas(avaliacoes)

# ESSE CODIGO ESTA ERRADO, POIS NAO TRATA BANCAS, E OUTRAS REPETICOES DE AVALIACOES
@register.filter
def get_oas_t(alocacao):
    avaliacoes = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame__grupo=False) | Avaliacao2.objects.filter(projeto=alocacao.projeto, exame__grupo=True)
    return get_oas(avaliacoes)
#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from django import template

from academica.support_notas import converte_letra
from academica.support2 import get_objetivos

from projetos.models import Avaliacao2

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
    """Retorna Objetivos de Aprendizagem da alocação (individual) no semestre."""
    avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame__grupo=False)
    return get_oas(avaliacoes)


@register.filter
def get_oas_g(projeto):
    """Retorna Objetivos de Aprendizagem do projeto (grupo) no semestre."""
    avaliacoes = Avaliacao2.objects.filter(projeto=projeto, exame__grupo=True)
    resultados = get_objetivos(projeto, avaliacoes)[0]
    objetivos = {}
    for obj, val_pes in resultados.items():
        cor = "black"
        if val_pes[0] < 5:
            cor = "red"
        objetivos[obj] = {"media": [converte_letra(val_pes[0]), val_pes[0], cor], "peso": val_pes[1]}
    return objetivos


@register.filter
def get_oas_t(alocacao):
    """Retorna Objetivos de Aprendizagem da alocação (grupo e individual) no semestre."""
    avaliacoes_i = Avaliacao2.objects.filter(alocacao=alocacao, exame__grupo=False)
    avaliacoes_g = Avaliacao2.objects.filter(projeto=alocacao.projeto, exame__grupo=True)
    return get_oas(avaliacoes_i|avaliacoes_g)

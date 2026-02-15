#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 31 de Janeiro de 2026
"""

import logging

# Get an instance of a logger
logger = logging.getLogger("django")

def filtra_composicoes(composicoes, ano, semestre):
    """Filtra composições."""

    composicoes = composicoes.order_by("exame__ordem")

    composicoes = composicoes.exclude(data_final__year__lt=ano)
    composicoes = composicoes.exclude(data_inicial__year__gt=ano)
    
    if semestre == 1:
        composicoes = composicoes.exclude(data_inicial__year=ano, data_inicial__month__gt=6)
    else:
        composicoes = composicoes.exclude(data_final__year=ano, data_final__month__lt=8)

    return composicoes

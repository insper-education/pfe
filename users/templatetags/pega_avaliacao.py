#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 11 de Novembro de 2023
"""

from django import template
register = template.Library()

@register.filter
def pega_tipo(objeto, tipo):
    """Filtra para um tipo específico de avaliação."""
    return objeto.filter(exame=tipo)

@register.filter
def pega_objetivo(avaliacoes, objetivo):
    """Filtra para um tipo específico de Objetivo de Aprendizagem."""
    avaliacao = avaliacoes.filter(objetivo=objetivo).last()
    return avaliacao

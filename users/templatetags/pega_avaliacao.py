#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 11 de Novembro de 2023
"""

from django import template
register = template.Library()

from projetos.models import Avaliacao2
from users.models import PFEUser

@register.filter
def pega_tipo(objeto, tipo):
    """Filtra para um tipo específico de avaliação."""
    return objeto.filter(exame=tipo)

@register.filter
def pega_objetivo(avaliacoes, objetivo):
    """Filtra para um tipo específico de Objetivo de Aprendizagem."""
    # avaliacoes = avaliacoes.filter(objetivo=objetivo)
    try:
        avaliacao = avaliacoes.get(objetivo=objetivo)
    except Avaliacao2.DoesNotExist:
        avaliacao = None
    return avaliacao

@register.filter
def pega_avaliador(objeto, avaliador):
    """Filtra para identificar avaliador."""
    avaliacao = objeto.filter(avaliador__id=avaliador)
    return avaliacao

@register.filter
def pega_avaliadores(objeto, tipo):
    """Filtra para identificar avaliadores."""
    avaliadores = list(objeto.filter(exame=tipo).order_by().values_list("avaliador", "avaliador__first_name", "avaliador__last_name").distinct())    
    return avaliadores

@register.filter
def add_orientador(lista, projeto):
    """adiciona na lista."""
    encontrou = False
    id = projeto.orientador.user.id
    for i in lista:
        if id == i[0]:
            encontrou = True
            break
    if not encontrou:
        lista += [(id, projeto.orientador.user.first_name, projeto.orientador.user.last_name)]
    return lista
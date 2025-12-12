#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 11 de Novembro de 2023
"""

import logging

from django import template
register = template.Library()

from projetos.models import Avaliacao2
#from users.models import PFEUser

# Get an instance of a logger
logger = logging.getLogger("django")

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
    """adiciona orientador na lista."""

    # Validações de entrada
    if not lista:
        lista = []

    if not projeto or not projeto.orientador or not projeto.orientador.user:
        return lista

    try:
        orientador_id = projeto.orientador.user.id
        orientador_nome = projeto.orientador.user.first_name or ""
        orientador_sobrenome = projeto.orientador.user.last_name or ""
        
        # Verificar se já existe na lista
        if not any(item[0] == orientador_id for item in lista):
            lista = list(lista) + [(orientador_id, orientador_nome, orientador_sobrenome)]
    
    except (AttributeError, TypeError) as e:
        logger.warning(f"Erro ao adicionar orientador: {e}")
    
    return lista
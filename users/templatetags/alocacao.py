#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Junho de 2025
"""

from django import template
register = template.Library()

from users.models import Alocacao

@register.filter
def alocacoes_insper(projeto):
    """
    Retorna as alocações só de estudantes do Insper de um projeto.
    """
    if not projeto:
        return None
    try:
        alocacoes = Alocacao.objects.filter(projeto=projeto, aluno__curso2__curso_do_insper=True)
    except Alocacao.DoesNotExist:
        alocacoes = None
    return alocacoes

@register.filter
def alocacoes_puxa_ids(relatos):
    """
    Retorna os IDs das alocações de um relato.
    """
    if not relatos:
        return None
    try:
        alocacoes = [relato.alocacao.id for relato in relatos]
    except AttributeError:
        alocacoes = None
    return alocacoes


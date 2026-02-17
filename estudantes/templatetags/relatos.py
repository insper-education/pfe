#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

import datetime
from django import template

from estudantes.models import Relato
from projetos.models import Evento
from projetos.support2 import busca_relatos as busca_relatos_external

register = template.Library()


@register.filter
def get_relatos(alocacao):
    """Retorna todos os possiveis relatos quinzenais da alocacao."""
    
    eventos = Evento.get_eventos(sigla="RQ", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
    relatos = []
    for index in range(len(eventos)):
        if not index: # index == 0:
            relato = Relato.objects.filter(alocacao=alocacao, momento__lte=eventos[0].endDate + datetime.timedelta(days=1)).order_by("momento").last()
        else:
            relato = Relato.objects.filter(alocacao=alocacao, momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), momento__lte=eventos[index].endDate + datetime.timedelta(days=1)).order_by("momento").last()
        relatos.append(relato)

    return list(zip(eventos, relatos, range(len(eventos))))


@register.filter
def busca_relatos(projeto):
    """Busca relatos quinzenais de um projeto."""
    return busca_relatos_external(projeto)

@register.filter
def has_relatos(projeto):
    """Retorna se houver algum relato quinzenal para o projeto."""            
    return Relato.objects.filter(alocacao__projeto=projeto).exists()


@register.filter
def get_relatos_edicao(edicao):
    """Retorna os relatos quinzenais do semestre."""
    
    if not edicao:
        return []

    if edicao != "todas":
        ano, semestre = map(int, edicao.split('.'))    
        eventos = Evento.get_eventos(sigla="RQ", ano=ano, semestre=semestre)
    else:
        eventos = Evento.get_eventos(sigla="RQ")
    
    return eventos

@register.filter
def porcentagem_relatos_avaliados(relatos):
    """Verifica se todos os relatos quinzenais foram avaliados."""
    total = len(relatos)
    if total == 0:
        return 0
    avaliados = 0
    for alocacao, relato in relatos.items():
        if relato[-1].avaliacao > -1:
            avaliados += 1
    return avaliados/total if total > 0 else 0

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
from projetos.support2 import busca_relatos

register = template.Library()


@register.filter
def get_relatos(alocacao):
    """Retorna todos os possiveis relatos quinzenais da alocacao."""
    
    eventos = Evento.get_eventos(sigla="RQ", ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
    relatos = []
    for index in range(len(eventos)):
        if not index: # index == 0:
            relato = Relato.objects.filter(alocacao=alocacao, momento__lte=eventos[0].endDate + datetime.timedelta(days=1)).order_by('momento').last()
        else:
            relato = Relato.objects.filter(alocacao=alocacao, momento__gt=eventos[index-1].endDate + datetime.timedelta(days=1), momento__lte=eventos[index].endDate + datetime.timedelta(days=1)).order_by("momento").last()
        relatos.append(relato)

    return zip(eventos, relatos, range(len(eventos)))


@register.filter
def traz_relatos(projeto):
    """Buscar os relatos."""
    return busca_relatos(projeto)

@register.filter
def has_relatos(projeto):
    """Retorna se houver algum relato quinzenal para o projeto."""            
    return Relato.objects.filter(alocacao__projeto=projeto).exists()
#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Maio de 2025
"""

from django import template

register = template.Library()

@register.filter
def data_evento(eventos, nome_evento):
    """Busca a data inicial de um evento em uma lista de eventos pelo nome."""
    return eventos.filter(tipo_evento__nome=nome_evento).last().startDate

def data_final_evento(eventos, nome_evento):
    """Busca a data final de um evento em uma lista de eventos pelo nome."""
    return eventos.filter(tipo_evento__nome=nome_evento).last().endDate

@register.filter
def data_evento_sigla(eventos, sigla_evento):
    """Busca a data inicial de um evento em uma lista de eventos pela sigla."""
    return eventos.filter(tipo_evento__sigla=sigla_evento).last().startDate

@register.filter
def data_final_evento_sigla(eventos, sigla_evento):
    """Busca a data final de um evento em uma lista de eventos pela sigla."""
    return eventos.filter(tipo_evento__sigla=sigla_evento).last().endDate
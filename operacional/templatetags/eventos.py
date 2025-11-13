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
    evento = eventos.filter(tipo_evento__nome=nome_evento).last()
    if evento:
        return evento.startDate
    raise ValueError(f"Nenhum evento encontrado com o nome '{nome_evento}'.")

def data_final_evento(eventos, nome_evento):
    """Busca a data final de um evento em uma lista de eventos pelo nome."""
    evento = eventos.filter(tipo_evento__nome=nome_evento).last()
    if evento:
        return evento.endDate
    raise ValueError(f"Nenhum evento encontrado com o nome '{nome_evento}'.")

@register.filter
def data_evento_sigla(eventos, sigla_evento):
    """Busca a data inicial de um evento em uma lista de eventos pela sigla."""
    evento = eventos.filter(tipo_evento__sigla=sigla_evento).last()
    if evento:
        return evento.startDate
    raise ValueError(f"Nenhum evento encontrado com a sigla '{sigla_evento}'.")

@register.filter
def data_final_evento_sigla(eventos, sigla_evento):
    """Busca a data final de um evento em uma lista de eventos pela sigla."""
    evento = eventos.filter(tipo_evento__sigla=sigla_evento).last()
    if evento:
        return evento.endDate
    raise ValueError(f"Nenhum evento encontrado com a sigla '{sigla_evento}'.")
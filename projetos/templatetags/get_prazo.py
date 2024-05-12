#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 30 de Novembro de 2023
"""

from django import template
from projetos.models import Evento

register = template.Library()

@register.filter
def get_prazo(relato):
    """Retorna a data para qual entrega o relato foi feito."""
    evento = Evento.objects.filter(tipo_de_evento=20, endDate__gte=relato.momento).order_by("endDate").first()
    if evento:
        return evento.endDate
    return None

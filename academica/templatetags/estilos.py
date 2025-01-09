#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

# from academica.models import ExibeNota

from django import template
register = template.Library()

@register.filter
def get_respostas_estilos_in_order(estilo):
    estilos = [
        estilo.estilo_comunicacao.resposta1,
        estilo.estilo_comunicacao.resposta2,
        estilo.estilo_comunicacao.resposta3,
        estilo.estilo_comunicacao.resposta4,
    ]
    respostas = [
        (estilo.prioridade_resposta1, estilos[estilo.prioridade_resposta1-1]),
        (estilo.prioridade_resposta2, estilos[estilo.prioridade_resposta2-1]),
        (estilo.prioridade_resposta3, estilos[estilo.prioridade_resposta3-1]),
        (estilo.prioridade_resposta4, estilos[estilo.prioridade_resposta4-1]),
    ]
    return respostas

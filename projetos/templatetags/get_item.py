#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Setembro de 2024
"""

from users.models import EstudanteEstiloComunicacao

from django import template

register = template.Library()

@register.filter
def get_selecao(estilo, estudante):
    try:
        return EstudanteEstiloComunicacao.objects.get(estilo_comunicacao=estilo, estudante=estudante)
    except EstudanteEstiloComunicacao.DoesNotExist:
        return None    
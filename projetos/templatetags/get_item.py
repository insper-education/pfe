#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 9 de Setembro de 2024
"""

from users.models import UsuarioEstiloComunicacao

from django import template

register = template.Library()

@register.filter
def get_selecao(estilo, usuario):
    if not usuario or not estilo:
        return None
    try:
        return UsuarioEstiloComunicacao.objects.get(estilo_comunicacao=estilo, usuario=usuario)
    except UsuarioEstiloComunicacao.DoesNotExist:
        return None

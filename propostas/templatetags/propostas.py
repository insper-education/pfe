#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Março de 2025
"""

from django import template

register = template.Library()


@register.filter
def contatos_tec(proposta):
    """Retorna todos os contatos técnicos."""
    if proposta is None:
        return None
    contatos = proposta.contatos.filter(tipo="T")
    return contatos

@register.filter
def contatos_adm(proposta):
    """Retorna todos os contatos administrativos."""
    if proposta is None:
        return None
    contatos = proposta.contatos.filter(tipo="A")
    return contatos

@register.filter
def contatos_tec3(proposta):
    """Retorna todos os contatos técnicos e completa com None para ter no mínimo 3 campos."""
    if proposta is None:
        return [None] * 3
    contatos = proposta.contatos.filter(tipo="T")
    return list(contatos) + [None] * (3 - len(contatos))

@register.filter
def contatos_adm3(proposta):
    """Retorna todos os contatos administrativos e completa com None para ter no mínimo 3 campos."""
    if proposta is None:
        return [None] * 3
    contatos = proposta.contatos.filter(tipo="A")
    return list(contatos) + [None] * (3 - len(contatos))

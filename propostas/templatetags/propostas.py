#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Março de 2025
"""

from django import template

from users.models import Opcao


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


@register.filter
def opcao_alocacao(proposta, alocacao):
    """Retorna a opção do estudante na proposta."""
    if proposta is None or alocacao is None or not hasattr(alocacao, "aluno") or alocacao.aluno is None:
        return "X"
    opcao = Opcao.objects.filter(proposta=proposta, aluno=alocacao.aluno).last()
    if opcao:
        return opcao.prioridade
    return 'X'  # Retorna 'X' se não houver opção registrada

#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 31 de Março de 2025
"""

from django import template

register = template.Library()

@register.filter
def autorizado(projeto, usuario):
    """Verifica se projeto pode ser visto por usuário."""
    if usuario.is_authenticated:
        if usuario.eh_parc:
            if projeto.proposta.organizacao == usuario.parceiro.organizacao:
                return True
            return False
        return True  # Teremos de analisar o caso de aluno e professor também
    return False

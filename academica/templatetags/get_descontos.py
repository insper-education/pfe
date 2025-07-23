#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Julho de 2025
"""

from academica.support2 import get_descontos_alocacao as get_descontos_alocacao_extern

from django import template
register = template.Library()


@register.filter
def get_descontos_alocacao(alocacao, request=None):
    """Recupera os descontos de alocação."""
    return get_descontos_alocacao_extern(alocacao)
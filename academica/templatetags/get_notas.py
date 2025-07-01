#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from projetos.support3 import get_notas_alocacao as get_notas_alocacao_extern

from django import template
register = template.Library()

@register.filter
def get_notas_alocacao(alocacao, request=None):
    """Recupera as notas de alocação."""
    return get_notas_alocacao_extern(alocacao, request=request)

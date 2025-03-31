#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 7 de Abril de 2024
"""

from django import template

register = template.Library()

@register.filter
def sem_externos(alocacoes):
    """Remore as alocacoes externas."""
    return alocacoes.filter(aluno__externo__isnull=True)

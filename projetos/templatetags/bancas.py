#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from django import template
from projetos.models import Banca

register = template.Library()

@register.filter()
def get_bancas(alocacao):
    """Retorna as bancas que estudante participou."""
    bancas_proj = Banca.objects.filter(projeto=alocacao.projeto)
    bancas_prob = Banca.objects.filter(alocacao=alocacao)
    return bancas_proj | bancas_prob
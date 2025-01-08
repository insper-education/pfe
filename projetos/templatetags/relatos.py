#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 8 de Janeiro de 2025
"""

from django import template

from projetos.support2 import get_relatos
from estudantes.models import Relato

register = template.Library()

@register.filter
def relatos(projeto):
    """Buscar os relatos."""
    return get_relatos(projeto)

@register.filter
def has_relatos(projeto):
    """Retorna se houver algum relato quinzenal para o projeto."""            
    return Relato.objects.filter(alocacao__projeto=projeto).exists()
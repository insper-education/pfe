#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 27 de Maio de 2025
"""

from django import template

register = template.Library()

@register.filter
def media_crs(alocacoes):
    """Verifica a média e desvio padrão dos CRs dos estudantes alocados."""
    if not alocacoes:
        return (0, 0)
    
    crs = [alocacao.aluno.cr for alocacao in alocacoes if alocacao.aluno and alocacao.aluno.cr is not None]
    
    if not crs:
        return (0, 0)
    
    media = sum(crs) / len(crs)
    desvio = (sum((x - media) ** 2 for x in crs) / len(crs)) ** 0.5
    
    return (media, desvio)

    

#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Junho de 2024
"""

from academica.models import ExibeNota

from academica.support3 import em_probation

from django import template
register = template.Library()

@register.filter
def exibe_notas(alocacao, exame):
    """Verifica se nota pode ser exibida para estudantes."""
    try:
        exibe = ExibeNota.objects.get(exame__sigla=exame, ano=alocacao.projeto.ano, semestre=alocacao.projeto.semestre)
    except Exception as e:
        return True
    return exibe.exibe


@register.filter
def exibe_notas_proj(projeto, exame):
    """Verifica se nota pode ser exibida para estudantes."""
    try:
        exibe = ExibeNota.objects.get(exame=exame, ano=projeto.ano, semestre=projeto.semestre)
    except Exception as e:
        return True
    return exibe.exibe


@register.filter
def exibe_notas_banca(banca):
    """Verifica se nota pode ser exibida para estudantes."""
    try:
        projeto = banca.get_projeto()
        exibe = ExibeNota.objects.get(exame=banca.composicao.exame, ano=projeto.ano, semestre=projeto.semestre)
    except Exception as e:
        return True
    return exibe.exibe


@register.filter
def exibe_notas_semestre(edicao, exame):
    """Verifica se nota pode ser exibida para estudantes."""
    if edicao is None:
        return True
    ano, semestre = edicao.split('.')
    try:
        exibe = ExibeNota.objects.get(exame=exame, ano=ano, semestre=semestre)
    except Exception as e:
        return True
    return exibe.exibe

@register.filter
def probation(alocacao):
    """Retorna se em probation."""
    return em_probation(alocacao)
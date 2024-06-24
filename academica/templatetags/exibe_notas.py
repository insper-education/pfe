#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Junho de 2024
"""

from academica.models import ExibeNota

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
    if banca.tipo_de_banca == 0:
        exame = "BF"
    elif banca.tipo_de_banca == 1:
        exame = "BI"
    elif banca.tipo_de_banca == 2:  # Banca Falconi
        exame = "F"
    elif banca.tipo_de_banca == 3:  # Banca Probation
        exame = "P"
    else:
        return True
    
    try:
        exibe = ExibeNota.objects.get(exame__sigla=exame, ano=banca.get_projeto().ano, semestre=banca.get_projeto().semestre)
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
#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 23 de Junho de 2024
"""

from django import template

from academica.models import ExibeNota
from academica.support3 import get_media_alocacao_i, em_probation
from academica.support4 import get_notas_estudante

from projetos.support3 import calcula_objetivos

from users.models import Alocacao

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


@register.filter
def get_medias_oo(alocacao):  # EVITAR USAR POIS MISTURA SEMESTRES (VER GET_OAS)
    """Retorna OOs."""
    alocacoes = Alocacao.objects.filter(id=alocacao.id)
    context = calcula_objetivos(alocacoes)
    return context

@register.filter
def get_media_alocacao(alocacao):
    """Retorna média individual de alocação."""
    if not alocacao:
        return None
    return get_media_alocacao_i(alocacao)

@register.filter
def media(alocacao):
    """Retorna média final."""
    return get_media_alocacao_i(alocacao)["media"]

@register.filter
def peso(alocacao):
    """Retorna peso final."""
    return get_media_alocacao_i(alocacao)["pesos"]

@register.filter
def recuper_notas_estudante(estudante):
    """Retorna notas do estudante no projeto."""
    return get_notas_estudante(estudante)

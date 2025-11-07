#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 7 de Novembro de 2025
"""

from django import template
register = template.Library()

from projetos.models import Coorientador, Banca, Encontro, Evento
from estudantes.models import EstiloComunicacao
from academica.support import get_respostas_estilos

@register.filter
def coorientacoes(usuario):
    """ Retorna coorientações por usuário. """
    return Coorientador.objects.filter(usuario=usuario).order_by("projeto__ano", "projeto__semestre")

@register.filter
def bancas(usuario):
    """ Retorna bancas com o usuário como membro. """
    return Banca.get_bancas_com_membro(usuario)

@register.filter
def mentorias(usuario):
    """ Retorna mentorias por usuário. """
    return Encontro.objects.filter(facilitador=usuario, projeto__isnull=False).order_by("startDate")

@register.filter
def aulas(usuario):
    """ Retorna aulas por usuário. """
    return Evento.objects.filter(tipo_evento__sigla="A", responsavel=usuario)

@register.filter
def estilos_respostas(usuario):
    """ Retorna respostas de estilos de comunicação do usuário. """
    return get_respostas_estilos(usuario)

@register.filter
def estilos_comunicacao(usuario):
    """ Retorna lista de estilos de comunicação. """
    return EstiloComunicacao.objects.all()
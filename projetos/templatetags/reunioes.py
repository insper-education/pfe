#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 24 de Novembro de 2025
"""

from django import template
from projetos.models import Reuniao, ReuniaoParticipante, Projeto
from users.models import Alocacao

register = template.Library()

@register.filter()
def get_reunioes(objeto):
    """Retorna as reuniões que o projeto do estudante teve."""
    if not objeto:
        return []
    try:
        if isinstance(objeto, Projeto):
            return Reuniao.objects.filter(projeto=objeto).order_by("data_hora")
        elif isinstance(objeto, Alocacao) and objeto.projeto:
            return Reuniao.objects.filter(projeto=objeto.projeto).order_by("data_hora")
    except Exception as e:
        return []

@register.filter(name="get_participacao")
def get_participacao(reuniao, user):
    """Retorna a participação de um usuário em uma reunião."""
    if not reuniao or not user:
        return None
    try:
        return ReuniaoParticipante.objects.get(reuniao=reuniao, participante=user)
    except ReuniaoParticipante.DoesNotExist:
        return None
    except Exception as e:
        return None

@register.filter(name="get_participantes")
def get_participantes(reuniao):
    """Retorna os participantes de uma reunião."""
    if not reuniao:
        return []
    try:
        return ReuniaoParticipante.objects.filter(reuniao=reuniao).select_related("participante").order_by("participante__first_name", "participante__last_name")
    except Exception as e:
        return []

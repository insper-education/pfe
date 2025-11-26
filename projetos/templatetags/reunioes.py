#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 24 de Novembro de 2025
"""

from django import template
from projetos.models import Reuniao, ReuniaoParticipante

register = template.Library()

@register.filter()
def get_reunioes(alocacao):
    """Retorna as reuniões que o projeto do estudante teve."""
    if not alocacao:
        return []
    try:
        return Reuniao.objects.filter(projeto=alocacao.projeto).order_by("data_hora")
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

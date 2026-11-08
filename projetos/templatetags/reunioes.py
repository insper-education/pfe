#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 24 de Novembro de 2025
"""

from django import template
from collections import OrderedDict
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


@register.filter()
def get_abonos_falta(reunioes):
    """Retorna lista de (data, estudantes) com abono de falta agrupado por dia."""
    if not reunioes:
        return []
    try:
        if hasattr(reunioes, "values_list"):
            reunioes_abono = reunioes.filter(visita_externa=True)
            ids_reunioes = reunioes_abono.values_list("id", flat=True)
        else:
            ids_reunioes = [r.id for r in reunioes if getattr(r, "visita_externa", False)]

        participantes = (
            ReuniaoParticipante.objects
            .filter(reuniao_id__in=ids_reunioes, situacao=1, participante__tipo_de_usuario=1)
            .select_related("reuniao", "participante")
            .order_by("reuniao__data_hora", "participante__first_name", "participante__last_name")
        )

        por_dia = OrderedDict()
        for rp in participantes:
            if not rp.reuniao or not rp.reuniao.data_hora:
                continue
            dia = rp.reuniao.data_hora.date()
            if dia not in por_dia:
                por_dia[dia] = set()
            nome = rp.participante.get_full_name() if rp.participante else ""
            if nome:
                por_dia[dia].add(nome)

        for dia in por_dia:
            por_dia[dia] = sorted(por_dia[dia], key=str.casefold)

        return list(por_dia.items())
    except Exception as e:
        return []


@register.filter()
def get_estudantes_abonados(reunioes):
    """Retorna lista de (estudantes, datas abonadas)."""
    if not reunioes:
        return []
    try:
        if hasattr(reunioes, "values_list"):
            reunioes_abono = reunioes.filter(visita_externa=True)
            ids_reunioes = reunioes_abono.values_list("id", flat=True)
        else:
            ids_reunioes = [r.id for r in reunioes if getattr(r, "visita_externa", False)]

        participantes = (
            ReuniaoParticipante.objects
            .filter(reuniao_id__in=ids_reunioes, situacao=1, participante__tipo_de_usuario=1)
            .select_related("reuniao", "participante")
            .order_by("participante__first_name", "participante__last_name", "reuniao__data_hora")
        )

        por_estudante = OrderedDict()
        for rp in participantes:
            if not rp.participante or not rp.reuniao or not rp.reuniao.data_hora:
                continue
            nome = rp.participante.get_full_name()
            dia = rp.reuniao.data_hora.date()
            if nome not in por_estudante:
                por_estudante[nome] = set()
            por_estudante[nome].add(dia)

        for nome in por_estudante:
            por_estudante[nome] = sorted(por_estudante[nome])

        return list(por_estudante.items())
    except Exception as e:
        return []
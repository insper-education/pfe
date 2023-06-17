#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 13 de Junho de 2023
"""

import dateutil.parser

from django.shortcuts import render

from projetos.models import Evento


def get_limite_propostas(configuracao):
    if configuracao.semestre == 1:
        evento = Evento.objects.filter(tipo_de_evento=123, endDate__year=configuracao.ano, endDate__month__lt=7).order_by("endDate", "startDate").last()
    else:
        evento = Evento.objects.filter(tipo_de_evento=123, endDate__year=configuracao.ano, endDate__month__gt=6).order_by("endDate", "startDate").last()
    # (123, 'Indicação de interesse nos projetos do próximo semestre pelos estudante')

    if evento is not None:
        return evento.endDate
    
    inicio_pfe = dateutil.parser.parse("07/06/2018").date()
    return inicio_pfe

def usuario_sem_acesso(request, acessos):
    
    if (not request.user.is_authenticated) or (request.user is None):
        mensagem = "Você não está autenticado!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    if request.user.tipo_de_usuario not in acessos:
        mensagem = "Você não tem privilégios de acesso a essa área!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

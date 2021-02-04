#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Dezembro de 2020
"""

import datetime

from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse

from projetos.models import Aviso, Evento, Configuracao


@login_required
@permission_required("users.altera_professor", login_url='/')
def index_operacional(request):
    """Mostra página principal para equipe operacional."""

    return render(request, 'operacional/index_operacional.html')


@login_required
@permission_required('users.altera_professor', login_url='/')
def avisos_listar(request):
    """Mostra toda a tabela de avisos da coordenação do PFE."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    qualquer_aviso = list(Aviso.objects.all())

    eventos = Evento.objects.filter(startDate__year=configuracao.ano)
    if configuracao.semestre == 1:
        qualquer_evento = list(eventos.filter(startDate__month__lt=7))
    else:
        qualquer_evento = list(eventos.filter(startDate__month__gt=6))

    avisos = sorted(qualquer_aviso+qualquer_evento, key=lambda t: t.get_data())

    context = {
        'avisos': avisos,
        'configuracao' : configuracao,
        'hoje' : datetime.date.today(),
        'filtro' : "todos",
    }
    return render(request, 'operacional/avisos_listar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def edita_aviso(request, primakey):
    """Edita aviso."""

    try:
        aviso = Aviso.objects.get(pk=primakey)
    except Aviso.DoesNotExist:
        return HttpResponse("Aviso não encontrado.", status=401)

    if request.method == 'POST':
        if 'aviso' in request.POST:
            aviso.mensagem = request.POST['aviso']
            aviso.save()
            return redirect('avisos_listar')

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {
        'aviso': aviso,
    }

    return render(request, 'operacional/edita_aviso.html', context)

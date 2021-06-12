#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Dezembro de 2020
"""

import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

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
    configuracao = get_object_or_404(Configuracao)

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


def trata_aviso(aviso, request):
    try:
        aviso.titulo = request.POST['titulo']
        aviso.delta = int(request.POST['delta'])
        aviso.mensagem = request.POST['mensagem']
        aviso.tipo_de_evento = int(request.POST['evento'])

        aviso.coordenacao = "coordenacao" in request.POST
        aviso.comite_pfe = "comite_pfe" in request.POST
        aviso.todos_alunos = "todos_alunos" in request.POST
        aviso.todos_orientadores = "todos_orientadores" in request.POST
        aviso.contatos_nas_organizacoes = "contatos_nas_organizacoes" in request.POST

    except (ValueError, OverflowError):
        return HttpResponse("Algum erro não identificado.", status=401)

    aviso.save()


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def edita_aviso(request, primarykey):
    """Edita aviso."""
    aviso = get_object_or_404(Aviso, pk=primarykey)

    if request.method == 'POST':
        if 'mensagem' in request.POST:
            trata_aviso(aviso, request)
            return redirect('avisos_listar')

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {
        "aviso": aviso,
        "eventos": Evento.TIPO_EVENTO,
    }

    return render(request, 'operacional/edita_aviso.html', context)



@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def cria_aviso(request):
    """Cria aviso."""

    if request.method == 'POST':
        
        if 'mensagem' in request.POST:

            aviso = Aviso.create()

            trata_aviso(aviso, request)
            
            return redirect('avisos_listar')

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {
        "eventos": Evento.TIPO_EVENTO,
    }

    return render(request, 'operacional/edita_aviso.html', context)

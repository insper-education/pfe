#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Dezembro de 2020
"""

import datetime
import dateutil.parser

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from projetos.support import simple_upload
from projetos.models import get_upload_path

from projetos.models import Aviso, Certificado, Evento, Configuracao, Projeto
from users.models import PFEUser
# from users.models import Aluno, Professor, Administrador, Parceiro

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_operacional(request):
    """Mostra página principal para equipe operacional."""
    return render(request, 'operacional/index_operacional.html')


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def avisos_listar(request):
    """Mostra toda a tabela de avisos da coordenação do PFE."""
    configuracao = get_object_or_404(Configuracao)

    eventos = Evento.objects.filter(startDate__year=configuracao.ano)
    if configuracao.semestre == 1:
        eventos = eventos.filter(startDate__month__lt=7)
    else:
        eventos = eventos.filter(startDate__month__gt=6)

    avisos = []
    for evento in eventos:
        avisos.append(
            {"class": "Evento",
             "tipo_de_evento": evento.tipo_de_evento,
             "titulo": evento.get_title(),
             "data": evento.get_data(),
             "id": None,
             "realizado": False,
             "color": evento.get_color(),
            })

        for aviso in Aviso.objects.filter(tipo_de_evento=evento.tipo_de_evento):
            avisos.append(
                {"class": "Aviso",
                "tipo_de_evento": aviso.tipo_de_evento,
                "titulo": aviso.titulo,
                "data": evento.get_data() + datetime.timedelta(days=aviso.delta),
                "id": aviso.id,
                "realizado": aviso.realizado,
                "data_realizado": aviso.data_realizado,
                "evento": aviso.get_evento(),
                "delta": aviso.delta,
                "coordenacao": aviso.coordenacao,
                "comite_pfe": aviso.comite_pfe,
                "todos_alunos": aviso.todos_alunos,
                "todos_orientadores": aviso.todos_orientadores,
                "contatos_nas_organizacoes": aviso.contatos_nas_organizacoes,
                })

    avisos = sorted(avisos, key=lambda t: t["data"])

    # IDs dos avisos buscados
    ids = [d['id'] for d in avisos if d['id'] is not None]

    sem_avisos = Aviso.objects.all().exclude(id__in=ids)
    for aviso in sem_avisos:
            avisos.append(
                {"class": "Aviso",
                "tipo_de_evento": aviso.tipo_de_evento,
                "titulo": aviso.titulo,
                "data": None,
                "id": aviso.id,
                "realizado": aviso.realizado,
                "data_realizado": aviso.data_realizado,
                "evento": aviso.get_evento(),
                "delta": aviso.delta,
                "coordenacao": aviso.coordenacao,
                "comite_pfe": aviso.comite_pfe,
                "todos_alunos": aviso.todos_alunos,
                "todos_orientadores": aviso.todos_orientadores,
                "contatos_nas_organizacoes": aviso.contatos_nas_organizacoes,
                })

    context = {
        'avisos': avisos,
        'configuracao' : configuracao,
        'hoje' : datetime.date.today(),
        'filtro' : "todos",
    }

    return render(request, 'operacional/avisos_listar.html', context)


def trata_aviso(aviso, request):
    """Puxa dados do request e põe em aviso."""
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

    return None


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def edita_aviso(request, primarykey):
    """Edita aviso."""
    aviso = get_object_or_404(Aviso, pk=primarykey)

    if request.method == 'POST':
        if 'mensagem' in request.POST:
            erro = trata_aviso(aviso, request)
            if erro:
                return erro
            return redirect('avisos_listar')

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {
        "aviso": aviso,
        "eventos": Evento.TIPO_EVENTO,
    }

    return render(request, 'operacional/edita_aviso.html', context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def carregar_certificado(request):
    """Carrega certificado na base de dados do PFE."""
    if request.method == 'POST':
        if 'usuario' in request.POST and 'tipo' in request.POST and "documento" in request.FILES:

            certificado = Certificado.create()

            usuario_id = request.POST.get('usuario', None)
            if usuario_id:
                usuario = get_object_or_404(PFEUser, id=usuario_id)
                certificado.usuario = usuario

            projeto_id = request.POST.get('projeto', None)
            if projeto_id:
                projeto = get_object_or_404(Projeto, id=projeto_id)
                certificado.projeto = projeto

            if 'data' in request.POST:
                try:
                    certificado.data = dateutil.parser\
                        .parse(request.POST['data'])
                except (ValueError, OverflowError):
                    certificado.data = datetime.date.today()

            tipo = request.POST.get('tipo', None)
            if tipo:
                certificado.tipo_de_certificado = int(tipo)

            certificado.observacao = request.POST.get('observacao', None)

            certificado.save()

            if 'documento' in request.FILES:
                documento = simple_upload(request.FILES['documento'],
                                          path=get_upload_path(certificado, ""))
                certificado.documento = documento[len(settings.MEDIA_URL):]

            certificado.save()

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "Certificado inserido na base de dados.",
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, 'generic.html', context=context)

    projetos = Projeto.objects.all()
    usuarios = PFEUser.objects.all()

    context = {
        "TIPO_DE_CERTIFICADO": Certificado.TIPO_DE_CERTIFICADO,
        "projetos": projetos,
        "usuarios": usuarios,
    }

    return render(request, 'operacional/carregar_certificado.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def cria_aviso(request):
    """Cria aviso."""
    if request.method == 'POST':

        if 'mensagem' in request.POST:

            aviso = Aviso.create()

            erro = trata_aviso(aviso, request)
            if erro:
                return erro

            return redirect('avisos_listar')

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {
        "eventos": Evento.TIPO_EVENTO,
    }

    return render(request, 'operacional/edita_aviso.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def deleta_aviso(request, primarykey):
    """Apaga aviso."""
    Aviso.objects.filter(id=primarykey).delete()
    return redirect('avisos_listar')

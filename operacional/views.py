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
from django.http import HttpResponse, JsonResponse

from django.shortcuts import render, redirect, get_object_or_404

from projetos.support import get_upload_path, simple_upload

from projetos.models import Aviso, Certificado, Evento, Configuracao
from projetos.models import Projeto, Banca, Conexao

from users.models import PFEUser, Aluno, Professor, Parceiro
from users.support import get_edicoes

from projetos.tipos import TIPO_EVENTO


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
             "evento": evento,
             "data": evento.get_data(),
             "id": None,
            })

        for aviso in Aviso.objects.filter(tipo_de_evento=evento.tipo_de_evento):
            avisos.append(
                {"class": "Aviso",
                 "aviso": aviso,
                 "data": evento.get_data() + datetime.timedelta(days=aviso.delta),
                 "id": aviso.id,
                })

    avisos = sorted(avisos, key=lambda t: t["data"])

    # Para caso exista um aviso que não está associado a um evento (faltou marcar evento por exemplo)
    ids = [d['id'] for d in avisos if d['id'] is not None]      # IDs dos avisos buscados
    sem_avisos = Aviso.objects.all().exclude(id__in=ids)
    for aviso in sem_avisos:
            avisos.append(
                {"class": "Aviso",
                 "aviso": aviso,
                 "data": None,
                 "id": aviso.id,
                })

    context = {
        "avisos": avisos,
        "hoje" : datetime.date.today(),
        "filtro" : "todos",
    }

    return render(request, "operacional/avisos_listar.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def emails(request):
    """Gera listas de emails, com alunos, professores, parceiros, etc.""" 
    edicoes, _, _ = get_edicoes(Aluno)

    configuracao = get_object_or_404(Configuracao)
    atual = str(configuracao.ano)+"."+str(configuracao.semestre)

    context = {
        "membros_comite": PFEUser.objects.filter(membro_comite=True),
        "todos_alunos": Aluno.objects.filter(trancado=False),
        "todos_professores": Professor.objects.all(),
        "todos_parceiros": Parceiro.objects.all(),
        "edicoes": edicoes,
        "atual": atual,
        "coordenacao": configuracao.coordenacao,
        "coordenacoes": PFEUser.objects.filter(coordenacao=True),
    }

    return render(request, 'operacional/emails.html', context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def emails_semestre(request):
    """Gera listas de emails por semestre."""
    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = request.POST["edicao"].split('.')

            estudantes = []  # Estudantes do semestre
            orientadores = []  # Orientadores por semestre
            organizacoes = []  # Controla as organizações participantes p/semestre
            #parceiros = []  # Parceiros das Organizações no semestre
            membros_bancas = []  # Membros das bancas

            for projeto in Projeto.objects.filter(ano=ano).filter(semestre=semestre):
                if Aluno.objects.filter(alocacao__projeto=projeto):  # checa se há alunos
                    estudantes += Aluno.objects.filter(trancado=False).\
                        filter(alocacao__projeto=projeto).\
                        filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

                if projeto.orientador and (projeto.orientador not in orientadores):
                    orientadores.append(projeto.orientador)  # Junta orientadores do semestre

                if projeto.organizacao not in organizacoes:
                    organizacoes.append(projeto.organizacao)  # Junta organizações do semestre

                # Parceiros de todas as organizações parceiras
                # parceiros = Parceiro.objects.filter(organizacao__in=organizacoes,
                #                                     user__is_active=True)
                # conexoes = Conexao.objects.filter(projeto=projeto, parceiro__user__is_active=True)
                conexoes = Conexao.objects.filter(projeto=projeto)

                bancas = Banca.objects.filter(projeto=projeto)
                for banca in bancas:
                    if banca.membro1 and (banca.membro1 not in membros_bancas):
                        membros_bancas.append(banca.membro1)
                    if banca.membro2 and (banca.membro2 not in membros_bancas):
                        membros_bancas.append(banca.membro2)
                    if banca.membro3 and (banca.membro3 not in membros_bancas):
                        membros_bancas.append(banca.membro3)

            # Cria listas para estudantes que ainda não estão em projetos
            estudantes_sem_projeto = Aluno.objects.filter(trancado=False).\
                filter(anoPFE=ano).\
                filter(semestrePFE=semestre).\
                filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
            for estudante in estudantes_sem_projeto:
                if estudante not in estudantes:
                    estudantes.append(estudante)

            data = {}  # Dicionario com as pessoas do projeto
            data["Estudantes"] = []
            for i in estudantes:
                data["Estudantes"].append([i.user.first_name, i.user.last_name, i.user.email])

            data["Orientadores"] = []
            for i in orientadores:
                data["Orientadores"].append([i.user.first_name, i.user.last_name, i.user.email])

            data["Parceiros"] = []
            # for i in parceiros:
            #     data["Parceiros"].append([i.user.first_name, i.user.last_name, i.user.email])
            for c in conexoes:
                data["Parceiros"].append([c.parceiro.user.first_name, c.parceiro.user.last_name, c.parceiro.user.email])

            data["Bancas"] = []
            for i in membros_bancas:
                data["Bancas"].append([i.first_name, i.last_name, i.email])

            return JsonResponse(data)

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def emails_projetos(request):
    """Gera listas de emails, com alunos, professores, parceiros, etc."""
    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = request.POST["edicao"].split('.')
            projetos = Projeto.objects.filter(ano=ano).filter(semestre=semestre)
            context = {
                "projetos": projetos,
            }
            return render(request, "operacional/emails_projetos.html", context=context)
    return HttpResponse("Algum erro não identificado.", status=401)



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

    if request.method == "POST":
        if "mensagem" in request.POST:
            erro = trata_aviso(aviso, request)
            if erro:
                return erro
            return redirect("avisos_listar")

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {
        "aviso": aviso,
        "eventos": TIPO_EVENTO,
    }

    return render(request, "operacional/edita_aviso.html", context)


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

            if "data" in request.POST:
                try:
                    certificado.data = dateutil.parser\
                        .parse(request.POST["data"])
                except (ValueError, OverflowError):
                    certificado.data = datetime.date.today()

            tipo = request.POST.get("tipo", None)
            if tipo:
                certificado.tipo_de_certificado = int(tipo)

            certificado.observacao = request.POST.get("observacao", None)

            certificado.save()

            if "documento" in request.FILES:
                documento = simple_upload(request.FILES["documento"],
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
        "eventos": TIPO_EVENTO,
    }

    return render(request, 'operacional/edita_aviso.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def deleta_aviso(request, primarykey):
    """Apaga aviso."""
    Aviso.objects.filter(id=primarykey).delete()
    return redirect('avisos_listar')


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def plano_aulas(request):
    """Gera tabela com aulas do semestre."""

    if request.is_ajax():

        if "edicao" in request.POST:
            
            ano, semestre = request.POST["edicao"].split('.')
            eventos = Evento.objects.filter(startDate__year=ano, tipo_de_evento=12)  # 12, 'Aula PFE'

            if semestre == "1":
                eventos = eventos.filter(startDate__month__lte=6)
            else:
                eventos = eventos.filter(startDate__month__gte=7)
            
            context = {"aulas": eventos,}
            return render(request, "operacional/plano_aulas.html", context=context)
        
        return HttpResponse("Algum erro não identificado.", status=401)
    
    edicoes, _, _ = get_edicoes(Aluno)
    context = {
        "edicoes": edicoes,
    }
    return render(request, "operacional/plano_aulas.html", context=context)

    


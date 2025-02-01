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

from django.db.models.functions import Coalesce

from django.shortcuts import render, redirect, get_object_or_404

from .support import trata_aviso

from administracao.models import TipoCertificado, TipoEvento

from projetos.support import get_upload_path, simple_upload

from projetos.models import Aviso, Certificado, Evento, Configuracao
from projetos.models import Projeto, Banca, Conexao

from users.models import PFEUser, Aluno, Professor, Parceiro
from users.support import get_edicoes

from projetos.tipos import TIPO_EVENTO

from academica.models import Composicao
from academica.support import filtra_composicoes


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_operacional(request):
    """Mostra página principal para equipe operacional."""
    context = {"titulo": { "pt": "Operacional", "en": "Operational" },}
    if "/operacional/operacional" in request.path:
        return render(request, "operacional/operacional.html", context=context)
    else:
        return render(request, "operacional/index_operacional.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def avisos_listar(request):
    """Mostra toda a tabela de avisos da coordenação."""
    configuracao = get_object_or_404(Configuracao)
    eventos = Evento.get_eventos(configuracao=configuracao)

    avisos = []
    for evento in eventos:
        avisos.append(
            {"class": "Evento",
             "evento": evento,
             "data": evento.get_data(),
             "id": None,
            })

        for aviso in Aviso.objects.filter(tipo_evento=evento.tipo_evento):
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

    cabecalhos = [
        {"pt": "&#10003;", "en": "&#10003;"},
        {"pt": "Data", "en": "Date"},
        {"pt": "Público", "en": "Target"},
        {"pt": "Título", "en": "Title"},
    ]

    captions = [
          {"sigla": "Co", "pt": "Coordenação", "en": "Coordination"},
          {"sigla": "Op", "pt": "Equipe Operacional", "en": "Operational Team"},
          {"sigla": "Cm", "pt": "Comitê Capstone", "en": "Capstone Committee"},
          {"sigla": "Es", "pt": "Estudantes", "en": "Students"},
          {"sigla": "Or", "pt": "Orientadores", "en": "Advisors"},
          {"sigla": "Og", "pt": "Contatos nas Organizações", "en": "Contacts in Organizations"},
    ]

    context = {
        "titulo": { "pt": "Avisos", "en": "Notices" },
        "avisos": avisos,
        "hoje" : datetime.date.today(),
        "filtro" : "todos",
        "cabecalhos": cabecalhos,
        "captions": captions,
    }

    return render(request, "operacional/avisos_listar.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def emails(request):
    """Gera listas de emails, com alunos, professores, parceiros, etc.""" 
    configuracao = get_object_or_404(Configuracao)
    context = {
        "titulo": { "pt": "Listas de e-mails", "en": "Email lists" },
        "membros_comite": PFEUser.objects.filter(membro_comite=True),
        "todos_alunos": Aluno.objects.filter(trancado=False),
        "todos_professores": Professor.objects.all(),
        "todos_parceiros": Parceiro.objects.all(),
        "edicoes": get_edicoes(Aluno)[0],
        "atual": str(configuracao.ano)+"."+str(configuracao.semestre),
        "coordenacao": configuracao.coordenacao,
    }
    return render(request, "operacional/emails.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def emails_semestre(request):
    """Gera listas de emails por semestre."""
    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = request.POST["edicao"].split('.')

            orientadores = set()  # Orientadores por semestre
            organizacoes = set()  # Controla as organizações participantes p/semestre
            conexoes = []  # Parceiros das Organizações no semestre
            membros_bancas = set()  # Membros das bancas

            for projeto in Projeto.objects.filter(ano=ano, semestre=semestre):
                if projeto.orientador:
                    orientadores.add(projeto.orientador)  # Junta orientadores do semestre
                if projeto.organizacao:
                    organizacoes.add(projeto.organizacao)  # Junta organizações do semestre

                conexoes += list(Conexao.objects.filter(projeto=projeto))

                bancas = Banca.objects.filter(projeto=projeto)
                for banca in bancas:
                    membros_bancas.update(banca.membros())

            data = {}  # Dicionario com as pessoas do projeto

            # Estudantes do semestre
            estudantes = Aluno.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre).select_related("user")
            data["Estudantes"] = list(estudantes.values_list("user__first_name", "user__last_name", "user__email"))

            # Estudantes do semestre do Insper
            estudantesInsper = Aluno.objects.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre, curso2__curso_do_insper=True).select_related("user")
            data["EstudantesInsper"] = list(estudantesInsper.values_list("user__first_name", "user__last_name", "user__email"))

            # Orientadores
            data["Orientadores"] = [[i.user.first_name, i.user.last_name, i.user.email] for i in orientadores]

            # Parceiros
            data["Parceiros"] = [[c.parceiro.user.first_name, c.parceiro.user.last_name, c.parceiro.user.email] for c in conexoes]

            # Bancas
            data["Bancas"] = [[i.first_name, i.last_name, i.email] for i in membros_bancas]

            return JsonResponse(data)

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def emails_projetos(request):
    """Gera listas de emails, com alunos, professores, parceiros, etc."""
    if request.is_ajax() and "edicao" in request.POST:
        ano, semestre = request.POST["edicao"].split('.')
        context = {"projetos": Projeto.objects.filter(ano=ano).filter(semestre=semestre),}
        return render(request, "operacional/emails_projetos.html", context=context)
    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
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
        "eventos": TipoEvento.objects.all(),
    }

    return render(request, "operacional/edita_aviso.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def carregar_certificado(request):
    """Carrega certificado na base de dados."""
    if request.method == "POST":
        if "usuario" in request.POST and "tipo" in request.POST and "documento" in request.FILES:

            certificado = Certificado()

            usuario_id = request.POST.get("usuario", None)
            certificado.usuario = get_object_or_404(PFEUser, id=usuario_id) if usuario_id else None
                
            projeto_id = request.POST.get("projeto", None)
            certificado.projeto = get_object_or_404(Projeto, id=projeto_id) if projeto_id else None

            if "data" in request.POST:
                try:
                    certificado.data = dateutil.parser.parse(request.POST["data"])
                except (ValueError, OverflowError):
                    certificado.data = datetime.date.today()
            else:
                certificado.data = datetime.date.today()

            # TROCAR O NUMERO POR UM TEXTO
            tipo = request.POST.get("tipo", None)
            tipocertificado = get_object_or_404(TipoCertificado, id=tipo) if tipo else None
            certificado.tipo_certificado = tipocertificado

            certificado.observacao = request.POST.get("observacao", None)

            if "documento" in request.FILES:
                documento = simple_upload(request.FILES["documento"],
                                          path=get_upload_path(certificado, ""))
                certificado.documento = documento[len(settings.MEDIA_URL):]

            certificado.save()

            mensagem = "Certificado inserido na base de dados."
            mensagem += "<br><b>Usuário</b>: " + str(certificado.usuario)
            mensagem += "<br><b>Projeto</b>: " + str(certificado.projeto)
            mensagem += "<br><b>Data</b>: " + str(certificado.data)
            mensagem += "<br><b>Tipo</b>: " + str(certificado.tipo_certificado.titulo)
            if certificado.observacao:
                mensagem += "<br><b>Observação</b>: " + str(certificado.observacao)
            
            mensagem += "<br><b>Documento</b>: " + str(certificado.documento)

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": mensagem,
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, "generic.html", context=context)

    projetos = Projeto.objects.annotate(
        titulo=Coalesce("titulo_final", "proposta__titulo")
    ).order_by("-ano", "-semestre", "titulo")

    usuarios = PFEUser.objects.all()

    tipos_certificados = TipoCertificado.objects.all()

    context = {
        "titulo": {"pt": "Carregar Certificado", "en": "Load Certificate"},
        "tipos_certificados": tipos_certificados,
        "projetos": projetos,
        "usuarios": usuarios,
    }

    return render(request, "operacional/carregar_certificado.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cria_aviso(request):
    """Cria aviso."""
    if request.method == "POST":

        if "mensagem" in request.POST:
            aviso = Aviso()
            erro = trata_aviso(aviso, request)
            if erro:
                return erro

            return redirect("avisos_listar")

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    context = {"eventos": TipoEvento.objects.all(),}
    return render(request, "operacional/edita_aviso.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
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
            context = {
                "aulas": Evento.get_eventos(nome="Aula", ano=ano, semestre=semestre),
                "composicoes": filtra_composicoes(Composicao.objects.all(), ano, semestre),
                }
            return render(request, "operacional/plano_aulas.html", context=context)
        
        return HttpResponse("Algum erro não identificado.", status=401)
    
    context = {
        "titulo": { "pt": "Plano de Aulas", "en": "Class Schedule" },
        "edicoes": get_edicoes(Projeto)[0],
    }
    return render(request, "operacional/plano_aulas.html", context=context)

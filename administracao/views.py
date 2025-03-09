#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import os
import json
import re
import tablib
import axes.utils
import datetime
import logging
import requests
import sys
import django
import celery
import pkg_resources

from celery import Celery

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db import connection
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone


from axes.models import AccessAttempt, AccessLog

from .support import registra_organizacao, registro_usuario
from .support import usuario_sem_acesso, envia_senha_mensagem
from .support import puxa_github, backup_github
from .support2 import create_backup, get_resource, get_queryset

from academica.models import CodigoConduta

from administracao.models import Estrutura

from documentos.support import render_to_pdf

from estudantes.models import Pares

from operacional.models import Curso

from propostas.support import ordena_propostas

from projetos.models import Configuracao, Organizacao, Proposta, Projeto
from projetos.models import Avaliacao2, Feedback, Disciplina
from projetos.support import simple_upload, get_upload_path
from projetos.support2 import get_pares_colegas

from users.models import PFEUser, Aluno, Professor, Parceiro, Administrador
from users.models import Opcao, Alocacao
from users.support import adianta_semestre, adianta_semestre_conf, get_edicoes


celery_app = Celery()

# Get an instance of a logger
logger = logging.getLogger("django")

@login_required
@permission_required("users.view_administrador", raise_exception=True)
def index_administracao(request):
    """Mostra página principal para administração do sistema."""
    context = {"titulo": {"pt": "Administração", "en": "Administration"},}
    if "/administracao/administracao" in request.path:
        return render(request, "administracao/administracao.html", context=context)
    else:
        return render(request, "administracao/index_admin.html", context=context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def index_carregar(request):
    """Para carregar dados de arquivos para o servidor."""
    context = {"titulo": {"pt": "Carregar Dados", "en": "Load Data"},}
    return render(request, "administracao/carregar.html", context=context)


@login_required
@transaction.atomic
@permission_required("projetos.add_disciplina", raise_exception=True)
def cadastrar_disciplina(request, proposta_id=None):
    """Cadastra Organização na base de dados."""
    cabecalhos = [{"pt": "Disciplinas Cadastradas", "en": "Registered Courses"},]
    context = {
        "titulo": {"pt": "Cadastro de Disciplina", "en": "Course Registration"},
        "disciplinas": Disciplina.objects.all().order_by("nome"),
        "Disciplina": Disciplina,
        "cabecalhos": cabecalhos,
    }
    if request.method == "POST":
        try:
            assert "nome" in request.POST
            disciplina, _created = Disciplina.objects.get_or_create(nome=request.POST["nome"])
            if not _created:
                context["mensagem_alerta_fade"] = {"pt": "Conflito: Disciplina já cadastrada", "en": "Conflict: Course already registered"}
            else:
                disciplina.save()
                context["mensagem_alerta_fade"] = {"pt": "Disciplina cadastrada na base de dados.", "en": "Course registered in the database."}

        except:
            return HttpResponse("<h3 style='color:red'>Falha na inserção na base da dados.<br>"+settings.CONTATO+"<h3>")

    return render(request, "administracao/cadastra_disciplina.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_organizacao(request, proposta_id=None):
    """Cadastra Organização na base de dados."""
    if request.method == "POST":

        if "nome" in request.POST and "sigla" in request.POST:

            org_ja_existe = Organizacao.objects.filter(nome=request.POST["nome"]) | Organizacao.objects.filter(sigla=request.POST["sigla"])
            if org_ja_existe:
                context = {
                    "voltar": True,
                    "organizacao": org_ja_existe.last(),
                    "area_principal": True,
                    "mensagem": "<h3 style='color:red'>Conflito: Organização já cadastrada!</h3>",
                }

            else:
                organizacao, mensagem, codigo = registra_organizacao(request)
                if codigo != 200:
                    return HttpResponse(mensagem, status=codigo)

                context = {
                    "voltar": True,
                    "organizacao": organizacao,
                    "organizacoes_lista": True,
                    "area_principal": True,
                    "mensagem": "Organização inserida na base de dados.",
                }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, "generic.html", context=context)

    proposta = None
    if proposta_id:
        proposta = get_object_or_404(Proposta, id=proposta_id)

    context = {
        "titulo": {"pt": "Cadastro de Organização", "en": "Organization Registration"},
        "proposta": proposta,
        "organizacao": Organizacao,
    }
    
    return render(request, "administracao/cadastra_organizacao.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_organizacao(request, primarykey):
    """Edita Organização na base de dados."""

    organizacao = get_object_or_404(Organizacao, id=primarykey)

    if request.method == "POST":

        if "nome" in request.POST and "sigla" in request.POST:

            _, mensagem, codigo = registra_organizacao(request, organizacao)
            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

            context = {
                "voltar": True,
                "organizacao": organizacao,
                "organizacoes_lista": True,
                "area_principal": True,
                "mensagem": "Organização atualizada na base de dados.",
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, "generic.html", context=context)

    context = {
        "titulo": {"pt": "Edição de Organização", "en": "Organization Edition"},
        "organizacao": organizacao,
        "edicao": True,
    }

    return render(request, "administracao/cadastra_organizacao.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_usuario(request):
    """Cadastra usuário na base de dados."""
    if request.method == "POST":

        if "email" in request.POST:

            usr_ja_existe = PFEUser.objects.filter(email=request.POST["email"])
            if usr_ja_existe:
                context = {
                    "voltar": True,
                    "usuario": usr_ja_existe.last(),
                    "area_principal": True,
                    "mensagem": "<h3 style='color:red'>Conflito: Usuário já cadastrada!</h3>",
                }

            else:
                mensagem, codigo, user = registro_usuario(request)

                if user is not None and "envia" in request.POST:
                    mensagem_email, codigo_email = envia_senha_mensagem(user)
                    mensagem += mensagem_email
                    if codigo_email != 200:
                        return HttpResponse(mensagem, status=codigo_email)

                if codigo != 200:
                    return HttpResponse(mensagem, status=codigo)

                context = {
                    "voltar": True,
                    "usuario": user,
                    "area_principal": True,
                    "mensagem": mensagem,
                }
        else:
            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.</h3>",
            }

        return render(request, "generic.html", context=context)

    context = {
        "organizacoes": Organizacao.objects.all().order_by(Lower("nome")),
        "cursos": Curso.objects.all().order_by("id"),
        "PFEUser": PFEUser,
        "Professor": Professor,
        "Parceiro": Parceiro,
        "Estudante": Aluno,
    }

    # Passado o tipo e nome da organização do parceiro (se o caso) a ser cadastrado
    tipo = request.GET.get("tipo", None)
    if tipo:
        if tipo == "parceiro":
            organizacao_str = request.GET.get("organizacao", None)
            if organizacao_str:
                try:
                    organizacao_id = int(organizacao_str)
                    organizacao_selecionada = Organizacao.objects.get(id=organizacao_id)
                except (ValueError, Organizacao.DoesNotExist):
                    return HttpResponseNotFound("<h1>Organização não encontrado!</h1>")
                context["organizacao_selecionada"] = organizacao_selecionada

        elif tipo == "professor":
            pass
        elif tipo == "estudante":
            pass
        else:
            return HttpResponseNotFound("<h1>Tipo não reconhecido!</h1>")
        context["tipo"] = tipo
    
    proposta_id = request.GET.get("proposta", None)
    if proposta_id:
        proposta = get_object_or_404(Proposta, id=proposta_id)
        mensagem = ""
        if proposta.contatos_tecnicos:
            mensagem += "<b>Contatos Técnicos apresentados na Propota: " + str(proposta.id) + "</b><br>"
            mensagem += proposta.contatos_tecnicos
            mensagem += "<br>"
        if proposta.contatos_administrativos:
            mensagem += "<b>Contatos Administrativos apresentados na Propota: " + str(proposta.id) + "</b><br>"
            mensagem += proposta.contatos_administrativos
            mensagem += "<br>"

        context["mensagem_aviso"] = {"pt": mensagem, "en": mensagem}

    context["titulo"] = {"pt": "Cadastro de Usuário", "en": "User Registration"}

    return render(request, "administracao/cadastra_usuario.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_usuario(request, primarykey):
    """Edita cadastro de usuário na base de dados."""
    user = get_object_or_404(PFEUser, id=primarykey)

    if request.method == "POST":

        if "email" in request.POST:
            mensagem, codigo, _ = registro_usuario(request, user)

            if user is not None and "envia" in request.POST:
                    mensagem_email, codigo_email = envia_senha_mensagem(user)
                    mensagem += mensagem_email
                    if codigo_email != 200:
                        return HttpResponse(mensagem, status=codigo_email)

            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

        else:
            mensagem = "<h3 style='color:red'>Falha na inserção na base da dados.<h3>"

        context = {
            "voltar": True,
            "cadastrar_usuario": True,
            "area_principal": True,
            "mensagem": mensagem,
        }

        return render(request, "generic.html", context=context)


    context = {
        "usuario": user,
        "organizacoes": Organizacao.objects.all().order_by(Lower("nome")),
        "cursos": Curso.objects.all().order_by("id"),
        "PFEUser": PFEUser,
        "Professor": Professor,
        "Parceiro": Parceiro,
        "Estudante": Aluno,
    }

    if user.eh_estud:
        context["tipo"] = "estudante"
    elif user.eh_prof:
        context["tipo"] = "professor"
    elif user.eh_parc:
        context["tipo"] = "parceiro"
        if user.parceiro.organizacao:
            context["organizacao_selecionada"] = user.parceiro.organizacao
    elif user.eh_admin:
        if not request.user.eh_admin:
            return HttpResponse("Edição de administrador bloqueada", status=401)
        else:
            context["tipo"] = "professor"  # a principio supondo que seja professor
    else:
        return HttpResponse("Erro com tipo de usuário", status=401)

    context["titulo"] = {"pt": "Edição de Usuário", "en": "Edit User"}

    return render(request, "administracao/cadastra_usuario.html", context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def carrega_arquivo(request, dado):
    """Faz o upload de arquivos CSV para o servidor."""

    resource = get_resource(dado)

    if resource is None:
        return HttpResponseNotFound("<h1>Tipo de dado não reconhecido!</h1>")

    # https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
    if request.method == "POST":

        dataset = tablib.Dataset()

        if "arquivo" in request.FILES:
            new_data = request.FILES["arquivo"].readlines()
            if ';' in str(new_data)[:32]:
                return HttpResponseNotFound("<h1>Arquivo de dados possui ponto e vírgula (;) !</h1>")
        else:
            return HttpResponseNotFound("<h1>Arquivo não reconhecido!</h1>")

        entradas = ""
        for i in new_data:
            texto = i.decode("utf-8")
            entradas += re.sub("[^A-Za-z0-9À-ÿ, \r\n@._]+", '', texto)  # Limpa caracteres especiais

        dataset.load(entradas, format="csv")
        dataset.insert_col(0, col=lambda row: None, header="id")

        result = resource.import_data(dataset, dry_run=True, raise_errors=True, before_import_kwargs={"dry_run": True})

        if result.has_errors():
            mensagem = "Erro ao carregar arquivo." + str(result)

            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }

            return render(request, "generic.html", context=context)

        resource.import_data(dataset, dry_run=False, collect_failed_rows=True, before_import_kwargs={"dry_run": False})  # importa os dados agora
        
        if hasattr(resource, "registros"):
            string_html = "<b>Importado ({0} registros novos): </b><br>".format(len(resource.registros["novos"]))
            for row_values in resource.registros["novos"]:
                string_html += str(row_values) + "<br>"
            string_html += "<br><br><b>Atualizando ({0} registros): </b><br>".format(len(resource.registros["atualizados"]))
            for row_values in resource.registros["atualizados"]:
                string_html += str(row_values) + "<br>"
        else:
            string_html = "Importado ({0} registros): <br>".format(len(dataset))
            for row_values in dataset:
                string_html += str(row_values) + "<br>"
        
        acerta_nomes = reverse("nomes")
        string_html += f"<br><br>Para acertar Maiúsculas e Mínúsculas <a href='{acerta_nomes}'>clique aqui</a>"

        context = {
            "area_principal": True,
            "mensagem": string_html,
        }

        return render(request, "generic.html", context=context)

    context = {
        "titulo": {"pt": "Carregamento de CSV (Comma Separated Values)", "en": "CSV Upload"},
        "campos_permitidos": resource.campos,
    }

    return render(request, "administracao/import.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def configurar(request):
    """Definir datas."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == "POST":

        if "periodo_ano" and "periodo_semestre" in request.POST:
            try:
                
                configuracao.ano = int(request.POST["periodo_ano"])
                configuracao.semestre = int(request.POST["periodo_semestre"])
                configuracao.prazo_avaliar = int(request.POST["prazo_avaliar"])
                configuracao.prazo_preencher_banca = int(request.POST["prazo_preencher_banca"])

                configuracao.coordenacao = get_object_or_404(Administrador,
                                                             pk=int(request.POST["coordenacao"]))

                configuracao.coordenacao.nome_para_certificados = request.POST["nome_para_certificados"]
                if "assinatura" in request.FILES:
                    assinatura = simple_upload(request.FILES["assinatura"],
                                                path=get_upload_path(configuracao, ""))
                    configuracao.coordenacao.assinatura = assinatura[len(settings.MEDIA_URL):]

                configuracao.operacao = get_object_or_404(PFEUser,
                                                             pk=int(request.POST["operacao"]))

                configuracao.coordenacao.save()
                configuracao.save()
                context = {
                    "area_principal": True,
                    "mensagem": "Dados atualizados.",
                }
                return render(request, "generic.html", context=context)
            except (ValueError, OverflowError, MultiValueDictKeyError):
                return HttpResponse("Algum erro não identificado.", status=401)
        else:
            return HttpResponse("Algum erro ao passar parâmetros.", status=401)
    

    # PFEUsers Admin e que são parceiros do próprio Insper
    organizacao = Organizacao.objects.get(nome="Insper")
    funcionarios_insper = PFEUser.objects.filter(parceiro__organizacao=organizacao)
    operacionalizadores = PFEUser.objects.filter(tipo_de_usuario=4) | funcionarios_insper

    context = {
        "titulo": {"pt": "Configuração do Sistema", "en": "System Configuration"},
        "configuracao": configuracao,
        "administradores": Administrador.objects.all(),
        "administrador": Administrador,
        "operacionalizadores": operacionalizadores,
    }

    return render(request, "administracao/configurar.html", context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def desbloquear_usuarios(request):
    """Desbloqueia todos os usuários."""
    usuario_sem_acesso(request, (4,)) # Soh Admin
    axes.utils.reset()
    return redirect("/administracao/bloqueados/")


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def exportar(request):
    """Exporta dados."""

    if request.method == "POST" and request.user.eh_admin:
        if "edicao" in request.POST and "dados" in request.POST and "formato" in request.POST:
            ano, semestre = map(int, request.POST["edicao"].split('.'))
        else:
            return HttpResponse("Erro")

        formato = request.POST["formato"].lower()
        databook = tablib.Databook()
        modelo = None
        for dado in request.POST.getlist("dados"):
            if modelo is None:
                modelo = dado
            else:
                modelo += "_" + dado

            resource = get_resource(dado)
            queryset = get_queryset(resource, dado, ano, semestre)

            if resource is None or queryset is None:
                mensagem = "Chamada irregular: Base de dados desconhecida = " + modelo
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, "generic.html", context=context)

            dataset = resource.export(queryset)
            dataset.title = dado
            databook.add_sheet(dataset)
        
        if formato in ("xls", "xlsx"):
            formato = "xlsx"
            response = HttpResponse(databook.export("xlsx"), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif formato == "json":
            response = HttpResponse(dataset.export("json"), content_type="application/json")
        elif formato == "csv":
            response = HttpResponse(dataset.export("csv"), content_type="text/csv")
        else:
            return HttpResponse("Erro")
        response["Content-Disposition"] = 'attachment; filename="'+modelo+'.'+formato+'"'
        return response

    dados = [
        ("Projetos", "projetos" ),
        ("Organizações", "organizacoes"),
        ("Opções", "opcoes"),
        ("Avaliações", "avaliacoes"),
        ("Usuários", "usuarios"),
        ("Estudantes", "estudantes"),
        ("Professores", "professores"),
        ("Parceiros", "parceiros"),
        ("Configuração", "configuracao"),
        ("Feedbacks", "feedbacks"),
        ("Alocações", "alocacoes"),
        ("Avaliação de Pares", "pares"),
    ]

    context = {
        "titulo": {"pt": "Exportar Dados", "en": "Export Data"},
        "dados": dados,
        "edicoes": get_edicoes(Aluno)[0],
      }
    return render(request, "administracao/exportar.html", context=context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def relatorios(request):
    """gera relatorio dos dados."""

    relatorios = [
        ("Propostas Completas", "propostas"),
        ("Propostas Simples", "propostas_s"),
        ("Projetos", "projetos"),
        ("Estudantes", "estudantes"),
        ("Feedbacks", "feedbacks"),
        ("Avaliação de Pares", "pares"),
        ("Códigos Conduta Projetos", "codigo_conduta_proj"),
    ]

    context = {
        "titulo": {"pt": "Gera Relatórios", "en": "Reports"},
        "relatorios": relatorios,
        "edicoes": get_edicoes(Aluno)[0],
      }
    return render(request, "administracao/relatorios.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def propor(request):
    """Monta grupos."""

    if request.is_ajax():
        otimizar = True

        configuracao = get_object_or_404(Configuracao)
        ano = configuracao.ano
        semestre = configuracao.semestre
        ano, semestre = adianta_semestre(ano, semestre)

        propostas = ordena_propostas(otimizar, ano, semestre)

        alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
            filter(ano=ano, semestre=semestre, trancado=False).\
            order_by(Lower("user__first_name"), Lower("user__last_name"))
        
        # Calcula média dos CRs
        media_cr = 0
        for aluno in alunos:
            media_cr += aluno.cr
        media_cr /= len(alunos)

        # checa para empresas repetidas, para colocar um número para cada uma
        repetidas = {}
        for proposta in propostas:
            if proposta.organizacao:
                if proposta.organizacao.sigla in repetidas:
                    repetidas[proposta.organizacao.sigla] += 1
                else:
                    repetidas[proposta.organizacao.sigla] = 0
            else:
                if proposta.nome_organizacao in repetidas:
                    repetidas[proposta.nome_organizacao] += 1
                else:
                    repetidas[proposta.nome_organizacao] = 0
        repetidas_limpa = {}
        for repetida in repetidas:
            if repetidas[repetida] != 0:  # tira zerados
                repetidas_limpa[repetida] = repetidas[repetida]
        proposta_indice = {}
        for proposta in reversed(propostas):
            if proposta.organizacao:
                if proposta.organizacao.sigla in repetidas_limpa:
                    proposta_indice[proposta.id] = \
                        repetidas_limpa[proposta.organizacao.sigla] + 1
                    repetidas_limpa[proposta.organizacao.sigla] -= 1
            else:
                if proposta.nome_organizacao in repetidas_limpa:
                    proposta_indice[proposta.id] = \
                        repetidas_limpa[proposta.nome_organizacao] + 1
                    repetidas_limpa[proposta.nome_organizacao] -= 1

        def pega_opcoes(alunos, propostas):
            opcoes = []
            for aluno in alunos:
                opcoes_aluno = []
                for proposta in propostas:
                    opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                    if opcao:
                        opcoes_aluno.append(opcao)
                    else:
                        opcoes_aluno.append(None)
                opcoes.append(opcoes_aluno)
            return opcoes

        opcoes = pega_opcoes(alunos, propostas)

        def calcula_qtd(opcoes, propostas, alunos):
            finish = True
            qtd = []
            for count, proposta in enumerate(propostas):
                tmp = 0
                for linha in range(len(alunos)):
                    pre = alunos[linha].pre_alocacao
                    if pre:
                        if pre == proposta:
                            tmp += 1
                    else:
                        optmp = Opcao.objects.filter(aluno=alunos[linha], prioridade=1).last()
                        if optmp and optmp.proposta == proposta:
                            tmp += 1
                # Somente grupos de 3 ou 4 ou proposta sem ninguem
                if tmp != 4 or tmp != 3 or tmp != 0:
                    finish = False
                qtd.append(tmp)
            return qtd, finish

        qtd, finish = calcula_qtd(opcoes, propostas, alunos)

        user = request.user
        if otimizar:  # Quer dizer que é um POST
            if not user.eh_admin:  # admin
                return HttpResponse("Usuário sem privilégios de administrador.", status=403)

            ordem_propostas = {}
            contador = 0
            for proposta in propostas:
                ordem_propostas[proposta.id] = contador
                contador += 1

            # Removendo propostas com menos de 3 estudantes (prioridade <= 5)
            soma = []
            for count, proposta in enumerate(propostas):
                tmp = 0
                for linha in range(len(alunos)):
                    opcao = opcoes[linha][count] 
                    if opcao and opcao.prioridade <= 5:
                        tmp += 1
                soma.append(tmp)
            idx = None
            for count, proposta in enumerate(propostas):
                if soma[count] < 3:
                    idx = count
                    break
            propostas = propostas[:idx]
            for linha in range(len(alunos)):
                opcoes[linha] = opcoes[linha][:idx] 
            soma = soma[:idx]
        
            # Se estudante foi e voltou em um grupo, não mudar mais
            pula_estudante = {}

            # Pre alocando todos nas suas primeiras opções
            for aluno in alunos:
                tmp_prioridade = 9999
                tmp_proposta = None
                for proposta in propostas:
                    opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                    if opcao and opcao.prioridade < tmp_prioridade:
                        tmp_proposta = proposta
                        tmp_prioridade = opcao.prioridade
                if tmp_prioridade < 9999:
                    aluno.pre_alocacao = tmp_proposta
                    aluno.save()
                else:
                    pula_estudante[aluno]=0  # Todas as opções de {aluno} são inviáveis.

            reduz = 1
            contador = 0
            while not finish:
                
                trocou = False

                for count, proposta in enumerate(propostas):
                    if qtd[count] == reduz:
                        troca = None
                        for linha in range(len(alunos)):
                            opcao = opcoes[linha][count]
                            if opcao and (opcao.prioridade <= 10) and (opcao.aluno.pre_alocacao != proposta):
                                op_qtd = qtd[ordem_propostas[opcao.aluno.pre_alocacao.id]]
                                if (opcao.aluno not in pula_estudante) or (opcao.prioridade < pula_estudante[opcao.aluno]):
                                    if (3 > op_qtd) or (4 < op_qtd):
                                        if (not troca):
                                            troca = opcao
                                        elif (opcao.prioridade < troca.prioridade):
                                            troca = opcao
                                        elif (opcao.prioridade == troca.prioridade) and (opcao.aluno.cr < troca.aluno.cr):
                                            troca = opcao
                        if troca:
                            trocou = True
                            aluno = Aluno.objects.get(pk=troca.aluno.pk)
                            antiga_opcao = Opcao.objects.filter(aluno=aluno, proposta=aluno.pre_alocacao).last()
                            if troca.prioridade < antiga_opcao.prioridade:
                                pula_estudante[aluno]=troca.prioridade
                            Aluno.objects.filter(pk=troca.aluno.pk).update(pre_alocacao=troca.proposta)
                            reduz = 1 # Volta a busca do começo sempre que há alguma troca
                            break

                alunos = Aluno.objects.filter(ano=ano, semestre=semestre, trancado=False).\
                    order_by(Lower("user__first_name"), Lower("user__last_name"))

                opcoes = pega_opcoes(alunos, propostas)
                qtd, finish = calcula_qtd(opcoes, propostas, alunos)

                if not trocou:
                    reduz += 1
                    if reduz == 4:
                        break

                # Para evitar travar totalmente
                contador += 1
                if contador > 50:
                    #"ESTOUROU"
                    break

        return JsonResponse({"atualizado": True,})

    return HttpResponseNotFound("Requisição errada")


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def montar_grupos(request):
    """Montar grupos para projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    ano, semestre = adianta_semestre(ano, semestre)

    propostas = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)

    estudantes = Aluno.objects.filter(trancado=False, ano=ano, semestre=semestre).\
        order_by(Lower("user__first_name"), Lower("user__last_name"))

    opcoes = []
    opcoes_periodo = Opcao.objects.filter(proposta__ano=ano, proposta__semestre=semestre).order_by("prioridade")
    for estudante in estudantes:
        opcao = opcoes_periodo.filter(aluno=estudante)
        opcoes.append(opcao)
        
        # Caso haja um pré-alocação de anos anteriores, limpar a pré-alocação
        if estudante.pre_alocacao and estudante.pre_alocacao not in propostas:
            estudante.pre_alocacao = None
            estudante.save()

    estudantes_opcoes = zip(estudantes, opcoes)

    # Checa se usuário é administrador ou professor
    user = request.user

    mensagem = ""

    if request.method == "POST" and user and request.user.tipo_de_usuario == 4:  # admin

        if "limpar" in request.POST:
            for estudante in estudantes:
                estudante.pre_alocacao = None
                estudante.save()

        if "fechar" in request.POST:
            for proposta in propostas:
                alocados = []
                for estudante in estudantes:
                    if estudante.pre_alocacao:
                        if estudante.pre_alocacao.id == proposta.id:
                            alocados.append(estudante)
                    else:
                        op_aloc = Opcao.objects.filter(aluno=estudante).\
                                    filter(proposta__ano=ano, proposta__semestre=semestre).\
                                    filter(prioridade=1).first()
                        if op_aloc and op_aloc.proposta == proposta:
                            alocados.append(estudante)
                if alocados:  # pelo menos um estudante no projeto
                    try:
                        projeto = Projeto.objects.get(proposta=proposta, avancado=None)
                    except Projeto.DoesNotExist:
                        projeto = Projeto(proposta=proposta)

                    if not projeto.organizacao:
                        projeto.organizacao = proposta.organizacao

                    projeto.ano = proposta.ano
                    projeto.semestre = proposta.semestre

                    projeto.save()

                    alocacoes = Alocacao.objects.filter(projeto=projeto)
                    for alocacao in alocacoes:  # Apaga todas alocacoes que não tiverem nota
                        avals = list(Avaliacao2.objects.filter(alocacao=alocacao))
                        if not avals:
                            alocacao.delete()
                        else:
                            mensagem += "- "+str(alocacao.aluno)+"\n"

                    for estudante in alocados:  # alocando estudantes no projeto
                        alocacao = Alocacao(projeto=projeto, aluno=estudante)
                        alocacao.save()

                else:
                    projetos = Projeto.objects.filter(proposta=proposta, avancado=None)
                    if not projetos:
                        continue

                    for projeto in projetos:
                        alocacoes = Alocacao.objects.filter(projeto=projeto)
                        for alocacao in alocacoes:  # Apaga todas alocacoes que não tiverem nota
                            alocacao.delete()

                        projeto.delete()

            if mensagem:
                request.session["mensagem"] = "Estudantes possuiam alocações com notas:\n" + mensagem

            return redirect("/administracao/selecionar_orientadores/")

    if user and user.tipo_de_usuario != 4:  # admin
        mensagem = "Sua conta não é de administrador, "
        mensagem += "você pode mexer na tela, contudo suas modificações não serão salvas."

    context = {
        "titulo": { "pt": "Planejamento de Grupos por Proposta", "en": "Planning Groups by Proposal" },
        "mensagem_aviso": {"pt": mensagem, "en": mensagem},
        "configuracao": configuracao,
        "propostas": propostas,
        "estudantes_opcoes": estudantes_opcoes,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"), 
    }

    return render(request, "administracao/montar_grupos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def selecionar_orientadores(request):
    """Selecionar Orientadores para os Projetos."""

    mensagem = request.session["mensagem"] if "mensagem" in request.session else ""
    if request.user.tipo_de_usuario != 4:  # Checa se usuário é administrador
        mensagem += "Sua conta não é de administrador, você pode mexer na tela, contudo suas modificações não serão salvas."

    ano, semestre = adianta_semestre_conf(get_object_or_404(Configuracao))

    context = {
        "titulo": { "pt": "Selecionar Orientadores para os Projetos", "en": "Select Advisors for Projects" },
        "mensagem_aviso": {"pt": mensagem, "en": mensagem},
        "projetos": Projeto.objects.filter(ano=ano, semestre=semestre),
        "orientadores": PFEUser.objects.filter(tipo_de_usuario__in=[2, 4])  #2prof 4adm,
    }

    return render(request, "administracao/selecionar_orientadores.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def fechar_conexoes(request):
    """Fechar conexões com Organizações."""
    
    mensagem = request.session["mensagem"] if "mensagem" in request.session else ""
    if request.user.tipo_de_usuario != 4:  # Checa se usuário é administrador
        mensagem += "Sua conta não é de administrador, você pode mexer na tela, contudo suas modificações não serão salvas."

    ano, semestre = adianta_semestre_conf(get_object_or_404(Configuracao))

    context = {
        "titulo": { "pt": "Fechar Conexões com Organizações", "en": "Close Connections with Organizations" },
        "mensagem_aviso": {"pt": mensagem, "en": mensagem},
        "projetos": Projeto.objects.filter(ano=ano, semestre=semestre),
    }

    return render(request, "administracao/fechar_conexoes.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def servico(request):
    """Caso servidor esteja em manutenção."""
    if request.method == "POST":
        check_values = request.POST.getlist("selection")
        settings.MAINTENANCE_MODE = 1 if "manutencao" in check_values else 0
        return redirect("/administracao")
    context = {
        "titulo": { "pt": "Manutenção do Servidor", "en": "Server Maintenance" },
        "manutencao": settings.MAINTENANCE_MODE,
        }
    return render(request, "administracao/servico.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def pre_alocar_estudante(request):
    """Ajax para pre-alocar estudates em propostas."""
    if request.user.tipo_de_usuario == 4:  # admin

        estudante = request.GET.get("estudante", None)
        estudante_id = int(estudante[len("estudante"):])
        estudante = get_object_or_404(Aluno, id=estudante_id)

        proposta = request.GET.get("proposta", None)
        proposta_id = int(proposta[len("proposta"):])
        proposta = get_object_or_404(Proposta, id=proposta_id)

        estudante.pre_alocacao = proposta
        estudante.save()

    elif request.user.tipo_de_usuario == 2:  # professor
        # atualizações não serão salvas
        pass

    else:
        return HttpResponseNotFound("<h1>Usuário sem privilérios!</h1>")

    return JsonResponse({"atualizado": False,})


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def estrela_estudante(request):
    """Ajax para informar que alocação de estudate pode ter algum ponto de observação."""
    if request.user.tipo_de_usuario == 4:  # admin

        estudante_id = request.GET.get("estudante", None)
        estudante = get_object_or_404(Aluno, id=estudante_id)

        estado = request.GET.get("estado", "false") == "true"
        estudante.estrela = estado
        estudante.save()

    elif request.user.tipo_de_usuario == 2:  # professor
        # atualizações não serão salvas
        pass

    else:
        return HttpResponseNotFound("<h1>Usuário sem privilérios!</h1>")

    return JsonResponse({"atualizado": False,})


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def definir_orientador(request):
    """Ajax para definir orientadores de projetos."""
    
    if request.user.tipo_de_usuario == 4:  # admin
        # Código só se usuário é administrador

        orientador_get = request.POST.get("orientador", None)
        orientador_id = int(orientador_get[len("orientador"):]) if orientador_get else None
        orientador = get_object_or_404(Professor, user_id=orientador_id) if orientador_id else None

        projeto_get = request.POST.get("projeto", None)        
        projeto_id = int(projeto_get[len("projeto"):]) if projeto_get else None
        projeto = get_object_or_404(Projeto, id=projeto_id)

        projeto.orientador = orientador
        projeto.save()

    elif request.user.tipo_de_usuario == 2:  # professor
        pass

    else:
        return HttpResponseNotFound("<h1>Usuário sem privilérios!</h1>")

    return JsonResponse({"atualizado": True,})


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def excluir_disciplina(request):
    """Remove Disciplina Recomendada."""
    
    if request.is_ajax() and "disciplina_id" in request.POST:
        disciplina_id = int(request.POST["disciplina_id"])
        instance = Disciplina.objects.get(id=disciplina_id)
        instance.delete()

        return JsonResponse({"atualizado": True})

    return HttpResponseNotFound("Requisição errada")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def export(request, modelo, formato):
    """Exporta dados direto para o navegador nos formatos CSV, XLS e JSON."""
    # APOSENTAR ESSE MÉTODO
    # NÃO USAR MAIS

    resource = get_resource(modelo)

    if resource is None:
        mensagem = "Chamada irregular: Base de dados desconhecida = " + modelo
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    dataset = resource.export()
    databook = tablib.Databook()
    databook.add_sheet(dataset)
    if formato in ("xls", "xlsx"):
        response = HttpResponse(databook.xlsx, content_type="application/ms-excel")
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(dataset.json, content_type="application/json")
    elif formato == "csv":
        response = HttpResponse(dataset.csv, content_type="text/csv")
    else:
        mensagem = "Chamada irregular : Formato desconhecido = " + formato
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    response["Content-Disposition"] = 'attachment; filename="'+modelo+'.'+formato+'"'

    return response


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def backup(request, formato):
    """Gera um backup de tudo."""
    databook = create_backup()
    if formato in ("xls", "xlsx"):
        response = HttpResponse(databook.xlsx, content_type="application/ms-excel")
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(databook.json, content_type="application/json")
    else:
        mensagem = "Chamada irregular : Formato desconhecido = " + formato
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    response["Content-Disposition"] = 'attachment; filename="backup.'+formato+'"'

    return response


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relatorio(request, modelo, formato):
    """Gera relatorios em html e PDF."""
    configuracao = get_object_or_404(Configuracao)
    context = {"titulo": {"pt": "Relatório", "en": "Report"},}

    edicao = request.GET.get("edicao", None)
    if edicao and edicao != "todas":
        ano, semestre = map(int, edicao.split('.'))
    else:
        edicao = None
   
    if modelo == "propostas":
        if edicao:
            context["propostas"] = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)
        else:
            context["propostas"] = Proposta.objects.all(disponivel=True)
        arquivo = "administracao/relatorio_propostas.html"

    if modelo == "propostas_s":
        if edicao:
            context["propostas"] = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)
        else:
            context["propostas"] = Proposta.objects.all(disponivel=True)
        arquivo = "administracao/relatorio_propostas_simples.html"

    elif modelo == "projetos":
        if edicao:
            context["projetos"] = Projeto.objects.filter(ano=ano, semestre=semestre)
        else:
            context["projetos"] = Projeto.objects.all()
        arquivo = "administracao/relatorio_projetos.html"

    elif modelo == "estudantes" or modelo == "alunos":
        if edicao:
            context["alunos"] = Aluno.objects.filter(ano=ano, semestre=semestre)
        else:
            context["alunos"] = Aluno.objects.all()
        arquivo = "administracao/relatorio_alunos.html"

    elif modelo == "feedbacks":
        context["feedbacks"] = Feedback.objects.all()
        arquivo = "administracao/relatorio_feedbacks.html"

    elif modelo == "pares":
        if edicao:
            projetos = Projeto.objects.filter(ano=ano, semestre=semestre)
        else:
            projetos = Projeto.objects.all()

        colegas = []
        for projeto in projetos:
            colegas.append(get_pares_colegas(projeto))

        context["proj_pares"] = zip(projetos, colegas)
        
        context["entregas"] = [resposta[1] for resposta in Pares.TIPO_ENTREGA]
        context["iniciativas"] = [resposta[1] for resposta in Pares.TIPO_INICIATIVA]
        context["comunicacoes"] = [resposta[1] for resposta in Pares.TIPO_COMUNICACAO]
        arquivo = "administracao/relatorio_pares.html"

    elif modelo == "codigo_conduta_proj":
        context["perguntas_codigo_conduta"] = Estrutura.loads(nome="Código de Conduta do Grupo")
        codigo_condutas = CodigoConduta.objects.filter(content_type=ContentType.objects.get_for_model(Projeto))
        respostas_condutas = []
        for codigo_conduta in codigo_condutas:
            r = json.loads(codigo_conduta.codigo_conduta)
            r["projeto"] = Projeto.objects.get(id=codigo_conduta.object_id)
            respostas_condutas.append(r)
        context["respostas_condutas"] = respostas_condutas
        arquivo = "administracao/relatorio_codigo_conduta_proj.html"

    else:
        context = {
            "area_principal": True,
            "mensagem": "Chamada irregular: Base de dados desconhecida = " + modelo,
        }
        return render(request, "generic.html", context=context)

    if formato in ("html", "HTML"):
        return render(request, arquivo, context)

    if formato in ("pdf", "PDF"):
        pdf = render_to_pdf(arquivo, context)
        return HttpResponse(pdf.getvalue(), content_type="application/pdf")

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def logs(request, dias=30):
    """Alguns logs de Admin."""
    usuario_sem_acesso(request, (4,)) # Soh Adm

    thirty_days_ago = timezone.now() - datetime.timedelta(days=dias)
    message = "As seguintes alterações foram realizadas pela interface de administrador:<br>"
    message += "(mostrando os últimos " + str(dias) + " dias)<br><br>"
    #for log in LogEntry.objects.all():
    for log in LogEntry.objects.filter(action_time__gte=thirty_days_ago):
        message += "&bull; " + str(log.user) + " [" + str(log.action_time) + "]: " + str(log)+"<br>\n"

    message += "<br><a href=' " + str(dias+30) + "'>Mostrar último " + str(dias+30) + " dias</a>"
    
    return HttpResponse(message)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def tarefas_agendadas(request):
    """Alguns logs de Admin."""
    usuario_sem_acesso(request, (4,)) # Soh Adm
    i = celery_app.control.inspect()
    scheduled_tasks = i.scheduled()

    agora = datetime.datetime.now()
    context = {
        "titulo": { "pt": "Tarefas Agendadas", "en": "Scheduled Tasks" },
        "agora": agora,
        "scheduled_tasks": scheduled_tasks,
    }
    return render(request, "administracao/tarefas_agendadas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_git(request):
    """Lista todos os repositórios do GitHub na conta do PFE/Capstone."""
    if request.method == "POST":
        for projeto in Projeto.objects.all():
            backup_github(projeto)
        context = {
            "voltar": True,
            "area_principal": True,
            "mensagem": "<h3 style='color:red'>Backup realizado.<h3>",
        }
        return render(request, "generic.html", context=context)

    #REPOS_URL = f"https://api.github.com/orgs/pfeinsper/repos"
    headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
    repositorios = {}
    for projeto in Projeto.objects.all():
        gits = puxa_github(projeto)
        for git_url in gits:
            repo_name = git_url.split('/')[-1].replace(".git", "")
            repo_owner = git_url.split('/')[-2]
            if repo_owner and repo_name:
                repo_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
                response = requests.get(repo_api_url, headers=headers)
                repos = response.json()
                repo_dict = {}
                for chave, valor in repos.items():
                    if chave == "created_at" or chave == "updated_at" or chave == "pushed_at":
                        repo_dict[chave] = datetime.datetime.strptime(valor, "%Y-%m-%dT%H:%M:%SZ")
                    else:
                        repo_dict[chave] = valor
                repositorios[projeto] = repo_dict

    context = {
        "titulo": { "pt": "Lista Repositórios do GitHub", "en": "GitHub Repositories List" },
        "repositorios": repositorios,
    }
    
    return render(request, "administracao/lista_git.html", context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def versoes_sistema(request):
    """Mostra versões do sistema."""

    versoes = {}
    versoes["Python"] = sys.version  # Retrieve Python version
    versoes["Django"] = django.get_version()  # Retrieve Django version
    versoes["Celery"] = celery.__version__  # Retrieve Celery version
    
    # Retrieve PostgreSQL version
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        versoes["Postgres"] = cursor.fetchone()[0]

    pacotes = {dist.project_name: dist.version for dist in pkg_resources.working_set}
    pacotes = dict(sorted(pacotes.items()))

    # show the environment that the server is running on
    versoes["Usuário"] = os.environ.get("USER", "Não definido")
    versoes["Diretório base"] = os.environ.get("PWD", "Não definido")
    
    # Get the virtual environment name
    venv_path = sys.prefix
    venv_name = os.path.basename(venv_path)
    versoes["Virtual Environment"] = venv_name

    if os.environ.get('RUN_MAIN') == 'true':
        versoes["Execution Context"] = "Django Development Server (manage.py runserver)"
    elif os.environ.get('mod_wsgi.process_group'):
        versoes["Execution Context"] = "Apache with mod_wsgi"
    

    context = {
        "titulo": { "pt": "Versões do Sistema", "en": "System Versions" },
        "versoes": versoes,
        "pacotes": pacotes,
    }
    return render(request, "administracao/versoes_sistema.html", context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def cancela_tarefa(request, task_id):
    if request.method == "POST":
        celery_app.control.revoke(task_id, terminate=True)
    return redirect("/administracao/tarefas_agendadas")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def conexoes_estabelecidas(request):
    """Mostra usuários conectados."""
    usuario_sem_acesso(request, (4,))  # Soh Adm
    
    mensagem = ""
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    usuarios = []
    for session in sessions:
        data = session.get_decoded()
        user_id = data.get("_auth_user_id", None)
        if user_id:
            try:
                user = PFEUser.objects.get(id=user_id)
                usuario = {
                    "usuario": user,
                    "autenticado": user.is_authenticated,
                    "desde": user.last_login,
                    "expire_date": session.expire_date,
                    "permissoes": str(user.get_all_permissions())[:120],
                }
                usuarios.append(usuario)
            except PFEUser.DoesNotExist:
                mensagem += f"User ID {user_id} não identificado.<br>\n"
            except Exception as e:
                mensagem += f"Erro ao processar User ID {user_id}: {str(e)}<br>\n"
        else:
            mensagem += "Sessão sem User ID.<br>\n"

    context = {
        "titulo": {"pt": "Conexões Estabelecidas", "en": "Established Connections"},
        "mensagem_aviso": {"pt": mensagem, "en": mensagem},
        "usuarios": usuarios,
    }

    return render(request, "administracao/conexoes_estabelecidas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bloqueados(request):
    """Mostra usuários e ips bloqueados."""
    if request.user.tipo_de_usuario != 4:
        return HttpResponse("Você não tem privilégios")

    mes_atras = timezone.now() - datetime.timedelta(days=30)
    
    context = {
        "titulo": { "pt": "Usuários e IPs", "en": "Users and IPs" },
        "access_logs": AccessLog.objects.all().filter(attempt_time__gte=mes_atras),
        "access_attempts": AccessAttempt.objects.all(),
    }
    return render(request, "administracao/bloqueados.html", context=context)

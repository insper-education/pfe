#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 29 de Dezembro de 2020
"""

import datetime
import dateutil.parser
import logging
import json

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, get_object_or_404
from django.template import TemplateSyntaxError
from django.urls import reverse

from .support import trata_aviso

from academica.models import Composicao
from academica.support5 import filtra_composicoes

from administracao.models import TipoCertificado, TipoEvento

from documentos.models import TipoDocumento

from projetos.models import Aviso, Certificado, Evento, Configuracao, Pedido
from projetos.models import Projeto, Banca, Conexao
from projetos.messages import email
from projetos.tipos import TIPO_EVENTO
from projetos.support import get_upload_path, simple_upload
from projetos.support5 import envia_mensagens_avisos

from users.models import PFEUser, Aluno, Professor, Parceiro, Alocacao
from users.support import get_edicoes


logger = logging.getLogger("django")  # Get an instance of a logger


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
                 "data": evento.get_data(final=aviso.delta_fim) + datetime.timedelta(days=aviso.delta),
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
        {"pt": "Data do Aviso/Lembrete", "en": "Notice/Reminder Date"},
        {"pt": "Ponto de Referência", "en": "Reference Point"},
        {"pt": "Público", "en": "Target"},
        {"pt": "Título", "en": "Title"},
    ]

    captions = [ [
          {"sigla": "Co", "pt": "Coordenação", "en": "Coordination"},
          {"sigla": "Op", "pt": "Equipe Operacional", "en": "Operational Team"},
          {"sigla": "Cm", "pt": "Comitê Capstone", "en": "Capstone Committee"},
          {"sigla": "Es", "pt": "Estudantes", "en": "Students"},
          {"sigla": "Or", "pt": "Orientadores", "en": "Advisors"},
          {"sigla": "Og", "pt": "Contatos nas Organizações", "en": "Contacts in Organizations"},
    ] ]

    
    try:
        aviso_id = int(request.GET.get("aviso"))
        if aviso_id <= 0:
            aviso_id = None
    except (TypeError, ValueError):
        aviso_id = None
    
    context = {
        "titulo": { "pt": "Agenda de Avisos Automáticos", "en": "Automatic Notices Agenda" },
        "avisos": avisos,
        "hoje" : datetime.date.today(),
        "filtro" : "todos",
        "cabecalhos": cabecalhos,
        "captions": captions,
        "aviso": aviso_id,
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
    if request.method == "POST" and "edicao" in request.POST:
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

        # Estudantes do semestre, mas que não estão alocados
        estudantesNaoAlocados = Aluno.objects.filter(ano=ano, semestre=semestre).exclude(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre).select_related("user")
        data["EstudantesNaoAlocados"] = list(estudantesNaoAlocados.values_list("user__first_name", "user__last_name", "user__email"))

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
    if request.method == "POST" and "edicao" in request.POST:
        ano, semestre = request.POST["edicao"].split('.')
        context = {"projetos": Projeto.objects.filter(ano=ano).filter(semestre=semestre),}
        return render(request, "operacional/emails_projetos.html", context=context)
    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_aviso(request, primarykey=None):
    """Edita aviso."""
    aviso = get_object_or_404(Aviso, pk=primarykey) if primarykey else None

    if request.method == "POST":
        if "mensagem" in request.POST:
            if primarykey is None:
                aviso = Aviso()
            try:
                aviso = trata_aviso(aviso, request)
            except (ValueError, OverflowError):
                return HttpResponse("Algum erro não identificado.", status=401)
            aviso.save()

            if "acao" in request.POST and request.POST["acao"] == "teste":
                try:
                    envia_mensagens_avisos(aviso_id=aviso.id if aviso else None, endereco=request.user.email)
                except TemplateSyntaxError:
                    logger.exception("Erro de sintaxe no template do aviso %s", aviso.id)
                    return HttpResponse("Erro de sintaxe no template do aviso. Verifique a mensagem e tente novamente.", status=400)

                context = {
                    "area_principal": True,
                    "mensagem": {"pt": "Mensagem enviada.", "en": "Message sent."},
                }
                return render(request, "generic_ml.html", context=context)

            # return redirect("avisos_listar")
        
            params = {"aviso": aviso.id}
            url = reverse("avisos_listar") + "?" + urlencode(params)
            return redirect(url)

        return HttpResponse("Problema com atualização de mensagem.", status=401)

    atributos = [field.name for field in Evento._meta.get_fields() if field.name != "id"]

    variaveis = {
        "hoje": { "pt": "Data do dia de envio do aviso", "en": "Date of the day of sending the notice" },
        "edicao": { "pt": "Edição do Capstone", "en": "Capstone edition" },
        "delta": { "pt": "Diferença de dias entre o envio do aviso e o aviso", "en": "Difference in days between the sending of the notice and the notice" },
        "delta_invert": { "pt": "Diferença de dias entre o evento e o envio do aviso (- delta)", "en": "Difference in days between the event and the sending of the notice (- delta)" },
        "delta_fim": { "pt": "Indica se o delta é em relação ao início(false) ou fim(true) do evento", "en": "Indicates whether the delta is in relation to the start(false) or end(true) of the event" },
        "orientadores": { "pt": "Professores orientadores do semestre", "en": "Advisors of the semester" },
        "estudantes": { "pt": "Estudantes do semestre (somente internos)", "en": "Students of the semester (only internal)" },
        "bancas": { "pt": "Próximas bancas", "en": "Next defenses" },
        "eventos": { 
            "pt": "Todos os eventos do semestre", "en": "All events of the semester",
            "exemplos": 'IA (Início das Aulas) = {{eventos|data_evento_sigla:"IA"}}, MA (Mentoria Acadêmica) = {{eventos|data_evento_sigla:"MA"}}',
            },
        "evento": { 
            "pt": "Evento relacionado", "en": "Related event",
            "atributos": atributos,
            },
    }

    filtros = {
        "dias": { "pt": "Adiciona/subtrai dias a uma data", "en": "Adds/subtracts days to a date" },
        "data_evento": { "pt": "Busca a data inicial de evento do semestre pelo nome", "en": "Search for the start date of the semester event by name" },
        "data_evento_sigla": { "pt": "Busca a data inicial de evento do semestre pela sigla", "en": "Search for the start date of the semester event by the acronym" },
        "data_final_evento": { "pt": "Busca a data final de evento do semestre pelo nome", "en": "Search for the end date of the semester event by name" },
        "data_final_evento_sigla": { "pt": "Busca a data final de evento do semestre pela sigla", "en": "Search for the end date of the semester event by the acronym" },
    }

    context = {
        "aviso": aviso,
        "eventos": TipoEvento.objects.all(),
        "variaveis": variaveis,
        "filtros": filtros,
        "tipos": TipoDocumento.objects.all(),
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

            mensagem = {"pt": "Certificado inserido na base de dados.", "en": "Certificate inserted in the database."}
            mensagem["pt"] += "<br><b>Usuário</b>: " + str(certificado.usuario)
            mensagem["en"] += "<br><b>User</b>: " + str(certificado.usuario)
            mensagem["pt"] += "<br><b>Projeto</b>: " + str(certificado.projeto)
            mensagem["en"] += "<br><b>Project</b>: " + str(certificado.projeto)
            mensagem["pt"] += "<br><b>Data</b>: " + str(certificado.data)
            mensagem["en"] += "<br><b>Date</b>: " + str(certificado.data)
            mensagem["pt"] += "<br><b>Tipo</b>: " + str(certificado.tipo_certificado.titulo)
            mensagem["en"] += "<br><b>Type</b>: " + str(certificado.tipo_certificado.titulo)
            if certificado.observacao:
                mensagem["pt"] += "<br><b>Observação</b>: " + str(certificado.observacao)
                mensagem["en"] += "<br><b>Observation</b>: " + str(certificado.observacao)
            
            mensagem["pt"] += "<br><b>Documento</b>: " + str(certificado.documento)
            mensagem["en"] += "<br><b>Document</b>: " + str(certificado.documento)

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": mensagem,
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem_erro": {"pt": "Falha na inserção na base da dados.", 
                                  "en": "Failed to insert in the database."},
            }

        return render(request, "generic_ml.html", context=context)

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
def deleta_aviso(request, primarykey):
    """Apaga aviso."""
    Aviso.objects.filter(id=primarykey).delete()
    return redirect('avisos_listar')


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def plano_aulas(request):
    """Gera tabela com aulas do semestre."""

    if request.method == "POST" and "edicao" in request.POST:
        ano, semestre = map(int, request.POST["edicao"].split('.'))
        context = {
            "aulas": Evento.get_eventos(nome="Aula", ano=ano, semestre=semestre),
            "composicoes": filtra_composicoes(Composicao.objects.all(), ano, semestre),
            }
        return render(request, "operacional/plano_aulas.html", context=context)
    
    context = {
        "titulo": { "pt": "Plano de Aulas", "en": "Class Schedule" },
        "edicoes": get_edicoes(Projeto)[0],
    }
    return render(request, "operacional/plano_aulas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def gerir_pedidos(request):
    """Gerencia pedidos feitos por estudantes, como pedidos de prorrogação, etc."""
    
    if request.method == "POST":
        configuracao = get_object_or_404(Configuracao)
        pedido_id = request.POST.get("pedido_id")
        acao = request.POST.get("acao")
        resposta = request.POST.get("resposta", "")

        pedido = get_object_or_404(Pedido, id=pedido_id)
        anotacao = ""

        if acao == "aprovar":
            pedido.status = "aprovado"
        elif acao == "reprovar":
            pedido.status = "reprovado"

        # Atualizar campos específicos do projeto quando aprovado
        projeto = pedido.projeto
        if projeto:
            if pedido.tipo == "github":
                url_time_github = request.POST.get("url_time_github", "").strip()
                if url_time_github:
                    projeto.url_time_github = url_time_github
                    anotacao += "URL do GitHub: " + url_time_github + "<br>"
                    
            elif pedido.tipo == "overleaf":
                url_latex = request.POST.get("url_latex", "").strip()
                if url_latex:
                    projeto.url_latex = url_latex
                    anotacao += "URL do Overleaf: " + url_latex + "<br>"

            elif pedido.tipo == "nuvem":
                conta_aws = request.POST.get("conta_aws", "").strip()
                if conta_aws:
                    projeto.conta_aws = conta_aws
                    anotacao += "Conta AWS: " + conta_aws + "<br>"
                    
            elif pedido.tipo == "llm":
                apontamento_llm = request.POST.get("apontamento_llm", "").strip()
                if apontamento_llm:
                    projeto.apontamento_llm = apontamento_llm
                    anotacao += "Apontamento LLM: " + apontamento_llm + "<br>"
                    
            elif pedido.tipo == "equipamento":
                lista_equipamentos = request.POST.get("lista_equipamentos", "").strip()
                if lista_equipamentos:
                    projeto.lista_equipamentos = lista_equipamentos
                    anotacao += "Lista de Equipamentos: " + lista_equipamentos + "<br>"
                        
            elif pedido.tipo == "compra":
                lista_compras = request.POST.get("lista_compras", "").strip()
                if lista_compras:
                    projeto.lista_compras = lista_compras
                    anotacao += "Lista de Compras: " + lista_compras + "<br>"
            
            projeto.save()
        
        pedido.resposta = resposta
        pedido.data_resposta = datetime.datetime.now()
        pedido.respondente = request.user
        pedido.save()

        email_subject = f"Resposta de Pedido de Recurso: {pedido.tipo.capitalize()} - Projeto {pedido.projeto.proposta.titulo}"
        email_recipients = [request.user.email]
        email_recipients += [configuracao.coordenacao.user.email]
        email_recipients += [pedido.projeto.orientador.user.email] if pedido.projeto.orientador else []
        for alocacao in Alocacao.objects.filter(projeto=pedido.projeto):
            email_recipients.append(alocacao.aluno.user.email)
        email_message = f"""
            {pedido.solicitante.get_full_name()},<br><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Seu pedido foi <b>{pedido.status}</b>.<br><br>
        """
        if resposta:
            email_message += f"&nbsp;&nbsp;&nbsp;&nbsp;Resposta:<br><div style='margin-left: 20px;'>{resposta}</div><br><br>"
        email_message += f"""
            &nbsp;&nbsp;&nbsp;&nbsp;Tipo: {pedido.tipo.capitalize()}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Projeto: {pedido.projeto.proposta.titulo}<br>
            &nbsp;&nbsp;&nbsp;&nbsp;Estudantes:<br>
            <div style="margin-left: 20px;">
        """
        for alocacao in Alocacao.objects.filter(projeto=pedido.projeto):
            email_message += f"&bull; {alocacao.aluno.user.get_full_name()} &lt;{alocacao.aluno.user.email}&gt;<br>"
        email_message += f"""
            </div><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Solicitante: {request.user.get_full_name()} &lt;{request.user.email}&gt;<br><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Detalhes do pedido:<br>
            <div style="margin-left: 20px;">
            {pedido.get_detalhes_completos()}
            </div><br>
            &nbsp;&nbsp;&nbsp;&nbsp;Anotação:<br>
            <div style="margin-left: 20px;">
            {anotacao if anotacao else "Nenhuma"}
            </div>
        """

        email(email_subject, email_recipients, email_message)

        
        return redirect("gerir_pedidos")

    pedidos = Pedido.objects.all().order_by("status", "-data_solicitacao")
    
    # Organiza os pedidos para facilitar a visualização
    pedidos_pendentes = pedidos.filter(status="pendente")
    pedidos_processados = pedidos.exclude(status="pendente")

    context = {
        "titulo": { "pt": "Gerenciar Pedidos", "en": "Manage Requests" },
        "pedidos_pendentes": pedidos_pendentes,
        "pedidos_processados": pedidos_processados,
    }
    return render(request, "operacional/gerir_pedidos.html", context=context)

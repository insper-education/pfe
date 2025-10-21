#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Dezembro de 2020
"""

import os
import datetime
import dateutil.parser
import logging
import requests
import json

from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Case, When, Value, F, Func, FloatField
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from .support import coleta_membros_banca, editar_banca, mensagem_orientador
from .support import recupera_orientadores_por_semestre
from .support import recupera_coorientadores_por_semestre
from .support import move_avaliacoes, ver_pendencias_professor, mensagem_edicao_banca
from .support3 import resultado_projetos_intern, puxa_encontros, puxa_bancas

from academica.models import Exame, Composicao, Peso
from academica.support import filtra_composicoes, filtra_entregas
from academica.support4 import get_banca_estudante
from academica.support_notas import converte_letra, converte_conceito

from administracao.models import Estrutura, Carta
from administracao.support import usuario_sem_acesso, puxa_github

from calendario.support import cria_material_documento

from documentos.models import TipoDocumento

from estudantes.models import Relato, Pares, FeedbackPares

from professores.support3 import get_banca_incompleta

from projetos.models import Coorientador, ObjetivosDeAprendizagem, Avaliacao2, Observacao
from projetos.models import Banca, Evento, Encontro, Documento, TematicaEncontro
from projetos.models import Projeto, Configuracao
from projetos.support4 import get_objetivos_atuais
from projetos.support2 import get_alocacoes, get_pares_colegas, recupera_envolvidos, anota_participacao
from projetos.messages import email, render_message, htmlizar, message_agendamento_dinamica, prepara_mensagem_email
from projetos.arquivos import le_arquivo

from users.models import PFEUser, Professor, Alocacao
from users.support import get_edicoes


# Get an instance of a logger
logger = logging.getLogger("django")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_professores(request):
    """Mostra página principal do usuário professor."""
    configuracao = get_object_or_404(Configuracao)
    pendencias = ver_pendencias_professor(request.user, configuracao.ano, configuracao.semestre)
    context = {
        "titulo": {"pt": "Área dos Professores", "en": "Professors Area"},
        "pendencias": pendencias,
    }
    if "/professores/professores" in request.path:
        return render(request, "professores/professores.html", context=context)
    else:
        return render(request, "professores/index_professor.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def avaliacoes_pares(request, prof_id=None, proj_id=None):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""
    context = {"titulo": {"pt": "Avaliações de Pares", "en": "Peer Evaluations"}}

    if prof_id and prof_id != "todos":
        orientador = get_object_or_404(Professor, pk=prof_id)
        if (orientador != request.user.professor) and (not request.user.eh_admin):  # Orientador ou Administrador
            return HttpResponse("Acesso negado.", status=401)

    if proj_id:
        context["projetos"] = Projeto.objects.filter(id=proj_id, orientador=orientador)
        
    elif request.is_ajax():
        
        projetos = Projeto.objects.filter(ano__gte=2023)  # 2023 é o ano que comecou a avaliacao de pares no sistema do PFE
        
        if prof_id:
            if prof_id == "todos":
                if not request.user.eh_admin:
                    return HttpResponse("Acesso negado.", status=401)
            else:
                projetos = projetos.filter(orientador=orientador)
        else:
            projetos = projetos.filter(orientador=request.user.professor)

        edicao = request.POST.get("edicao")
        if edicao and edicao != "todas":
            ano, semestre = edicao.split('.')
            projetos = projetos.filter(ano=ano, semestre=semestre)
        elif not edicao:
            return HttpResponse("Algum erro não identificado.", status=401)
            
        context["projetos"] = projetos

    else:
        configuracao = get_object_or_404(Configuracao)
        context["edicoes"] = get_edicoes(Pares)[0]
        context["selecionada_edicao"] = f"{configuracao.ano}.{configuracao.semestre}"
    
    context["administracao"] = request.user.eh_admin

    return render(request, "professores/avaliacoes_pares.html", context=context)


# @login_required
# @permission_required("users.altera_professor", raise_exception=True)
# Permite que compartilhe com a agenda mesmo com pessoas não logadas
def ajax_bancas(request):
    """Retorna as bancas do ano."""
    if request.is_ajax() and "start" in request.POST and "end" in request.POST:
        start = datetime.datetime.strptime(request.POST["start"], "%Y-%m-%d").date() - datetime.timedelta(days=90)
        end = datetime.datetime.strptime(request.POST["end"], "%Y-%m-%d").date() + datetime.timedelta(days=90)
        bancas = {}

        for banca in Banca.objects.filter(startDate__gte=start, startDate__lte=end):
            projeto = banca.get_projeto()
            orientador = projeto.orientador.user.get_full_name() if projeto and projeto.orientador else None
            organizacao_sigla = projeto.organizacao.sigla if projeto and projeto.organizacao else None
            estudante = banca.alocacao.aluno.user.get_full_name() if banca.alocacao else None
            membros = banca.membros()
            if request.user.is_authenticated and request.user.eh_prof_a:
                editable = request.user.eh_admin or (projeto and projeto.orientador == request.user.professor)
            else:
                editable = False

            title = f"{projeto.get_titulo_org()}" if projeto else "Projeto ou alocação não identificados"
            if banca.alocacao:
                title = f"Estudante: {estudante} - {projeto.get_titulo_org()}"
            if banca.location:
                title += f"\n<br>Local: {banca.location}"
            title += "\n<br>Banca:"
            for membro in membros:
                title += f"\n<br>&bull; {membro.get_full_name()}"
                if projeto.orientador and projeto.orientador.user == membro:
                    title += " (O)"

            if banca.composicao and banca.composicao.exame:
                cor = banca.composicao.exame.cor
                className = banca.composicao.exame.className
            else:
                cor = "808080"
                className = ""

            bancas[banca.id] = {
                "start": banca.startDate.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": banca.endDate.strftime("%Y-%m-%dT%H:%M:%S"),
                "local": banca.location,
                "organizacao": organizacao_sigla,
                "orientador": orientador,
                "estudante": estudante,
                "color": f"#{cor}",
                "className": className,
                "editable": editable,
                "title": title,
                **{f"membro{num+1}": membro.get_full_name() for num, membro in enumerate(membros)}
            }

        return JsonResponse(bancas)

    return HttpResponse("Erro.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_banca(request):
    """Atualiza os dados de uma banca por ajax."""
    if request.is_ajax() and all(key in request.POST for key in ("id", "start", "end")):
        try:
            banca = Banca.objects.get(id=request.POST["id"])
            banca.startDate = datetime.datetime.strptime(request.POST["start"], "%d/%m/%Y, %H:%M")
            banca.endDate = datetime.datetime.strptime(request.POST["end"], "%d/%m/%Y, %H:%M")
            banca.save()
            return JsonResponse({"atualizado": True})
        except Banca.DoesNotExist:
            return HttpResponse("Banca não encontrada", status=404)
        except ValueError:
            return HttpResponse("Formado de data inválido", status=400)
    return HttpResponse("Erro.", status=400)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_dinamica(request):
    """Atualiza os dados de uma dinamica por ajax."""
    if request.is_ajax() and all(key in request.POST for key in ("id", "start", "end")):
        try:
            encontro = Encontro.objects.get(id = request.POST["id"])
            encontro.startDate = datetime.datetime.strptime(request.POST["start"], "%d/%m/%Y, %H:%M")
            encontro.endDate = datetime.datetime.strptime(request.POST["end"], "%d/%m/%Y, %H:%M")
            encontro.save()
            return JsonResponse({"atualizado": True,})
        except Encontro.DoesNotExist:
            return HttpResponse("Encontro não encontrada", status=404)
        except ValueError:
            return HttpResponse("Formado de data inválido", status=400)
    return HttpResponse("Erro.", status=400)




def get_edicoes_orientador(orientador, configuracao_ate):
    """Função usada para recuperar todas as edições de orientação de um professor."""

    pares = Projeto.objects.filter(orientador=orientador).values("ano", "semestre")

    edicoes = []
    ano, semestre = None, None
    for pair in pares.distinct("ano", "semestre"):
        ano = pair.get("ano")
        semestre = pair.get("semestre")
        if ano == None or semestre == None:
            continue
        edicoes.append(f"{ano}.{semestre}")
        if ano == configuracao_ate.ano and semestre == configuracao_ate.semestre:
            break

    return edicoes, ano, semestre


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def avaliar_entregas(request, prof_id=None):
    """Página para fzer e ver avaliação de entregas dos estudantes."""

    # Identifica o professor
    professor = None
    if prof_id:
        if prof_id == "todos":
            if not request.user.eh_admin:  # Administrador
                raise PermissionDenied("Sem acesso a estes projetos.")
        else:
            professor = get_object_or_404(Professor, pk=prof_id)
    else:
        professor = request.user.professor

    # Identifica o projeto, se houver
    projeto_id = request.GET.get("projeto", None)

    if request.is_ajax():

        projetos = Projeto.objects.all()

        # Se projeto especificado
        if projeto_id:
            edicao = None
            projetos = projetos.filter(id=projeto_id)
            if (projetos.first().orientador != request.user.professor) and (not request.user.eh_admin):
                raise PermissionDenied("Sem acesso a este projeto.")

        else:
            # Filtrando projetos conforme o professor orientador
            if prof_id is not None:
                if prof_id != "todos":
                    if (professor != request.user.professor) and (not request.user.eh_admin):
                        raise PermissionDenied("Sem acesso a estes projetos.")
                    projetos = projetos.filter(orientador=professor)
            else:
                projetos = projetos.filter(orientador=professor)

            # Filtrando projetos conforme a edição
            edicao = request.POST.get("edicao", None)
            if edicao and edicao != "todas":
                try:
                    ano, semestre = map(int, edicao.split('.'))
                    projetos = projetos.filter(ano=ano, semestre=semestre)
                except ValueError:
                    return HttpResponse("Edição inválida.", status=400)

        # Coletando entregas por projeto
        avaliacoes = [
            (projeto, filtra_entregas(
                filtra_composicoes(Composicao.objects.filter(entregavel=True), projeto.ano, projeto.semestre),
                projeto
            ))
            for projeto in projetos
        ]

        context = {
            "avaliacoes": avaliacoes,
            "edicao": edicao,
            "prazo_avaliar": -int(get_object_or_404(Configuracao).prazo_avaliar),
            "hoje": datetime.date.today(),
        }

    else:  # Não é AJAX
        
        configuracao = get_object_or_404(Configuracao)
        if projeto_id:
            edicoes = None
        elif professor and prof_id != "todos":
            edicoes = get_edicoes_orientador(professor, configuracao)[0]
        else:
            edicoes = get_edicoes(Projeto, configuracao)[0]

        # Coletando os tipos de entregas que podem ser avaliadas
        exames = {c.exame for c in Composicao.objects.filter(entregavel=True)}

        selecionada_edicao = None
        edicao = request.GET.get("edicao", None)
        if edicao:
            if edicao == "todas":
                selecionada_edicao = "todas"
            else:
                try:
                    ano, semestre = map(int, edicao.split('.'))
                    selecionada_edicao = f"{ano}.{semestre}"
                except ValueError:
                    raise PermissionDenied("Acesso negado.")        
        if edicoes and selecionada_edicao not in edicoes:  # Precisa estar entre as possíveis
            selecionada_edicao = None
        
        base_url = reverse("avaliar_entregas")
        endpoints = [
            {"path": f"{base_url}{{valor}}", "method": "GET", "description": "acessa o cadastro do professor com id igual a valor."},
            {"path": f"{base_url}?edicao={{valor}}", "method": "GET", "description": "seleciona a edição dos projetos a ser apresentado. Exemplo: selecao=2023.1"},
            {"path": f"{base_url}?edicao=todas", "method": "GET", "description": "seleciona todas as edições."},
            {"path": f"{base_url}?projeto={{valor}}", "method": "GET", "description": "seleciona o projeto com id igual a valor."},
        ]

        context = {
                "titulo": {"pt": "Avaliar Entregas", "en": "Evaluate Deliveries"},
                "edicoes": edicoes,
                "selecionada_edicao": selecionada_edicao,
                "tipos_entregas": exames if (prof_id=="todos") else None,
                "endpoints": json.dumps(endpoints),
            }

    return render(request, "professores/avaliar_entregas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def aulas_tabela(request):
    """Lista todas as aulas agendadas, conforme periodo pedido."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            if edicao == "todas":
                aulas = Evento.objects.filter(tipo_evento__sigla="A")
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    aulas = Evento.objects.filter(tipo_evento__sigla="A", endDate__year=ano)
                elif semestre == '1':
                    aulas = Evento.objects.filter(tipo_evento__sigla="A", endDate__year=ano, endDate__month__lt=7)
                else:  # semestre == '2':
                    aulas = Evento.objects.filter(tipo_evento__sigla="A", endDate__year=ano, endDate__month__gt=6)

        cabecalhos = [{"pt": "Nome", "en": "Name"},
                      {"pt": "e-mail", "en": "e-mail"},
                      {"pt": "Aula/Data", "en": "Class/Date"}]
        context = {
            "aulas": aulas,
            "cabecalhos": cabecalhos,
            }

    else:
        context = {
            "titulo": { "pt": "Alocação em Aulas", "en": "Class Allocation" },
            "edicoes": get_edicoes(Projeto, anual=True)[0],
            }

    return render(request, "professores/aulas_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def avaliar_bancas(request, prof_id=None):
    """Visualiza os resultados das bancas de um projeto."""

    if request.is_ajax():

        if "edicao" in request.POST:

            if prof_id and request.user.eh_admin:  # Administrador
                professor = get_object_or_404(Professor, pk=prof_id)
            else:
                professor = request.user.professor

            bancas = Banca.get_bancas_com_membro(professor.user).order_by("composicao__exame__id")

            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = request.POST["edicao"].split('.')
                bancas = bancas.filter(projeto__ano=ano, projeto__semestre=semestre)

        else:
            return HttpResponse("Erro ao carregar dados.", status=401)
        
        context = {
            "objetivos": ObjetivosDeAprendizagem.objects.all(),
            "bancas": bancas,
            "hoje": datetime.datetime.now(),
        }
    else:
        configuracao = get_object_or_404(Configuracao)
        context = {
            "titulo": {"pt": "Avaliar Bancas", "en": "Evaluate Examination Boards"},
            "edicoes": get_edicoes(Projeto)[0],
            "selecionada_edicao": f"{configuracao.ano}.{configuracao.semestre}",
        }
    return render(request, "professores/resultado_bancas.html", context=context)


@transaction.atomic
def banca(request, slug):
    """Somente ve a banca, sem edição."""
    banca = get_object_or_404(Banca, slug=slug)

    if banca.composicao.exame.sigla == "BI":  # (1, "intermediaria"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Intermediária") | TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
    elif banca.composicao.exame.sigla == "BF":  # (0, "final"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.composicao.exame.sigla == "F":  # (2, "falconi"),
        # Reaproveita o tipo de documento da banca final
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.composicao.exame.sigla == "P":  # (3, "probation"),
        # Reaproveita o tipo de documento da banca final
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório para Probation") | TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    else:
        tipo_documento = None
    
    if tipo_documento:
        documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
        if banca.alocacao and banca.alocacao.projeto:
            documentos = documentos | Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.alocacao.projeto)
        documentos = documentos.order_by("tipo_documento", "-data")
    else:
        documentos = None

    context = {
        "titulo": {"pt": "Banca", "en": "Examination Board"},
        "banca": banca,
        "documentos": documentos,
        "bloqueado": True,
    }

    return render(request, "professores/banca_ver.html", context)


# Qualquer um consegue acessar, mesmo não logado
def encontro_feedback(request, pk):
    """Cria uma tela para preencher feedbacks das mentorias."""
    encontro = get_object_or_404(Encontro, pk=pk)
    if not encontro.projeto:
        return HttpResponseNotFound("<h1>Nenhum Projeto foi definido para esse encontro/mentoria!</h1>")

    envolvidos = recupera_envolvidos(encontro.projeto, encontro=encontro, filtro=['E'])

    if request.method == "POST":
        encontro.observacoes_estudantes = request.POST.get("observacoes_estudantes")
        encontro.observacoes_orientador = request.POST.get("observacoes_orientador")
        encontro.save()

        participantes = anota_participacao(request.POST, encontro=encontro)

        # Mensagem para facilitador
        subject = "Capstone | Anotações de Mentoria - " + encontro.projeto.get_titulo_org()
        configuracao = get_object_or_404(Configuracao)
        #recipient_list = [encontro.facilitador.email, encontro.projeto.orientador.user.email, configuracao.coordenacao.user.email]

        recipient_list = list(filter(None, [
            getattr(encontro.facilitador, "email", None),
            getattr(encontro.projeto and encontro.projeto.orientador and encontro.projeto.orientador.user, "email", None),
            getattr(configuracao and configuracao.coordenacao and configuracao.coordenacao.user, "email", None)
        ]))

        context_email = {
            "encontro": encontro,
            "participantes": participantes,
            "configuracao": configuracao,
        }

        mensagem = render_message("Anotações de Mentoria", context_email)
        email(subject, recipient_list, mensagem)

        if request.user.is_authenticated:
            return redirect("dinamicas_lista")
        else:
            context = {"mensagem": {"pt": "Observações Enviadas, Obrigado", "en": "Notes Sent, Thank you"}}
            return render(request, "generic_ml.html", context=context)

    context = {
            "titulo": {"pt": "Feedback de Mentoria", "en": "Mentoring Feedback"},
            "encontro": encontro,
            "envolvidos": {encontro.projeto.id: envolvidos},
        }

    return render(request, "professores/encontro_feedback.html", context=context)


@transaction.atomic
def banca_avaliar(request, slug, documento_id=None):
    """Cria uma tela para preencher avaliações de bancas."""
    configuracao = get_object_or_404(Configuracao)
    mensagem = ""

    try:
        banca = Banca.objects.get(slug=slug)
        if banca.projeto is None and banca.alocacao is None:
            return HttpResponseNotFound("<h1>Banca não registrada corretamente!</h1>")
        
        adm = PFEUser.objects.filter(pk=request.user.pk, tipo_de_usuario=4).exists()  # se adm
        vencida = banca.endDate.date() + datetime.timedelta(days=configuracao.prazo_avaliar_banca) < datetime.date.today()

        if vencida:  # prazo vencido
            mensagem += render_message("Banca Vencida", {"banca": banca, "configuracao": configuracao})
            if not adm:  # se administrador passa direto
                context = {
                    "area_principal": True,
                    "mensagem": {"pt": mensagem, "en": mensagem},  # Arrumar isso
                }
                return render(request, "generic_ml.html", context=context)

    except Banca.DoesNotExist:
        return HttpResponseNotFound("<h1>Banca não encontrada!</h1>")

    projeto = banca.get_projeto()

    # Usado para pegar o relatório de avaliação de banca para usuários não cadastrados
    if documento_id:
        documento = Documento.objects.get(id=documento_id, projeto=projeto)
        path = str(documento.documento).split('/')[-1]
        local_path = os.path.join(settings.MEDIA_ROOT, "{0}".format(documento.documento))
        diferenca = (datetime.date.today() - banca.endDate.date()).days
        if diferenca > 2 * configuracao.prazo_avaliar_banca:
            return HttpResponseNotFound("<h1>Link expirado!<br> Documentos só podem ser visualizados até " + str(2 * configuracao.prazo_avaliar_banca) + " dias após a data da banca!</h1>")
        return le_arquivo(request, local_path, path, bypass_confidencial=True)

    objetivos = banca.composicao.pesos.all()
    pesos = Peso.objects.filter(composicao=banca.composicao)
    
    if request.method == "POST":
        if "avaliador" in request.POST:

            avaliador = get_object_or_404(PFEUser, pk=int(request.POST["avaliador"]))
            exame = banca.composicao.exame

            # Identifica que uma avaliação/observação já foi realizada anteriormente
            avaliacoes_anteriores = Avaliacao2.objects.filter(projeto=projeto, avaliador=avaliador, exame=exame)
            observacoes_anteriores = Observacao.objects.filter(projeto=projeto, avaliador=avaliador, exame=exame)
            if banca.alocacao:
                avaliacoes_anteriores = avaliacoes_anteriores.filter(alocacao=banca.alocacao)
                observacoes_anteriores = observacoes_anteriores.filter(alocacao=banca.alocacao)
            
            realizada = avaliacoes_anteriores.exists()

            # Mover avaliação anterior para base de dados de Avaliações Velhas
            move_avaliacoes(avaliacoes_anteriores, observacoes_anteriores)

            objetivos_possiveis = len(objetivos)
            julgamento = [None]*objetivos_possiveis
            
            avaliacoes = dict(filter(lambda elem: elem[0][:9] == "objetivo.", request.POST.items()))

            for i, aval in enumerate(avaliacoes):

                pk_objetivo, conceito = request.POST[aval].split('.')
                julgamento[i] = Avaliacao2.objects.create(projeto=projeto, exame=exame, avaliador=avaliador)
                julgamento[i].alocacao = banca.alocacao  # Caso Probation
                julgamento[i].objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=pk_objetivo)

                if conceito == "NA":
                    julgamento[i].na = True
                else:
                    julgamento[i].na = False
                    julgamento[i].nota = converte_conceito(conceito)
                    if exame.titulo == "Banca Intermediária" or exame.titulo == "Banca Final":
                        julgamento[i].peso = pesos.get(objetivo=julgamento[i].objetivo).peso
                    else:
                        julgamento[i].peso = 0.0 

                julgamento[i].save()

            julgamento_observacoes = None
            if ("observacoes_orientador" in request.POST and request.POST["observacoes_orientador"] != "") or \
               ("observacoes_estudantes" in request.POST and request.POST["observacoes_estudantes"] != "") or \
               ("destaque" in request.POST):
                julgamento_observacoes = Observacao.objects.create(projeto=projeto, exame=exame, avaliador=avaliador)
                julgamento_observacoes.alocacao = banca.alocacao  # Caso Probation
                julgamento_observacoes.observacoes_orientador = request.POST.get("observacoes_orientador")
                julgamento_observacoes.observacoes_estudantes = request.POST.get("observacoes_estudantes")                
                julgamento_observacoes.destaque = True if request.POST.get("destaque") == "true" else False
                julgamento_observacoes.save()

            if "arquivo" in request.FILES:
                # Envia documento com anotações para os envolvidos intantanemente
                documento = cria_material_documento(request, "arquivo", sigla="RAMB", confidencial=False,
                                                    projeto=projeto, usuario=avaliador,
                                                    prefix="rev_"+str(avaliador.first_name)+"_"+str(banca.composicao.exame.sigla)+"_")
                if documento:
                    documento.anotacao = banca.composicao.exame.titulo
                    documento.save()
                    subject = "Capstone | Documento com anotações - " + banca.composicao.exame.titulo + " "
                    subject += projeto.get_titulo_org()
                    mensagem_anot = "Anotações em Relatório de Banca<br>\n<br>\n"
                    mensagem_anot += "Anotações realizadas por: " + avaliador.get_full_name() + "<br>\n"
                    mensagem_anot += "Banca: " + banca.composicao.exame.titulo + "<br>\n"
                    mensagem_anot += "Projeto: " + projeto.get_titulo_org() + "<br>\n"
                    mensagem_anot += "Data: " + str(datetime.datetime.now()) + "<br>\n<br>\n<br>\n"
                    mensagem_anot += "Documento com Anotações: "
                    mensagem_anot += "<a href='" + request.scheme + "://" + request.get_host() + documento.documento.url + "' target='_blank' rel='noopener noreferrer'>"
                    mensagem_anot += request.scheme + "://" + request.get_host() + documento.documento.url + "</a><br>\n<br>\n<br>\n"
                    recipient_list = [alocacao.aluno.user.email for alocacao in projeto.alocacao_set.all()]
                    recipient_list.append(avaliador.email)
                    recipient_list.append(projeto.orientador.user.email)
                    #recipient_list.append(configuracao.coordenacao.user.email)
                    email(subject, recipient_list, mensagem_anot)

            subject = "Capstone | Avaliação de Banca - " + banca.composicao.exame.titulo + " "
            if banca.composicao.exame.sigla == "P":
                subject += banca.alocacao.aluno.user.get_full_name() + " "
            subject += projeto.get_titulo_org()

            # Envio de mensagem para Avaliador
            context_carta = {
                "request": request,
                "avaliador": avaliador,
                "realizada": realizada,
                "banca": banca,
                "julgamento": julgamento,
                "julgamento_observacoes": julgamento_observacoes,
                "destaque": True if request.POST.get("destaque") == "true" else False,
            }
            message = render_message("Resultado Avaliador", context_carta, urlize=False)

            recipient_list = [avaliador.email, ]
            email(subject, recipient_list, message)
            
            # Envio de mensagem para Orientador / Coordenação
            message = mensagem_orientador(banca)
            
            if banca.composicao.exame.sigla in ["BI", "BF"]:  # Intermediária e Final
                recipient_list = [projeto.orientador.user.email, ]
            else:  # Falconi ou Probation
                recipient_list = [configuracao.coordenacao.user.email, ]
            email(subject, recipient_list, message)
            
            resposta = {"pt": "Avaliação submetida e enviada para:<br>", "en": "Evaluation submitted and sent to:<br>"}
            for recipient in recipient_list:
                resposta["pt"] += "&bull; {0}<br>".format(recipient)
                resposta["en"] += "&bull; {0}<br>".format(recipient)
            if realizada:
                resposta["pt"] += "<br><br><h2>Essa é uma atualização de uma avaliação já enviada anteriormente!</h2><br><br>"
                resposta["en"] += "<br><br><h2>This is an update of an evaluation already sent!</h2><br><br>"

            context = {
                "area_principal": True,
                "mensagem": resposta,
            }
            return render(request, "generic_ml.html", context=context)

        return HttpResponse("Avaliação não submetida.")
    else:

        pessoas, membros = coleta_membros_banca(banca)
        composicao = banca.composicao

        # Identificando quem seria o avaliador
        avaliador_id = request.GET.get("avaliador")
        if avaliador_id:
            try:
                avaliador_id = int(avaliador_id)
            except ValueError:
                return HttpResponseNotFound("<h1>Usuário não encontrado!</h1>")
        else:
            avaliador_id = request.user.pk if request.user.is_authenticated else None
        
        conceitos = [None]*len(objetivos)
        for i in range(len(objetivos)):
            try:
                tmp_objetivo = int(request.GET.get("objetivo"+str(i), '0'))
            except ValueError:
                return HttpResponseNotFound("<h1>Erro em objetivo!</h1>")
            tmp_conceito = request.GET.get("conceito"+str(i), '')
            conceitos[i] = (tmp_objetivo, tmp_conceito)

        map_tipo_documento = {
            "BF": TipoDocumento.objects.filter(nome__in=["Apresentação da Banca Final", "Relatório Final de Grupo"]),
            "BI": TipoDocumento.objects.filter(nome__in=["Apresentação da Banca Intermediária", "Relatório Intermediário de Grupo"]),
            "F": TipoDocumento.objects.filter(nome__in=["Apresentação da Banca Final", "Relatório Final de Grupo"]),
            "P": TipoDocumento.objects.filter(nome__in=["Parecer para Probation", "Apresentação da Banca Final", "Relatório Final de Grupo"]),
        }

        tipo_documento = map_tipo_documento.get(banca.composicao.exame.sigla)

        documentos = None
        if tipo_documento:
            documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=projeto).order_by("tipo_documento", "-data")

        if banca.composicao.exame.sigla == "P":  # Probation
            documentos = documentos | Documento.objects.filter(tipo_documento__sigla="RII", usuario=banca.alocacao.aluno.user) | Documento.objects.filter(tipo_documento__sigla="RIF", usuario=banca.alocacao.aluno.user)
            
        niveis_objetivos = Estrutura.loads(nome="Níveis de Objetivos")

        destaque = request.GET.get("destaque", None)
        if destaque is not None:
            destaque = True if destaque == "True" else False

        base_url = reverse("banca_avaliar", kwargs={"slug": slug})
        endpoints = [
            {"path": f"{base_url}?avaliador={{valor}}", "method": "GET", "description": "Seleciona o avaliador."},
            {"path": f"{base_url}?objetivo{{num}}={{id}}&conceito{{num}}={{conceito}}", "method": "GET", "description": "Preenche um conceito para um objetivo."},
            {"path": f"{base_url}?observacoes_orientador={{texto}}", "method": "GET", "description": "Preenche as observações do orientador."},
            {"path": f"{base_url}?observacoes_estudantes={{texto}}", "method": "GET", "description": "Preenche as observações dos estudantes."},
            {"path": f"{base_url}?destaque={{valor}}", "method": "GET", "description": "Marca que o avaliador quer destacar o projeto."},
            {"path": f"{base_url}/{{slug}}/{{documento_id}}", "method": "GET", "description": "Baixa o documento de avaliação da banca."},
        ]

        context = {
            "titulo": {"pt": "Formulário de Avaliação de Bancas", "en": "Examination Board Evaluation Form"},
            "projeto": projeto,
            "estudante": banca.alocacao.aluno if banca.alocacao else None,
            "individual": True if banca.alocacao else False,
            "pessoas": pessoas,
            "membros": membros,
            "pesos": pesos,
            "banca": banca,
            "composicao": composicao,
            "avaliador": avaliador_id,
            "conceitos": conceitos,
            "documentos": documentos,
            "observacoes_orientador": unquote(request.GET.get("observacoes_orientador", '')),
            "observacoes_estudantes": unquote(request.GET.get("observacoes_estudantes", '')),
            "today": datetime.datetime.now(),
            "periodo_para_rubricas": banca.composicao.exame.periodo_para_rubricas,
            "niveis_objetivos": niveis_objetivos,
            "destaque": destaque,
            "endpoints": json.dumps(endpoints),
        }

        if mensagem:
            context["mensagem_aviso"] = {"pt": mensagem, "en": mensagem}

        return render(request, "professores/banca_avaliar.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def banca_ver(request, primarykey):
    """Retorna banca pedida."""
    banca = get_object_or_404(Banca, id=primarykey)
    if banca.composicao.exame.sigla == "BI":  # (1, "intermediaria"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Intermediária") | TipoDocumento.objects.filter(nome="Relatório Intermediário de Grupo")
    elif banca.composicao.exame.sigla == "BF":  # (0, "final"),
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.composicao.exame.sigla == "F":  # (2, "falconi"),
        # Repetindo banca final para falconi
        tipo_documento = TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    elif banca.composicao.exame.sigla == "P":  # (3, "probation"),
        # Repetindo banca final para probation
        tipo_documento = TipoDocumento.objects.filter(nome="Relatório para Probation") | TipoDocumento.objects.filter(nome="Apresentação da Banca Final") | TipoDocumento.objects.filter(nome="Relatório Final de Grupo")
    else:
        tipo_documento = TipoDocumento.objects.none()

    documentos = Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.projeto)
    if banca.alocacao and banca.alocacao.projeto:
        documentos = documentos | Documento.objects.filter(tipo_documento__in=tipo_documento, projeto=banca.alocacao.projeto)
    documentos = documentos.order_by("tipo_documento", "-data")

    context = {
        "titulo": {"pt": "Banca", "en": "Examination Board"},
        "banca": banca,
        "documentos": documentos,
    }

    return render(request, "professores/banca_ver.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_alocadas(request):
    """Mostra detalhes sobre o professor."""
    
    bancas = Banca.get_bancas_com_membro(request.user)

    # Usado para inverter as datas das bancas atuais
    periodo = timezone.now().date() - datetime.timedelta(days=30)
    bancas = bancas.annotate(
        custom_order=Case(
            When(startDate__lt=periodo, then=Value(100000000000)),
            When(startDate__gte=periodo, then=Func(F("startDate"), function='EXTRACT', template="%(function)s(EPOCH FROM %(expressions)s)", output_field=FloatField())),
            output_field=FloatField(),
        )
    ).order_by("custom_order", "-startDate")

    context = {
        "titulo": {"pt": "Participação em Bancas", "en": "Member in Examination Boards"},
        "bancas": bancas,
        }
    return render(request, "professores/bancas_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_tabela_alocacao_completa(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    configuracao = get_object_or_404(Configuracao)

    membros_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        membros = dict()
        bancas = Banca.objects.all().filter(projeto__ano=ano).filter(projeto__semestre=semestre)
        for banca in bancas:
            for membro in banca.membros():
                membros.setdefault(membro, []).append(banca)

        membros_pfe.append(membros)
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    # inverti lista deixando os mais novos primeiro
    anos = zip(membros_pfe[::-1], periodo[::-1])

    informacoes = [
        ("#MembrosTable tr > *:nth-child(2)", "e-mail", "e-mail"),
        ("#MembrosTable tr > *:nth-child(3)", "Quantidade", "Quantity"),
        ("#MembrosTable tr > *:nth-child(4)", "Projetos", "Projects"),
    ]

    context = {
        "anos": anos,
        "informacoes": informacoes,
        "titulo": { "pt": "Alocação em Bancas", "en": "Examination Board Assignment" },
    }

    return render(request, "professores/bancas_tabela_alocacao_completa.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_criar(request, data=None):
    """Cria uma banca de avaliação para o projeto."""

    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax() and request.method == "POST":

        atualizado = True
        mensagem, banca = editar_banca(None, request)
        if mensagem is None:
            mensagem_edicao_banca(banca, enviar=("enviar_mensagem" in request.POST)) # Atualizada
        else:
            atualizado = False

        context = {
            "atualizado": atualizado,
            "mensagem": mensagem,
        }
        return JsonResponse(context)

    # Originalmente estava: .exclude(orientador=None)
    projetos = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre)
    alocacoes = Alocacao.objects.filter(projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre).order_by("aluno__user__first_name", "aluno__user__last_name")    
    professores, falconis = coleta_membros_banca()

    # Coletando bancas agendadas a partir de hoje
    hoje = datetime.date.today()
    bancas_agendadas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    projetos_agendados = list(bancas_agendadas.values_list("projeto", flat=True))

    eventos = Evento.get_eventos(configuracao=configuracao)
    tipos_banca = Composicao.get_composicoes(configuracao.ano, configuracao.semestre).filter(exame__banca=True).order_by("exame__id")  # Ordena por ID para manter a ordem de BI, BF, F, P

    bancas_intermediarias = eventos.filter(tipo_evento__sigla="BI")
    bancas_finais = eventos.filter(tipo_evento__sigla="BF")
    bancas_probation = eventos.filter(tipo_evento__sigla="P")
    bancas_falconi = eventos.filter(tipo_evento__sigla="F")

    context = {
        "projetos": projetos,
        "alocacoes": alocacoes,
        "professores": professores,
        "Banca": Banca,
        "tipos_banca": tipos_banca,
        "falconis": falconis,
        "projetos_agendados": projetos_agendados,
        "bancas_intermediarias": bancas_intermediarias,
        "bancas_finais": bancas_finais,
        "bancas_probation": bancas_probation,
        "bancas_falconi": bancas_falconi,
        "url": request.get_full_path(),
        "root_page_url": request.session.get("root_page_url", '/'),
    }

    if data:
        context["data"] = data[:10]  # soh a data, tirando a hora se for o caso
        datar = datetime.datetime.strptime(context["data"], "%Y-%m-%d").date()
        if bancas_finais and bancas_finais.first().startDate and bancas_finais.last().endDate:
            if datar >= bancas_finais.first().startDate and datar <= bancas_finais.last().endDate:
                context["tipob"] = "BF"
        if bancas_intermediarias and bancas_intermediarias.first().startDate and bancas_intermediarias.last().endDate:
            if datar >= bancas_intermediarias.first().startDate and datar <= bancas_intermediarias.last().endDate:
                context["tipob"] = "BI"
        if bancas_falconi and bancas_falconi.first().startDate and bancas_falconi.last().endDate:
            if datar >= bancas_falconi.first().startDate and datar <= bancas_falconi.last().endDate:
                context["tipob"] = "F"
        if bancas_probation and bancas_probation.first().startDate and bancas_probation.last().endDate:
            if datar >= bancas_probation.first().startDate and datar <= bancas_probation.last().endDate:
                context["tipob"] = "P"
        
    return render(request, "professores/bancas_view.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_editar(request, primarykey=None):
    """Edita uma banca de avaliação para o projeto."""
    configuracao = get_object_or_404(Configuracao)

    if primarykey is None:
        return HttpResponseNotFound("<h1>Erro!</h1>")

    banca = get_object_or_404(Banca, pk=primarykey)

    if request.is_ajax() and request.method == "POST":

        atualizado = True
        mensagem = ""
        if "atualizar" in request.POST:
            mensagem, _ = editar_banca(banca, request)
            if mensagem is None:
                mensagem_edicao_banca(banca, True, enviar=("enviar_mensagem" in request.POST)) # Atualizada
            else:
                atualizado = False
        elif "excluir" in request.POST:
            mensagem_edicao_banca(banca, True, True, enviar=("enviar_mensagem" in request.POST)) # Excluída
            if "projeto" in request.POST:
                banca.delete()
        else:
            return HttpResponse("Atualização não realizada.", status=401)

        context = {
                "atualizado": atualizado,
                "mensagem": mensagem,
            }
        return JsonResponse(context)
    
    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre).exclude(orientador=None)
    alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
    professores, falconis = coleta_membros_banca()

    eventos = Evento.get_eventos(configuracao=configuracao)
    tipos_banca = Composicao.get_composicoes(ano, semestre).filter(exame__banca=True).order_by("exame__id")  # Ordena por ID para manter a ordem de BI, BF, F, P

    bancas_intermediarias = eventos.filter(tipo_evento__sigla="BI").order_by("startDate")
    bancas_finais = eventos.filter(tipo_evento__sigla="BF").order_by("startDate")
    bancas_probation = eventos.filter(tipo_evento__sigla="P").order_by("startDate")
    bancas_falconi = eventos.filter(tipo_evento__sigla="F").order_by("startDate")

    context = {
        "projetos": projetos,  # Creio que não seja necessário
        "alocacoes": alocacoes,   # Creio que não seja necessário
        "professores": professores,
        "banca": banca,
        "Banca": Banca,
        "tipos_banca": tipos_banca,
        "falconis": falconis,
        "bancas_intermediarias": bancas_intermediarias,
        "bancas_finais": bancas_finais,
        "bancas_probation": bancas_probation,
        "bancas_falconi": bancas_falconi,
        "url": request.get_full_path(),
        "root_page_url": request.session.get("root_page_url", '/'),
    }
    return render(request, "professores/bancas_view.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_tabela_alocacao(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                bancas = Banca.objects.all()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    bancas = Banca.objects.filter(projeto__ano=ano)
                else:
                    bancas = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

            membros = dict()
            
            for banca in bancas:
                for membro in banca.membros():
                    membros.setdefault(membro, []).append(banca)
    
        cabecalhos = [{"pt": "Nome", "en": "Name"},
                      {"pt": "e-mail", "en": "e-mail"},
                      {"pt": "Grupos", "en": "Groups"},
                      {"pt": "Projetos", "en": "Projects"}]
        
        context = {
            "cabecalhos": cabecalhos,
            "membros": membros,
            }

    else:
        context = {
            "titulo": { "pt": "Alocação em Bancas", "en": "Examination Board Allocation" },
            "edicoes": get_edicoes(Projeto, anual=True)[0],
            }

    return render(request, "professores/bancas_tabela_alocacao.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def coorientacoes_alocadas(request):
    """Mostra detalhes sobre o professor."""
    context = {
        "titulo": {"pt": "Projetos Coorientados", "en": "Cooriented Projects"},
        "coorientacoes": Coorientador.objects.filter(usuario=request.user).order_by("-projeto__ano", "-projeto__semestre"),
        }
    return render(request, "professores/coorientacoes_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_index(request, facilit_id=None):
    """Menus de encontros/mentorias."""

    encontros = Encontro.objects.all().order_by("startDate")
    
    if facilit_id and request.user.eh_admin:  # Administrador
        facilitador = get_object_or_404(PFEUser, pk=facilit_id)
        encontros = encontros.filter(facilitador=facilitador)

    context = {
        "titulo": {"pt": "Agendar Mentorias", "en": "Schedule Mentorships"},
        "encontros": encontros,
        }
    return render(request, "professores/dinamicas_index.html", context)


# @login_required
# @permission_required("users.altera_professor", raise_exception=True)
def bancas_index(request, prof_id=None):
    """Menus de bancas e calendario de bancas."""
    dias_bancas = Evento.objects.filter(tipo_evento__sigla__in=("BI", "BF", "P", "F"))
    if request.user.is_authenticated:
        usuario = request.user
        if prof_id and request.user.eh_admin:  # Administrador
            professor = get_object_or_404(Professor, pk=prof_id)
        elif request.user.eh_prof:
            professor = request.user.professor
        else:
            professor = None
    else:
        usuario = None
        professor = None

    # checando se projetos atuais tem banca marcada
    configuracao = get_object_or_404(Configuracao)
    hoje = datetime.date.today()
    bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    sem_banca = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre, orientador=professor)
    for banca in bancas:
        if banca.projeto:
            sem_banca = sem_banca.exclude(id=banca.projeto.id)

    # Usando para #atualizar a página raiz no edit da banca
    request.session["root_page_url"] = request.build_absolute_uri()
    context = {
        "titulo": {"pt": "Agenda de Bancas", "en": "Examination Board Schedule"},
        "dias_bancas": dias_bancas,
        "view": request.GET.get("view", None),
        "date": request.GET.get("date", None),
        "usuario": usuario,
        "sem_banca": sem_banca,
        "root_page_url": request.session["root_page_url"],  # Usando para #atualizar a página raiz no edit da banca
    }

    return render(request, "professores/bancas_index.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_lista(request, edicao=None):
    """Mostra os horários de dinâmicas."""

    if request.is_ajax() and "edicao" in request.POST:
        context = puxa_encontros(request.POST["edicao"])

    else:

        informacoes = [
                (".tematica", "tematica", "theme"),
                (".local", "local", "local"),
                (".grupo", "grupo", "group"),
                (".orientacao", "orientação", "supervision"),
                (".cursos", "cursos", "programs"),
                (".facilitador", "facilitador", "facilitator"),
                (".avaliacao", "link avaliação", "evaluation link"),
                (".agendamento", "agendamento", "schedule"),
                (".email", "e-mail", "e-mail"),
                (".editar", "editar", "edit"),
                (".sem_agendamento", "sem agendamento", "without schedule"),
            ]

        configuracao = get_object_or_404(Configuracao)
        context = {
                "titulo": {"pt": "Listagem das Mentorias", "en": "List of Mentoring"},
                "edicoes": get_edicoes(Projeto)[0],
                "informacoes": informacoes,
                "configuracao": configuracao,
                "tematicas": TematicaEncontro.objects.all().order_by("nome"),
            }
        
        if edicao:
            if '.' in edicao:
                context["selecionada_edicao"] = edicao
            elif edicao != "proximas" and edicao != "todas":
                context["projeto"] = get_object_or_404(Projeto, id=edicao)
        
    # Usando para #atualizar a página raiz no edit da banca
    request.session["root_page_url"] = request.build_absolute_uri()
    context["root_page_url"] = request.session["root_page_url"]
    context["hoje"] = datetime.date.today()

    return render(request, "professores/dinamicas_lista.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ajax_permite_agendar_mentorias(request):
    """Atualiza uma configuração de agendamento de mentorias."""

    if request.is_ajax():
        configuracao = get_object_or_404(Configuracao)
        configuracao.permite_agendar_mentorias = request.POST.get("permite_agendar_mentorias") == "true"
        configuracao.save()
        return JsonResponse({"atualizado": True})

    return HttpResponse("Erro não identificado.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ajax_atualiza_visibilidade_tematica(request):
    """Atualiza uma configuração de visibilidade de temáticas de mentorias."""

    if request.is_ajax():
        tematica_id = request.POST.get("tematica_id", None)
        visibilidade = request.POST.get("visibilidade", None)
        if tematica_id and visibilidade is not None:
            try:
                tematica = get_object_or_404(TematicaEncontro, pk=int(tematica_id))
            except ValueError:
                return HttpResponse("Temática não encontrada.", status=404)
            tematica.visibilidade = True if visibilidade == "true" else False
            tematica.save()
            return JsonResponse({"atualizado": True})

    return HttpResponse("Erro não identificado.", status=401)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def ajax_verifica_membro_banca(request):
    """Verifica se o usuário é membro de alguma banca."""
    membro_id = request.POST.get("membro_id", None)
    edicao = request.POST.get("edicao", None)
    tipo = [request.POST.get("tipo", None)]  # "BI", "BF", "P", "F"
    remove_banca = request.POST.get("remove_banca", None)
    if request.is_ajax() and membro_id and tipo:
        try:
            membro = get_object_or_404(PFEUser, pk=int(membro_id))
        except ValueError:
            return HttpResponse("Membro não encontrado.", status=404)
        bancas = Banca.get_bancas_com_membro(membro, siglas=tipo)

        if edicao and '.' in edicao:
            ano, semestre = edicao.split('.')
            bancas = bancas.filter(projeto__ano=ano, projeto__semestre=semestre)
        else:
            configuracao = get_object_or_404(Configuracao)
            bancas = bancas.filter(projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre)
        
        if remove_banca:
            remove_banca = int(remove_banca)
            bancas = bancas.exclude(id=remove_banca)

        lista_bancas = []
        for banca in bancas:
            if banca.alocacao:
                aluno_nome = banca.alocacao.aluno.user.get_full_name()
                aluno_email = banca.alocacao.aluno.user.email
                projeto_titulo = banca.alocacao.projeto.get_titulo_org()
            else:
                aluno_nome = ""
                aluno_email = ""
                projeto_titulo = banca.projeto.get_titulo_org() if banca.projeto else ""
            data = banca.startDate.strftime("%d/%m %H:%M") if banca.startDate else ""
            data += " às " + banca.endDate.strftime("%H:%M") if banca.endDate else ""
            lista_bancas.append({
                "id": banca.id,
                "data": data,
                "tipo": banca.composicao.exame.titulo if banca.composicao and banca.composicao.exame else "",
                "projeto": projeto_titulo,
                "aluno_nome": aluno_nome,
                "aluno_email": aluno_email,
                "local": banca.location if banca.location else "",
                "link": banca.link if banca.link else "",
            })

        return JsonResponse({"lista_bancas": lista_bancas})
    return HttpResponse("Erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_lista(request, edicao=None):
    """Lista as bancas agendadas, conforme periodo ou projeto pedido."""
    configuracao = get_object_or_404(Configuracao)
    context = {"titulo": {"pt": "Listagem das Bancas", "en": "List of Examination Boards"},}
    
    # Usando para #atualizar a página raiz no edit da banca
    request.session["root_page_url"] = request.build_absolute_uri()
    context["root_page_url"] = request.session["root_page_url"]

    context["dias_bancas"] = Evento.objects.filter(tipo_evento__sigla__in=("BI", "BF", "P", "F"))
    context["tipos_bancas"] = Exame.objects.filter(banca=True).order_by("id")
        
    if request.is_ajax() and "edicao" in request.POST:
        context.update(puxa_bancas(request.POST["edicao"]))
        
    elif request.method == "POST":

        aviso = ""
        # pega todas as bancas marcadas
        dados = request.POST.getlist("banca")
        for d in dados:
            banca = get_object_or_404(Banca, pk=d)
            projeto = banca.get_projeto()
            recipient_list = []
            for membro in banca.membros():
                recipient_list.append(membro.email)
            recipient_list.append(configuracao.coordenacao.user.email)
            if banca and banca.alocacao:
                assunto = "Capstone | Banca: " + banca.alocacao.aluno.user.get_full_name() + " " + banca.alocacao.projeto.get_titulo_org()
            else:
                assunto = "Capstone | Banca: " + projeto.get_titulo_org()
            context_carta = {
                "request": request,
                "projeto": projeto,
                "banca": banca,
            }
            mensagem = render_message("Mensagem Banca", context_carta, urlize=False)
            email(assunto, recipient_list, mensagem)
            aviso += "Banca de " + projeto.get_titulo_org() + " enviada para: " + str(recipient_list) + "<br>"

        mensagem = {
            "pt": "Mensagens de Avaliação de Bancas enviadas.<br><br>" + aviso,
            "en": "Examination Board Evaluation Messages sent.<br><br>" + aviso,
        }
        context = {
            "voltar": True,
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic_ml.html", context=context)

    else:
        context["informacoes"] = [
                (".local", "local", "local"),
                (".link", "video-conferência", "video-conference"),
                (".grupo", "grupo", "group"),
                (".orientacao", "orientação", "supervision"),
                (".cursos", "cursos", "programs"),
                (".banca", "avaliadores", "examiners"),
                (".avaliacao", "link avaliação", "evaluation link"),
                (".agendamento", "agendamento", "schedule"),
                (".email", "e-mail", "e-mail"),
                (".editar", "editar", "edit"),
                (".sem_agendamento", "sem agendamento", "without schedule"),
            ]
        context["edicoes"] = get_edicoes(Projeto)[0]

        if edicao:
            if '.' in edicao:
                context["selecionada_edicao"] = edicao
            elif edicao != "proximas" and edicao != "todas":
                context["projeto"] = get_object_or_404(Projeto, id=edicao)

    return render(request, "professores/bancas_lista.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mensagem_email(request, tipo=None, primarykey=None):
    """Envia mensagens."""

    if primarykey is None:
        return HttpResponseNotFound("<h1>Erro!</h1>")

    # Envia mensagem diretamente
    if request.is_ajax() and request.method == "POST":

        mensagem = ""
        if "assunto" in request.POST and "para" in request.POST and "mensagem" in request.POST:
            assunto = request.POST["assunto"]
            para = request.POST["para"]
            mensagem = request.POST["mensagem"]
        else:
            return HttpResponse("Envio não realizado.", status=401)

        recipient_list = para.split(';')
        configuracao = get_object_or_404(Configuracao)
        recipient_list.append(configuracao.coordenacao.user.email)

        email(assunto, recipient_list, mensagem)

        context = {
                "atualizado": True,
                "mensagem": mensagem,
            }
        return JsonResponse(context)
    
    subject, para, message = prepara_mensagem_email(request, tipo, primarykey)

    context = {
        "assunto": subject,
        "para": para,
        "mensagem": message,
        "url": request.get_full_path(),
    }
    return render(request, "professores/mensagem_email.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mentorias_alocadas(request):
    """Mostra detalhes sobre o professor."""
    mentorias = Encontro.objects.exclude(endDate__lt=datetime.date.today(), projeto__isnull=True)
    mentorias = mentorias.filter(facilitador=request.user).order_by("-projeto__ano", "-projeto__semestre", "startDate")
    context = {
        "titulo": {"pt": "Mentorias Facilitadas", "en": "Facilitated Mentoring"},
        "mentorias": mentorias,
        }
    return render(request, "professores/mentorias_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mentorias_tabela(request):
    """Lista todas as mentorias agendadas, conforme periodo pedido."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                mentorias = Encontro.objects.all()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    mentorias = Encontro.objects.filter(projeto__ano=ano)
                else:
                    mentorias = Encontro.objects.filter(projeto__ano=ano).filter(projeto__semestre=semestre)

            mentores = dict()
            for mentoria in mentorias.filter(projeto__isnull=False):
                mentores.setdefault(mentoria.facilitador, []).append(mentoria)

        cabecalhos = [{"pt": "Nome", "en": "Name"},
                      {"pt": "e-mail", "en": "e-mail"},
                      {"pt": "Grupos", "en": "Groups"},
                      {"pt": "Projetos", "en": "Projects"}]

        context = {
            "cabecalhos": cabecalhos,
            "mentores": mentores,
            }

    else:
        edicoes = get_edicoes(Projeto, anual=True)[0]
        context = {
            "titulo": { "pt": "Alocação em Mentorias", "en": "Mentoring Allocation" },
            "edicoes": edicoes,
            }

    return render(request, "professores/mentorias_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def orientacoes_alocadas(request):
    """Mostra detalhes sobre o professor."""
    context = {
        "titulo": {"pt": "Projetos Orientados", "en": "Projects Oriented"},
        "projetos": Projeto.objects.filter(orientador=request.user.professor).order_by("-ano", "-semestre"),
        }
    return render(request, "professores/orientacoes_alocadas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
@transaction.atomic
def entrega_avaliar(request, composicao_id, projeto_id, estudante_id=None):
    """Cria uma tela para preencher avaliações de entregas."""
    
    projeto = Projeto.objects.get(pk=projeto_id)
    if request.user != projeto.orientador.user and request.user.tipo_de_usuario != 4:
        return HttpResponseNotFound("<h1>Você não é o orientador desse projeto!</h1>")

    composicao = Composicao.objects.get(pk=composicao_id)

    estudante = None
    if estudante_id:
        estudante = PFEUser.objects.get(pk=estudante_id)
        if estudante.tipo_de_usuario != 1:
            return HttpResponseNotFound("<h1>Pessoa avaliada não é estudante!</h1>")
        alocacao = Alocacao.objects.get(projeto=projeto, aluno=estudante.aluno)

    objetivos = composicao.pesos.all()
    pesos = Peso.objects.filter(composicao=composicao)
    
    editor = request.user == projeto.orientador.user
    
    if request.method == "POST":

        objetivos_possiveis = 0
        
        if objetivos:
            objetivos_possiveis = len(objetivos)
            julgamento = [None]*objetivos_possiveis
            
            avaliacoes = dict(filter(lambda elem: elem[0][:9] == "objetivo.", request.POST.items()))

            nova_avaliacao = True
            for i, aval in enumerate(avaliacoes):

                obj_nota = request.POST[aval]
                conceito = obj_nota.split('.')[1]
                
                pk_objetivo = int(obj_nota.split('.')[0])
                objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=pk_objetivo)

                if composicao.exame.grupo:
                    avaliacao, nova_avaliacao = Avaliacao2.objects.get_or_create(projeto=projeto, 
                                                                                 exame=composicao.exame, 
                                                                                 objetivo=objetivo,
                                                                                 avaliador=request.user)
                else:
                    if not estudante or not alocacao:
                        return HttpResponseNotFound("<h1>Estudante não encontrado!</h1>")
                    avaliacao, nova_avaliacao = Avaliacao2.objects.get_or_create(projeto=projeto, 
                                                                                 exame=composicao.exame, 
                                                                                 objetivo=objetivo,
                                                                                 avaliador=request.user,
                                                                                 alocacao=alocacao)

                julgamento[i] = avaliacao

                if conceito == "NA":
                    julgamento[i].na = True
                else:
                    julgamento[i].nota = converte_conceito(conceito)
                    julgamento[i].peso = Peso.objects.get(composicao=composicao, objetivo=objetivo).peso
                    julgamento[i].na = False
                
                julgamento[i].momento = datetime.datetime.now()
                julgamento[i].save()

        else:
            julgamento = [None]
            avaliacao, nova_avaliacao = Avaliacao2.objects.get_or_create(projeto=projeto, 
                                                                    exame=composicao.exame, 
                                                                    objetivo=None,
                                                                    avaliador=request.user)
            julgamento[0] = avaliacao

            if "decisao" in request.POST:
                if request.POST["decisao"] == "1":
                    avaliacao.nota = 10
                else:
                    avaliacao.nota = 1  # Zero é um problema pois pode ser confundido com não avaliado
                avaliacao.peso = 0

            avaliacao.momento = datetime.datetime.now()
            avaliacao.save()


        julgamento_observacoes = None
        if ("observacoes_orientador" in request.POST and request.POST["observacoes_orientador"] != "") or \
           ("observacoes_estudantes" in request.POST and request.POST["observacoes_estudantes"] != ""):
            
            if composicao.exame.grupo:
                observacao, _ = Observacao.objects.get_or_create(projeto=projeto,
                                                                        exame=composicao.exame,
                                                                        avaliador=request.user)
            else:
                if not estudante or not alocacao:
                    return HttpResponseNotFound('<h1>Estudante não encontrado!</h1>')
                observacao, _ = Observacao.objects.get_or_create(projeto=projeto,
                                                                        exame=composicao.exame,
                                                                        avaliador=request.user,
                                                                        alocacao=alocacao)

            julgamento_observacoes = observacao
            julgamento_observacoes.observacoes_orientador = request.POST.get("observacoes_orientador")
            julgamento_observacoes.observacoes_estudantes = request.POST.get("observacoes_estudantes")
            julgamento_observacoes.momento = datetime.datetime.now()
            julgamento_observacoes.save()


        if "arquivo" in request.FILES:
            # Envia documento com anotações para os envolvidos intantanemente
            documento = cria_material_documento(request, "arquivo", sigla="RAO", confidencial=False,
                                                projeto=projeto, usuario=request.user,
                                                prefix="rev_"+str(request.user.first_name)+"_"+str(composicao.exame.sigla)+"_")
            if documento:
                documento.anotacao = composicao.exame.titulo
                documento.save()
                subject = "Capstone | Documento com anotações - " + composicao.exame.titulo + " "
                subject += projeto.get_titulo_org()
                mensagem_anot = "Anotações em Relatório<br>\n<br>\n"
                mensagem_anot += "Anotações realizadas por: " + request.user.get_full_name() + "<br>\n"
                mensagem_anot += "Exame: " + composicao.exame.titulo + "<br>\n"
                mensagem_anot += "Projeto: " + projeto.get_titulo_org() + "<br>\n"
                mensagem_anot += "Data: " + str(datetime.datetime.now()) + "<br>\n<br>\n<br>\n"
                mensagem_anot += "Documento com Anotações: "
                mensagem_anot += "<a href='" + request.scheme + "://" + request.get_host() + documento.documento.url + "' target='_blank' rel='noopener noreferrer'>"
                mensagem_anot += request.scheme + "://" + request.get_host() + documento.documento.url + "</a><br>\n<br>\n<br>\n"
                recipient_list = [alocacao.aluno.user.email for alocacao in projeto.alocacao_set.all()]
                recipient_list.append(request.user.email)
                # recipient_list.append(projeto.orientador.user.email)
                # recipient_list.append(configuracao.coordenacao.user.email)
                email(subject, recipient_list, mensagem_anot)


        resposta = {"pt": "Avaliação concluída com sucesso.<br>", 
                   "en": "Evaluation completed successfully.<br>"}

        envia = "envia" in request.POST
        if envia:
            subject = "Capstone | Resultado da Avaliação (" + composicao.exame.titulo + ") " + projeto.get_titulo_org()
            
            # Mensagem preparada para os estudantes
            context_carta = {
                "projeto": projeto,
                "composicao": composicao,
                "julgamento": julgamento,
                "julgamento_observacoes": julgamento_observacoes,
                "objetivos_possiveis": objetivos_possiveis,
                "individual": not composicao.exame.grupo,
            }
            message = render_message("Resultado Estudantes", context_carta)
        
            # O Orientador e o(s) Estudante(s) serão notificados
            recipient_list = [projeto.orientador.user.email,]
            if estudante:
                recipient_list.append(estudante.email)
            else:
                alocacoes = Alocacao.objects.filter(projeto=projeto)
                for alocacao in alocacoes:
                    recipient_list.append(alocacao.aluno.user.email)

            email(subject, recipient_list, message)
            resposta["pt"] += "<br>Enviada mensagem por e-mail notificando estudantes dos conceitos definidos<br>"
            resposta["en"] += "<br>Sent message by e-mail notifying students of the defined concepts<br>"
        
        if request.user.eh_prof_a:
            request.user.professor.email_avaliacao = envia
            request.user.professor.save()
        
        if not nova_avaliacao:
            resposta["pt"] += "<br><br><h2>Essa é uma atualização de uma avaliação já enviada anteriormente!</h2><br><br>"
            resposta["en"] += "<br><br><h2>This is an update of an evaluation already sent before!</h2><br><br>"
        
        context = {
            "area_principal": True,
            "avaliar_entregas": True,
            "mensagem": resposta,
        }
        return render(request, "generic_ml.html", context=context)

    else:  # Não é POST

        if estudante and (not composicao.exame.grupo):
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento, projeto=projeto, usuario=estudante)
        else:
            documentos = Documento.objects.filter(tipo_documento=composicao.tipo_documento, projeto=projeto)

        evento = Evento.get_evento(tipo=composicao.tipo_evento, ano=projeto.ano, semestre=projeto.semestre)

        if composicao.exame.grupo:
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                exame=composicao.exame, 
                                                avaliador=projeto.orientador.user
                                                )
        else:
            if not estudante or not alocacao:
                return HttpResponseNotFound("<h1>Estudante não encontrado!</h1>")
            avaliacoes = Avaliacao2.objects.filter(projeto=projeto, 
                                                exame=composicao.exame, 
                                                avaliador=projeto.orientador.user,
                                                alocacao=alocacao
                                                )

        conceitos = []
        avaliacao = None
        for i in range(len(avaliacoes)):
            if avaliacoes[i].objetivo:
                tmp_objetivo = avaliacoes[i].objetivo.pk
                tmp_conceito = converte_letra(avaliacoes[i].nota, mais="X")
                conceitos.append( (tmp_objetivo, tmp_conceito) )
            else:
                avaliacao = avaliacoes[i].nota

        if composicao.exame.grupo:
            observacao = Observacao.objects.filter(projeto=projeto, exame=composicao.exame,
                                                    avaliador=projeto.orientador.user).last()
        else:
            if not estudante or not alocacao:
                return HttpResponseNotFound("<h1>Estudante não encontrado!</h1>")
            observacao = Observacao.objects.filter(projeto=projeto, exame=composicao.exame,
                                                    avaliador=projeto.orientador.user, alocacao=alocacao).last()

        hoje = datetime.datetime.now()

        primeiro_documento = documentos.first()  # primeiro é o último entregue por data
        atrasado = hoje.date() > evento.endDate  # USADO PARA BLOQUEAR NOTAS EM OBJETIVOS DE APRENDIZAGEM
        sem_documentos = False
        if atrasado:
            if primeiro_documento:
                if primeiro_documento.data and primeiro_documento.data.date() <= evento.endDate:
                    atrasado = False
            else:
                sem_documentos = True  # Documentos já deveriam ter sido entregues
            
        
        niveis_objetivos = Estrutura.loads(nome="Níveis de Objetivos")

        relatorio_revisado_orientador = Documento.objects.filter(projeto=projeto, tipo_documento__sigla="RAO").last()

        context = {
            "titulo": {"pt": "Formulário de Avaliação de Entrega", "en": "Delivery Evaluation Form"},
            "projeto": projeto,
            "composicao": composicao,
            "estudante": estudante,
            "documentos": documentos,
            "evento": evento,
            "periodo_para_rubricas": composicao.exame.periodo_para_rubricas,
            "pesos": pesos,
            "today": hoje,
            "conceitos": conceitos,
            "observacao": observacao,
            "editor": editor,
            "avaliacao": avaliacao,
            "atrasado": atrasado,
            "sem_documentos": sem_documentos,
            "niveis_objetivos": niveis_objetivos,
            "relatorio_revisado_orientador": relatorio_revisado_orientador,
        }
    
        return render(request, "professores/entrega_avaliar.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def informe_bancas(request, sigla):
    """Avisa todos os orientadores dos resultados das Bancas Intermediárias."""

    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    bancas = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre, composicao__exame__sigla=sigla)
    administracao = request.user.eh_admin

    if administracao and request.method == "POST":

        for banca in bancas:
            # Envio de mensagem para Orientador / Coordenação
            message = mensagem_orientador(banca, geral=True)
            subject = "Capstone | Resultado Geral da Avaliação de Banca: {0}".format(banca.projeto)
            recipient_list = [banca.projeto.orientador.user.email, ]
            email(subject, recipient_list, message)

        resposta = {"pt": "Informe enviado para:<br>", 
                   "en": "Report sent to:<br>"}

        for banca in bancas:
            resposta["pt"] += "&bull; {0} - banca do dia: {1}<br>".format(banca.projeto.orientador, banca.startDate)
            resposta["en"] += "&bull; {0} - board on: {1}<br>".format(banca.projeto.orientador, banca.startDate)

        context = {
            "area_principal": True,
            "mensagem": resposta,
        }

        return render(request, "generic_ml.html", context=context)

    mensagem_aviso = None
    if not administracao:
        mensagem_aviso = {"pt": "Apenas administradores podem enviar o informe!", "en": "Only administrators can send the report!"}
        
    context = {
        "titulo": {"pt": "Informe de Bancas Finais" if sigla=="BF" else "Informe de Bancas Intermediárias",
                   "en": "Final Examination Boards Report" if sigla=="BF" else "Intermediate Examination Boards Report"},
        "bancas": bancas,
        "administracao": administracao,
        "mensagem_aviso": mensagem_aviso,
    }
    return render(request, "professores/informe_bancas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_bancas(request):
    """Visualiza os resultados das bancas."""

    projeto_id = request.GET.get("projeto", None)
    banca_id = request.GET.get("banca", None)
    if projeto_id:
        projeto = Projeto.objects.get(pk=projeto_id)
        bancas = Banca.objects.filter(projeto=projeto_id)
    elif banca_id:
        bancas = Banca.objects.filter(pk=banca_id)
        projeto = bancas.last().get_projeto()
    else:
        return HttpResponseNotFound("<h1>Bancas não encontradas!</h1>")

    base_url = reverse("resultado_bancas")
    endpoints = [
        {"path": f"{base_url}?projeto={{valor}}", "method": "GET", "description": "Filtra projetos pelo ID do projeto. Exemplo: projeto=1"},
        {"path": f"{base_url}?banca={{valor}}", "method": "GET", "description": "Filtra projetos pelo ID da banca. Exemplo: banca=1"}
    ]

    context = {
        "titulo": {"pt": "Resultado Bancas", "en": "Examination Boards Result"},
        "objetivos": ObjetivosDeAprendizagem.objects.all(),
        "bancas": bancas,
        "projeto": projeto,
        "endpoints": json.dumps(endpoints),
    }
    return render(request, "professores/resultado_bancas.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_criar(request, data=None):
    """Cria um encontro."""
    configuracao = get_object_or_404(Configuracao)
    
    if request.is_ajax() and request.method == "POST":

        mensagem = ""
        if "criar" in request.POST:

            if ("inicio" in request.POST) and ("fim" in request.POST):

                try:
                    startDate = dateutil.parser.parse(request.POST["inicio"])
                    endDate = dateutil.parser.parse(request.POST["fim"])
                    diferenca = endDate - startDate
                except (ValueError, OverflowError):
                    return HttpResponse("Erro com data da Dinâmica!")

                vezes = int(request.POST["vezes"])
                intervalo = int(request.POST["intervalo"])
                local = request.POST.get("local", None)
                tematica_id = request.POST.get("tematica", None)
                if tematica_id:
                    try:
                        tematica = TematicaEncontro.objects.get(id=tematica_id)
                    except TematicaEncontro.DoesNotExist:
                        return HttpResponse("Temática não encontrada.", status=401)
                projeto_id = request.POST.get("projeto", None)
                if projeto_id and projeto_id != "0":
                    try:
                        projeto = Projeto.objects.get(id=projeto_id)
                    except Projeto.DoesNotExist:
                        return HttpResponse("Projeto não encontrado.", status=401)
                else:
                    projeto = None
                facilitador_id = request.POST.get("facilitador", None)
                if facilitador_id and facilitador_id != "0":
                    try:
                        facilitador = PFEUser.objects.get(id=facilitador_id)
                    except PFEUser.DoesNotExist:
                        return HttpResponse("Facilitador não encontrado.", status=401)
                else:
                    facilitador = None
                        
                for vez in range(vezes):

                    encontro = Encontro(startDate=startDate, endDate=endDate)

                    startDate += diferenca +  datetime.timedelta(minutes=intervalo)
                    endDate += diferenca +  datetime.timedelta(minutes=intervalo)

                    if tematica_id:
                        try:
                            encontro.tematica = TematicaEncontro.objects.get(id=tematica_id)
                        except TematicaEncontro.DoesNotExist:
                            return HttpResponse("Temática não encontrada.", status=401)

                    if local:
                        encontro.location = local

                    if projeto:
                        encontro.projeto = projeto
                        
                    if facilitador:
                        encontro.facilitador = facilitador

                    encontro.save()

                    if "enviar_mensagem" in request.POST:
                        if encontro.projeto or encontro.facilitador:
                            subject = "Capstone | Dinâmica agendada"
                            recipient_list = []
                            alocacoes = Alocacao.objects.filter(projeto=encontro.projeto)
                            for alocacao in alocacoes:
                                recipient_list.append(alocacao.aluno.user.email)
                            if encontro.facilitador:
                                recipient_list.append(encontro.facilitador.email)
                            recipient_list.append(str(configuracao.coordenacao.user.email))
                            message = message_agendamento_dinamica(encontro, False) # Atualizada
                            email(subject, recipient_list, message)

                if vezes > 1:
                    mensagem = "Dinâmicas criadas."
                else:
                    mensagem = "Dinâmica criada."
            else:
                return HttpResponse("Dinâmica não registrada, erro!", status=401)

        # else Atualização não realizada.

        context = {
            "atualizado": True,
            "mensagem": mensagem,
        }
        return JsonResponse(context)

    context = {
        "projetos": Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre),
        "professores": PFEUser.objects.filter(tipo_de_usuario__in=[2,4]),  # 'professor' ou 'administrador'
        "falconis": PFEUser.objects.filter(parceiro__organizacao__sigla="Falconi"),
        "url": request.get_full_path(),
        "root_page_url": request.session.get("root_page_url", '/'),
        "Encontro": Encontro,
        "tematicas": TematicaEncontro.objects.all().order_by("nome"),
    }

    if data:
        context["data"] = data

    return render(request, "professores/dinamicas_view.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_editar(request, primarykey=None):
    """Edita um encontro."""

    encontro = Encontro.objects.filter(pk=primarykey).first()

    if encontro is None or primarykey is None:
        if "desbloquear" in request.POST:
            #return None # Encontro foi excluído
            context = {
                "atualizado": True,
                "mensagem": "Encontro não encontrado, pode ter sido excluído.",
            }
            return JsonResponse(context)
        else:
            return HttpResponseNotFound('<h1>Erro na busca de encontro!</h1>')

    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax() and request.method == "POST":
        encontro.bloqueado = False  # Desbloqueia o encontro
        encontro.save()

        mensagem = ""
        if "atualizar" in request.POST:
            
            if ("inicio" in request.POST) and ("fim" in request.POST):

                projeto_antigo = None
                facilitador_antigo = None
                projeto_id = request.POST.get("projeto")
                if projeto_id:
                    projeto_novo = get_object_or_404(Projeto, id=projeto_id) if projeto_id != '0' else None
                    if encontro.projeto and projeto_novo != encontro.projeto:
                        projeto_antigo = encontro.projeto
                    encontro.projeto = projeto_novo
                facilitador_id = request.POST.get("facilitador")
                if facilitador_id:
                    facilitador_novo = get_object_or_404(PFEUser, id=facilitador_id) if facilitador_id != '0' else None
                    if encontro.facilitador and facilitador_novo != encontro.facilitador:
                        facilitador_antigo = encontro.facilitador
                    encontro.facilitador = facilitador_novo
                encontro.save()

                if "enviar_mensagem" in request.POST:
                    if projeto_antigo or facilitador_antigo:
                        subject = "Capstone | Dinâmica cancelada"
                        recipient_list = []
                        if projeto_antigo:
                            alocacoes = Alocacao.objects.filter(projeto=projeto_antigo)
                            for alocacao in alocacoes:
                                recipient_list.append(alocacao.aluno.user.email)
                        if facilitador_antigo:
                            recipient_list.append(facilitador_antigo.email)
                        recipient_list.append(str(configuracao.coordenacao.user.email))
                        message = message_agendamento_dinamica(encontro, encontro.startDate)
                        email(subject, recipient_list, message)

                cancelado = None
                try:
                    startDate_novo = datetime.datetime.strptime(request.POST["inicio"], "%Y-%m-%dT%H:%M")
                    endDate_novo = datetime.datetime.strptime(request.POST["fim"], "%Y-%m-%dT%H:%M")
                    if encontro.startDate != startDate_novo or encontro.endDate != endDate_novo:
                        cancelado = "dia " + str(encontro.startDate.strftime("%d/%m/%Y")) + " das " + str(encontro.startDate.strftime("%H:%M")) + ' às ' + str(encontro.endDate.strftime("%H:%M"))
                    encontro.startDate = startDate_novo
                    encontro.endDate = endDate_novo

                    encontro.location = request.POST.get("local")
                    tematica_id = request.POST.get("tematica", None)
                    if tematica_id:
                        try:
                            encontro.tematica = TematicaEncontro.objects.get(id=tematica_id)
                        except TematicaEncontro.DoesNotExist:
                            return HttpResponse("Temática não encontrada.", status=401)
                    
                except (ValueError, OverflowError):
                    return HttpResponse("Erro com data da Dinâmica!", status=401)
                encontro.save()

                if "enviar_mensagem" in request.POST:
                    if encontro.projeto or encontro.facilitador:
                        subject = "Capstone | Dinâmica agendada"
                        recipient_list = []
                        if encontro.projeto:
                            alocacoes = Alocacao.objects.filter(projeto=encontro.projeto)
                            for alocacao in alocacoes:
                                recipient_list.append(alocacao.aluno.user.email)
                        if encontro.facilitador:
                            recipient_list.append(encontro.facilitador.email)
                        recipient_list.append(str(configuracao.coordenacao.user.email))
                        message = message_agendamento_dinamica(encontro, cancelado) # Atualizada
                        email(subject, recipient_list, message)

                mensagem = "Dinâmica atualizada."
                
            else:
                return HttpResponse("Dinâmica não atualizada, erro!", status=401)

        elif "excluir" in request.POST:
            mensagem = "Mentoria excluída!"

            if "enviar_mensagem" in request.POST:
                subject = "Capstone | Dinâmica cancelada"
                recipient_list = []
                if encontro.projeto:
                    alocacoes = Alocacao.objects.filter(projeto=encontro.projeto)
                    for alocacao in alocacoes:
                        recipient_list.append(alocacao.aluno.user.email)
                if encontro.facilitador:
                    recipient_list.append(encontro.facilitador.email)
                recipient_list.append(str(configuracao.coordenacao.user.email))
                message = message_agendamento_dinamica(encontro, encontro.startDate) # Cancelada
                email(subject, recipient_list, message)

            encontro.delete()

        # else Atualização não realizada. / Serve para desbloquear agendamento
        context = {
            "atualizado": True,
            "mensagem": mensagem,
        }
        return JsonResponse(context)
    
    else:  # Não é POST (e GET)
        encontro.bloqueado = True  # Bloqueia para evitar edição concorrente
        encontro.save()

    context = {
        "projetos": Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre),
        "professores": PFEUser.objects.filter(tipo_de_usuario__in=[2,4]),  # 'professor' ou 'administrador'
        "falconis": PFEUser.objects.filter(parceiro__organizacao__sigla="Falconi"),
        "encontro": encontro,
        "url": request.get_full_path(),
        "root_page_url": request.session.get("root_page_url", '/'),
        "Encontro": Encontro,
        "tematicas": TematicaEncontro.objects.all().order_by("nome"),
    }
    return render(request, "professores/dinamicas_view.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def dinamicas_editar_edicao(request, edicao):
    """Edita vários encontros."""
    
    if request.is_ajax() and request.method == "POST":
        encontros = puxa_encontros(edicao)
        for encontro in encontros:
            encontro.location = request.POST.get("local")
            encontro.tematica = request.POST.get("tematica")
            facilitador_id = request.POST.get("facilitador")
            if facilitador_id:
                encontro.facilitador = get_object_or_404(PFEUser, id=facilitador_id) if facilitador_id != '0' else None
            encontro.save()

        context = {"atualizado": True,}
        return JsonResponse(context)
    
    context = {
        "professores": PFEUser.objects.filter(tipo_de_usuario__in=[2,4]),  # 'professor' ou 'administrador'
        "falconis": PFEUser.objects.filter(parceiro__organizacao__sigla="Falconi"),
        "todas": True,
        "url": request.get_full_path(),
        "root_page_url": request.session.get("root_page_url", '/'),
        "Encontro": Encontro,
        "tematicas": TematicaEncontro.objects.all().order_by("nome"),
    }
    return render(request, "professores/dinamicas_view.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def orientadores_tabela_completa(request):
    """Alocação dos Orientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)
    orientadores = recupera_orientadores_por_semestre(configuracao)

    cabecalhos = [{"pt": "Nome", "en": "Name"},
                  {"pt": "Grupos", "en": "Groups"},]
    
    context = {
        "titulo": {"pt": "Alocação de Orientadores", "en": "Advisor Allocation"},
        "anos": orientadores,
        "cabecalhos": cabecalhos,
        
    }
    return render(request, "professores/orientadores_tabela_completa.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def orientadores_tabela(request):
    """Alocação dos Orientadores por semestre."""
    #configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            professores_pfe = Professor.objects.all().order_by(Lower("user__first_name"),
                                                               Lower("user__last_name"))

            professores = []

            if edicao == "todas":
                professores_pfe = professores_pfe.filter(professor_orientador__isnull=False).distinct()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    professores_pfe = professores_pfe.filter(professor_orientador__ano=ano).distinct()
                else:
                    professores_pfe = professores_pfe.filter(professor_orientador__ano=ano,
                                                             professor_orientador__semestre=semestre).distinct()

            professores = professores_pfe

            grupos = []

            for professor in professores:

                grupos_pfe = Projeto.objects.filter(orientador=professor)

                if edicao != "todas":
                    if semestre == "1/2":
                        grupos_pfe = grupos_pfe.filter(ano=ano)
                    else:
                        grupos_pfe = grupos_pfe.filter(ano=ano).\
                                                filter(semestre=semestre)


                grupos.append(grupos_pfe)

            orientacoes = zip(professores, grupos)

        cabecalhos = [{"pt": "Nome", "en": "Name"},
                      {"pt": "Tipo", "en": "Type"},
                      {"pt": "e-mail", "en": "e-mail"},
                      {"pt": "Grupos", "en": "Groups"},
                      {"pt": "Projetos", "en": "Projects"}, ]

        context = {
            "orientacoes": orientacoes,
            "cabecalhos": cabecalhos,
        }

    else:
        
        informacoes = [
            (".semestre", "Semestre", "Semester"),
            (".organizacao", "Organização", "Organization"),
            (".titulo_projeto", "Título do Projeto", "Project Title"),
            (".tamanho_grupo", "Tamanho do Grupo", "Group Size"),
        ]

        context = {
            "edicoes": get_edicoes(Projeto, anual=True)[0],
            "titulo": {"pt": "Alocação de Orientadores", "en": "Advisors Allocation"},
            "informacoes": informacoes,
        }

    return render(request, "professores/orientadores_tabela.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def coorientadores_tabela_completa(request):
    """Alocação dos Coorientadores por semestre."""
    configuracao = get_object_or_404(Configuracao)
    coorientadores_ano = recupera_coorientadores_por_semestre(configuracao)

    cabecalhos = [{"pt": "Nome", "en": "Name"},
                  {"pt": "Grupos", "en": "Groups"},]

    context = {
        "titulo": {"pt": "Alocação de Coorientadores", "en": "Co-Advisor Allocation"},
        "coorientadores_ano": coorientadores_ano,
        "cabecalhos": cabecalhos,
        
    }
    return render(request, "professores/coorientadores_tabela_completa.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def coorientadores_tabela(request):
    """Alocação dos Coorientadores por semestre."""
    
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]

            professores_pfe = Professor.objects.all().order_by(Lower("user__first_name"),
                                                               Lower("user__last_name"))

            professores = []

            if edicao == "todas":
                professores_pfe = professores_pfe.filter(user__coorientador__isnull=False).distinct()
            else:
                ano, semestre = edicao.split('.')
                if semestre == "1/2":
                    professores_pfe = professores_pfe.filter(user__coorientador__projeto__ano=ano).distinct()
                else:
                    professores_pfe = professores_pfe.filter(user__coorientador__projeto__ano=ano,
                                                             user__coorientador__projeto__semestre=semestre).distinct()

            professores = professores_pfe

            grupos = []

            for professor in professores:

                grupos_pfe = Coorientador.objects.filter(usuario=professor.user)

                if edicao != "todas":
                    if semestre == "1/2":
                        grupos_pfe = grupos_pfe.filter(projeto__ano=ano)
                    else:
                        grupos_pfe = grupos_pfe.filter(projeto__ano=ano).\
                                                filter(projeto__semestre=semestre)

                grupos.append(grupos_pfe)

            orientacoes = zip(professores, grupos)
    
        context = {
            "orientacoes": orientacoes,
            "cabecalhos": [{"pt": "Nome", "en": "Name"},
                           {"pt": "Tipo", "en": "Type"},
                           {"pt": "e-mail", "en": "e-mail"},
                           {"pt": "Grupos", "en": "Groups"},
                           {"pt": "Projetos", "en": "Projects"}, ],
            }

    else:
        informacoes = [
            (".semestre", "Semestre", "Semester"),
            (".organizacao", "Organização", "Organization"),
            (".titulo_projeto", "Título do Projeto", "Project Title"),
            (".tamanho_grupo", "Tamanho do Grupo", "Group Size"),
        ]

        context = {
            "titulo": {"pt": "Alocação de Coorientadores", "en": "Co-Advisor Allocation"},
            "edicoes": get_edicoes(Projeto, anual=True)[0],
            "informacoes": informacoes,
        }

    return render(request, "professores/coorientadores_tabela.html", context)


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def pendencias_professores(request):
    """Mostra pendencias dos professores."""
    configuracao = get_object_or_404(Configuracao)
    orientadores_ids = Projeto.objects.filter(ano=configuracao.ano, semestre=configuracao.semestre).values_list("orientador", flat=True)
    orientadores = Professor.objects.filter(id__in=orientadores_ids)
    
    bancas = Banca.objects.filter(projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre)
    membros_banca_ids = {membro.id for banca in bancas for membro in banca.membros()}
    membros_banca = Professor.objects.filter(user__id__in=membros_banca_ids)  

    professores = {}
    for professor in orientadores | membros_banca:
        professores[professor] = ver_pendencias_professor(professor.user, configuracao.ano, configuracao.semestre)

    tipos = [
        ("Planos de Orientação", "planos_de_orientacao"),
        ("Relatos Quinzenais", "relatos_quinzenais"),
        ("Avaliar Entregas", "avaliar_entregas"),
        ("Agendar Bancas", "bancas_index"),
        ("Avaliar Bancas", "avaliar_bancas"),
        ("Avaliações de Pares", "avaliacoes_pares"),
    ]

    context = {
        "titulo": {"pt": "Pendências dos Professores", "en": "Professors Pending Tasks"},
        "professores": professores,
        "tipos": tipos,
        "coordenacao": configuracao.coordenacao,
        }
    
    return render(request, "professores/pendencias_professores.html", context=context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relatos_quinzenais(request, todos=None):
    """Formulários com os projetos e relatos a avaliar do professor orientador."""

    if todos is not None and not request.user.eh_admin:  # Administrador
        return HttpResponse("Acesso negado.", status=401)

    if request.is_ajax():

        if "edicao" in request.POST:

            projetos = Projeto.objects.all()
            if todos == "todos":
                pass
            elif todos is not None:
                professor = get_object_or_404(Professor, pk=todos)
                projetos = projetos.filter(orientador=professor)
            else:
                projetos = projetos.filter(orientador=request.user.professor)

            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = map(int, edicao.split('.'))
                projetos = projetos.filter(ano=ano, semestre=semestre)
            
            alocacoes = []
            for projeto in projetos:
                alocacoes.append(get_alocacoes(projeto))
            
            proj_aloc = zip(projetos, alocacoes)

            context = {
                "administracao": True,
                "proj_aloc": proj_aloc,
                "edicao": edicao,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        configuracao = get_object_or_404(Configuracao)
        context = {
                "titulo": {"pt": "Relatos Quinzenais", "en": "Biweekly Reports"},
                "administracao": True,
                "edicoes": get_edicoes(Relato)[0],
                "selecionada_edicao": f"{configuracao.ano}.{configuracao.semestre}",
            }

    return render(request, "professores/relatos_quinzenais.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
@transaction.atomic
def relato_avaliar(request, projeto_id, evento_id):
    """Cria uma tela para preencher avaliações dos relatos quinzenais."""
    configuracao = get_object_or_404(Configuracao)
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    evento = get_object_or_404(Evento, pk=evento_id)
    
    evento_anterior = Evento.objects.filter(tipo_evento__sigla="RQ", endDate__lt=evento.endDate).order_by("endDate").last()
    
    alocacoes = Alocacao.objects.filter(projeto=projeto, aluno__externo__isnull=True)

    relatos = []
    for alocacao in alocacoes:
        relatos.append(Relato.objects.filter(alocacao=alocacao,
                                    momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                    momento__lte=evento.endDate + datetime.timedelta(days=1)).order_by("momento").last() )
                                    # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão vale começo do dia

    # Só o próprio orientador pode editar uma avaliação
    if projeto.orientador:
        editor = request.user == projeto.orientador.user
    else:
        editor = False

    exame = Exame.objects.get(titulo="Relato Quinzenal")

    if request.method == "POST":

        if editor:

            avaliacoes = dict(filter(lambda elem: elem[0][:3] == "op.", request.POST.items()))
            
            avaliacao_negativa = False
            for aval in avaliacoes:

                relato_id = int(aval.split('.')[1])
                relato = get_object_or_404(Relato, pk=relato_id)

                obj_nota = float(request.POST[aval])  # Seria melhor decimal.
                
                if obj_nota != relato.avaliacao:
                    relato.avaliacao = obj_nota
                    if( -0.5 < obj_nota < 0.5 ): # Para testar se zero (preciso melhorar isso)
                        avaliacao_negativa = True
                    if relato.momento_avaliacao is None:  # Se o relato não tiver sido avaliado ainda
                        relato.momento_avaliacao = datetime.datetime.now()

                feedback = request.POST.get("feedback" + str(relato.id), None)
                if feedback and feedback != "" and feedback != relato.feedback:
                    relato.feedback = feedback

                    # Manda mensagem para estudante
                    corpo_email = f"{relato.alocacao.aluno.user.get_full_name()},<br>\n<br>\n"
                    corpo_email += "&nbsp;&nbsp;&nbsp;&nbsp;Você teve feedbacks do seu relato quinzenal "
                    if projeto.orientador.user.genero == "F":
                        corpo_email += "pela sua orientadora"
                    else:
                        corpo_email += "pelo seu orientador"
                    corpo_email += f" ({projeto.orientador.user.get_full_name()}).<br>\n"
                    corpo_email += "&nbsp;&nbsp;&nbsp;&nbsp;Por favor, observe com muita atenção a fim de melhor entender como você está se saindo no projeto.<br>\n<br>\n"
                    corpo_email += "A percepção do seu desempenho no projeto é: "
                    if relato:
                        if relato.avaliacao > 0:
                            corpo_email += "<b>Adequada</b>"
                        elif relato.avaliacao < 0:
                            pass
                            #corpo_email += "[<small>&#8987;</small> AGUARDANDO ORIENTADOR]"
                        else:
                            corpo_email += "<b>Inadequada</b>"
                    # else:
                    #     corpo_email += "[<small>&#10060;</small> NÃO ENTREGUE POR ESTUDANTE]"
                    corpo_email += "<br>\n<br>\n"
                    corpo_email += "Feedback:<br>\n" 
                    corpo_email += "<b>" + htmlizar(feedback) + "</b><br>\n"
                    email_dest = [relato.alocacao.aluno.user.email, projeto.orientador.user.email]  # configuracao.coordenacao.user.email
                    email("Capstone | Feedback de Relato Quinzenal", email_dest, corpo_email)

                elif feedback != relato.feedback:
                    relato.feedback = None

                relato.save()
                

            observacoes = request.POST.get("observacoes", None)

            if observacoes and observacoes != "":
                (obs, _) = Observacao.objects.get_or_create(projeto=projeto,
                                                                avaliador=request.user,
                                                                momento=evento.endDate,  # data marcada do fim do evento
                                                                exame=exame)  # (200, "Relato Quinzenal"),
                obs.observacoes_orientador = observacoes
                obs.save()
            else:
                obs = Observacao.objects.filter(projeto=projeto,
                                          avaliador=request.user,
                                          momento=evento.endDate,  # data marcada do fim do evento
                                          exame=exame).last()
                if obs:
                    obs.delete()
                

            # Dispara aviso a coordenação caso alguma observação ou estudante com dificuldade
            if avaliacao_negativa and (observacoes != ""):

                email_dest = []
                email_dest.append(str(configuracao.coordenacao.user.email))
                email_dest.append(str(projeto.orientador.user.email))

                # Necessário refazer tabela de relatos e alocacoes para mensagens irem corretas
                relatos = []
                for alocacao in alocacoes:
                    relatos.append(Relato.objects.filter(alocacao=alocacao,
                                                momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                                momento__lte=evento.endDate + datetime.timedelta(days=1)).order_by("momento").last() )
                                                # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão valo começo do dia

                # Manda mensagem para coordenadores
                corpo_email = "<b>-- OBSERVAÇÕES DE ANOTAÇÃO QUINZENAL REALIZADA PELO PROFESSOR --</b><br>\n<br>\n"
                corpo_email += "<b>Projeto:</b> " + projeto.get_titulo() + "<br>\n"
                corpo_email += "<b>Orientador/Coorientador:</b> " + str(request.user) + "<br>\n"
                corpo_email += "<b>Grupo:</b><br>"
                for alocacao, relato in zip(alocacoes, relatos):
                    corpo_email += "&nbsp;&nbsp;&nbsp;&nbsp;\t- " + alocacao.aluno.user.get_full_name() + " (" + alocacao.aluno.get_curso_completo() + ") "
                    if relato:
                        if relato.avaliacao > 0:
                            corpo_email += "[&#x1F44D; Adequado]"
                        elif relato.avaliacao < 0:
                            corpo_email += "[<small>&#8987;</small> AGUARDANDO ORIENTADOR]"
                        else:
                            corpo_email += "[&#x1F44E; Inadequado]"
                    else:
                        corpo_email += "[<small>&#10060;</small> NÃO ENTREGUE POR ESTUDANTE]"
                    corpo_email += "<br>"
                corpo_email += "<hr>"
                corpo_email += "<b>Observações:</b><br>\n" 
                corpo_email += "<div style='padding: 10px; border: 2px solid #DDDDDD;'>" + htmlizar(observacoes) + "</div><br>\n"
                assunto = "Observações de Anotação Quinzenal Realizada pelo orientador"
                email(assunto, email_dest, corpo_email)

            context = {
                "area_principal": True,
                "mensagem": {"pt": "avaliação realizada", "en": "evaluation made"},
            }
            return render(request, "generic_ml.html", context=context)
            
        else:
            return HttpResponseNotFound("<h1>Erro na edição do relato!</h1>")

    else:  # GET

        obs = Observacao.objects.filter(projeto=projeto,
                                        momento__gt=evento_anterior.endDate + datetime.timedelta(days=1),
                                        momento__lte=evento.endDate + datetime.timedelta(days=1),
                                        exame=exame).last()  # (200, "Relato Quinzenal"),
                                        # O datetime.timedelta(days=1) é necessário pois temos de checar passadas 24 horas, senão vale começo do dia
        
        ## Para puxar o respositório informado
        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        repositorios = []
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
                repositorios.append( (projeto, repo_dict) )

        context = {
            "titulo": { "pt": "Avaliar Relato Quinzenal", "en": "Evaluate Biweekly Report" },
            "editor": editor,
            "projeto": projeto,
            "observacoes": obs.observacoes_orientador if obs else None,
            "alocacoes_relatos": zip(alocacoes, relatos),
            "evento": evento,
            "evento_anterior": evento_anterior,
            "Observacao": Observacao,
            "Relato": Relato,
            "ia_feedback": Estrutura.loads(nome="IA Feedback"),
            "repositorios": repositorios,
        }
        return render(request, "professores/relato_avaliar.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def objetivo_editar(request, primarykey):
    """Edita um objetivo de aprendizado."""
    objetivo = get_object_or_404(ObjetivosDeAprendizagem, pk=primarykey)

    if request.method == "POST":
        # if editar_objetivo(objetivo, request):
        #     mensagem = {"pt": "Banca editada.", "en": "Banca edited."}
        # else:
        #     mensagem = {"pt": "Erro ao Editar banca.", "en": "Error editing banca."}
        context = {
            "area_principal": True,
            "bancas_index": True,
        }
        return render(request, "generic_ml.html", context=context)

    context = {
            "titulo": {"pt": "Editar Objetivo de Aprendizagem", "en": "Edit Learning Goal"},
            "objetivo": objetivo,
        }
    return render(request, "professores/objetivo_editar.html", context)


@login_required
@permission_required("projetos.view_objetidosdeaprendizagem", raise_exception=True)
def objetivos_rubricas(request):
    """Exibe os objetivos e rubricas."""
    context = {
        "titulo": {"pt": "Objetivos de Aprendizagem e Rubricas", "en": "Learning Goals and Rubrics"},
        "objetivos": get_objetivos_atuais(),
        "niveis_objetivos": Estrutura.loads(nome="Níveis de Objetivos"),
    }
    return render(request, "professores/objetivos_rubricas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def planos_de_orientacao(request, prof_id=None):
    """Mostra os planos de orientação do professor."""
    if prof_id and request.user.tipo_de_usuario == 4:  # Administrador
        professor = get_object_or_404(Professor, pk=prof_id)
    else:
        professor = request.user.professor

    context = {
        "titulo": {"pt": "Planos de Orientação", "en": "Advising Plans"},
        "projetos": Projeto.objects.filter(orientador=professor).order_by("-ano", "-semestre"),
        "template": Documento.objects.filter(tipo_documento__sigla="TPO").last(),  # Template de Plano de Orientação
        "professor": professor,
    }
    return render(request, "professores/planos_de_orientacao.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def planos_de_orientacao_todos(request):
    """Formulários com os projetos e planos de orientação dos professores orientadores."""
    usuario_sem_acesso(request, (4,)) # Soh Parc Adm

    if request.is_ajax():

        if "edicao" in request.POST:

            projetos = Projeto.objects.all()

            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = edicao.split('.')
                projetos = projetos.filter(ano=ano, semestre=semestre)
                
            context = {
                "administracao": True,
                "projetos": projetos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        context = {
                "titulo": {"pt": "Planos de Orientação", "en": "Orientation Plans"},
                "administracao": True,
                "edicoes": get_edicoes(Projeto)[0],
            }

    return render(request, "professores/planos_de_orientacao_todos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_projetos_edicao(request, edicao):
    """Mostra os resultados das avaliações (Bancas) para uma edição."""
    try:
        ano, semestre = map(int, edicao.split('.'))
    except ValueError:
        return HttpResponseNotFound("<h1>Erro em identificar ano e semestre!</h1>")
    return resultado_projetos_intern(request, ano, semestre)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_projetos(request):
    """Mostra os resultados das avaliações (Bancas)."""
    return resultado_projetos_intern(request)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def resultado_meus_projetos(request):
    """Mostra os resultados das avaliações somente do professor (Bancas)."""
    return resultado_projetos_intern(request, professor=request.user.professor)


@login_required
@permission_required("projetos.view_avaliacao2", raise_exception=True)
def resultado_p_certificacao(request):
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            projetos = Projeto.objects.all()
            if edicao != "todas":
                ano, semestre = map(int, edicao.split('.'))
                projetos = projetos.filter(ano=ano, semestre=semestre)
            else:
                ano, semestre = 0, 0

            recomendacoes = {nome: [] for nome in ["Banca Final", "Banca Intermediária"]}
            notas = {nome: [] for nome in ["Falconi"]}

            for projeto in projetos:
                bi = Banca.objects.filter(projeto=projeto, composicao__exame__sigla="BI").last()
                recomendacoes["Banca Intermediária"].append(bi.get_recomendacao_destaque() if bi else None)
                bf = Banca.objects.filter(projeto=projeto, composicao__exame__sigla="BF").last()
                recomendacoes["Banca Final"].append(bf.get_recomendacao_destaque() if bf else None)

                # Banca Intermediária
                aval_i = Avaliacao2.objects.filter(projeto=projeto, exame__sigla="BI")  # BI

                # Banca Falconi
                aval_b = Avaliacao2.objects.filter(projeto=projeto, exame__sigla="F")  # Falc.
                banca_info = get_banca_estudante(aval_b, ano=projeto.ano, semestre=projeto.semestre)
                nota_b = banca_info["media"]
                peso = banca_info["peso"]
                avaliadores = banca_info["avaliadores"]
                nota_incompleta, banca = get_banca_incompleta(projeto=projeto, sigla="F", avaliadores=avaliadores)

                if peso is not None:
                    certificacao = ""
                    if nota_b >= 8:
                        certificacao = "E"  # Excelencia FALCONI-INSPER
                    elif nota_b >= 6:
                        certificacao = "D"  # Destaque FALCONI-INSPER

                    notas["Falconi"].append({
                                        #"avaliadores": "{0}".format(nomes),
                                        "avaliadores": avaliadores,
                                        "nota_texto": "{0:5.2f}".format(nota_b),
                                        "nota": nota_b,
                                        "certificacao": certificacao,
                                        "nota_incompleta": nota_incompleta,
                                        "banca": banca,
                                        })
                    
                else:
                    notas["Falconi"].append({"avaliadores": None,
                                        "nota_texto": "",
                                        "nota": 0,
                                        "certificacao": "",
                                        "nota_incompleta": nota_incompleta,
                                        "banca": banca,})
                
            tabela = zip(projetos,
                         recomendacoes["Banca Intermediária"],
                         recomendacoes["Banca Final"],
                         notas["Falconi"],
                         )

            context = {
                    "tabela": tabela,
                    "edicao": edicao,
                }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else:
        edicoes = get_edicoes(Projeto)[0]

        configuracao = get_object_or_404(Configuracao)
        selecionada_edicao = "{0}.{1}".format(configuracao.ano, configuracao.semestre)

        try:
            regulamento = Documento.objects.filter(tipo_documento__sigla="RCF").order_by("-data").last()  # Regulamento da Certificação Falconi
        except Documento.DoesNotExist:
            regulamento = None

        informacoes = [
            ("#ProjetosTable tr > *:nth-child(3)", "Período", "Semester"),
            ("#ProjetosTable tr > *:nth-child(4)", "Orientador", "Advisor"),
            ("""#ProjetosTable tr > *:nth-child(5),
                #ProjetosTable tr > *:nth-child(6)""", "Recomendações", "Recommendations"),
            (".grupo", "Grupo", "Group"),
            (".email", "e-mail", "e-mail", "grupo"),
            (".curso", "curso", "program", "grupo"),
        ]

        context = {
            "titulo": {"pt": "Resultado para Certificação", "en": "Certification Results"},
            "edicoes": edicoes,
            "selecionada_edicao": selecionada_edicao,
            "informacoes": informacoes,
            "regulamento": regulamento,
        }

    return render(request, "professores/resultado_p_certificacao.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def todos_professores(request):
    """Exibe todas os professores que estão cadastrados."""
    context = {
            "professores": Professor.objects.all(),
            "cabecalhos": [{ "pt": "Nome", "en": "Name", },
                           { "pt": "e-mail", "en": "e-mail", },
                           { "pt": "Área", "en": "Area", },
                           { "pt": "Bancas", "en": "Examination Boards", },
                           { "pt": "Orientações", "en": "Advising", },
                           { "pt": "Coorientações", "en": "Co-Advising", },
                           { "pt": "Documentos Públicos", "en": "Public Documents", },
                           { "pt": "Lattes", "en": "Lattes", },],
            "titulo": { "pt": "Professores", "en": "Professors", },
        }

    return render(request, "professores/todos_professores.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def ver_pares_projeto(request, projeto_id, momento):
    """Permite visualizar a avaliação de pares."""

    configuracao = get_object_or_404(Configuracao)
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    tipo = 0 if momento=="intermediaria" else 1

    if request.user != projeto.orientador.user and not request.user.eh_admin:
        return HttpResponse("Somente o próprio orientador pode confirmar uma avaliação de pares.", status=401)

    # Marcando que orientador viu avaliação
    editor = False
    if request.user == projeto.orientador.user:
        editor = True
        for alocacao in alocacoes:
            if momento=="intermediaria" and not alocacao.avaliacao_intermediaria:
                alocacao.avaliacao_intermediaria = datetime.datetime.now()
            elif momento=="final" and not alocacao.avaliacao_final:
                alocacao.avaliacao_final = datetime.datetime.now()
            alocacao.save()
        if request.method == "POST":
            for alocacao in alocacoes:
                feedback = request.POST.get("feedback" + str(alocacao.id), None)
                if feedback and feedback != "":
                    feedbackpares = FeedbackPares.objects.get_or_create(alocacao=alocacao, tipo=tipo)[0]
                    if feedback != feedbackpares.feedback:
                        feedbackpares.feedback = feedback
                        feedbackpares.momento = datetime.datetime.now()
                        feedbackpares.save()

                        # Manda mensagem para estudante
                        corpo_email = f"{alocacao.aluno.user.get_full_name()},<br>\n<br>\n"
                        corpo_email += "&nbsp;&nbsp;&nbsp;&nbsp;Você teve feedbacks da sua avaliação de pares "
                        if projeto.orientador.user.genero == "F":
                            corpo_email += "pela sua orientadora"
                        else:
                            corpo_email += "pelo seu orientador"
                        corpo_email += f" ({projeto.orientador.user.get_full_name()}).<br>\n"
                        corpo_email += "&nbsp;&nbsp;&nbsp;&nbsp;Por favor, observe com muita atenção a fim de melhor entender como você está se saindo no projeto.<br>\n<br>\n"
                        corpo_email += "<br>\n<br>\n"
                        corpo_email += "Feedback:<br>\n" 
                        corpo_email += "<b>" + htmlizar(feedback) + "</b><br>\n"
                        email_dest = [alocacao.aluno.user.email, projeto.orientador.user.email] #, configuracao.coordenacao.user.email
                        email("Capstone | Feedback de Avaliação de Pares", email_dest, corpo_email)
                        
                else:
                    feedbackpares = FeedbackPares.objects.filter(alocacao=alocacao, tipo=tipo).last()
                    if feedbackpares:
                        feedbackpares.delete()

            # Mensagem que feedbacks foram enviados
            context = {
                "area_principal": True,
                "mensagem": {"pt": "feedbacks enviados", "en": "feedbacks sent"},
            }
            return render(request, "generic_ml.html", context=context)
            
    verificada = None
    for alocacao in alocacoes:
        if momento=="intermediaria" and not verificada:
            verificada = alocacao.avaliacao_intermediaria
        elif momento=="final" and not verificada:
            verificada = alocacao.avaliacao_final

    colegas = get_pares_colegas(projeto, tipo)
    
    entregas = [resposta[1] for resposta in Pares.TIPO_ENTREGA]
    iniciativas = [resposta[1] for resposta in Pares.TIPO_INICIATIVA]
    comunicacoes = [resposta[1] for resposta in Pares.TIPO_COMUNICACAO]

    context = {
        "titulo": {
            "pt": "Avaliação de Pares " + ("Intermediária" if momento=="intermediaria" else "Final"),
            "en": ("Intermediate" if momento=="intermediaria" else "Final") + " Peer Evaluation",
            },
        "alocacoes": alocacoes,
        "colegas": colegas,
        "momento": momento,
        "projeto": projeto,
        "msg_aval_pares": get_object_or_404(Carta, sigla="MAP"),
        "entregas": entregas,
        "iniciativas": iniciativas,
        "comunicacoes": comunicacoes,
        "FeedbackPares": FeedbackPares,
        "verificada": verificada,
        "editor": editor,
        "tipo_aval": {
            "pt": "Avaliação de Pares " + ("Intermediária" if momento=="intermediaria" else "Final"),
            "en": ("Intermediate" if momento=="intermediaria" else "Final") + " Peer Evaluation",
            },
    }

    return render(request, "professores/ver_pares_projeto.html", context)

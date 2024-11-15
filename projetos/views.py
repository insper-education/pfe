#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import datetime
import csv
import dateutil.parser
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from users.models import PFEUser, Aluno, Professor, Opcao, Alocacao, Parceiro
from users.support import adianta_semestre, get_edicoes

from operacional.models import Curso

from .models import Projeto, Proposta, Configuracao, Observacao
from .models import Coorientador, Avaliacao2, ObjetivosDeAprendizagem

from .models import Feedback, Acompanhamento, Anotacao, Organizacao
from .models import Documento, FeedbackEstudante
from .models import Banco, Reembolso, Aviso, Conexao
from .models import Area, AreaDeInteresse, Banca

from .messages import email, message_reembolso

from academica.models import Exame

from .support import simple_upload, calcula_objetivos, cap_name, media
from .support import divide57

from .tasks import avisos_do_dia, eventos_do_dia

from administracao.support import usuario_sem_acesso

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_areas_estudantes(alunos):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    usuarios = [aluno.user for aluno in alunos]

    todas_areas = Area.objects.filter(ativa=True)
    areaspfe = {
        area.titulo: (AreaDeInteresse.objects.filter(usuario__in=usuarios, area=area), area.descricao)
        for area in todas_areas
    }

    outras = AreaDeInteresse.objects.filter(usuario__in=usuarios, area__isnull=True)

    return areaspfe, outras

def get_areas_propostas(propostas):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {
        area.titulo: (AreaDeInteresse.objects.filter(proposta__in=propostas, area=area), area.descricao)
        for area in Area.objects.filter(ativa=True)
    }

    outras = AreaDeInteresse.objects.filter(proposta__in=propostas, area__isnull=True)

    return areaspfe, outras


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def index_projetos(request):
    """Página principal dos Projetos."""
    context = {"titulo": "Projetos",}

    if "/projetos/projetos" in request.path:
        return render(request, "projetos/projetos.html", context=context)
    else:
        return render(request, "projetos/index_projetos.html", context=context)


@login_required
def projeto_detalhes(request, primarykey):
    """Exibe proposta de projeto com seus detalhes para estudantes."""
    projeto = get_object_or_404(Projeto, pk=primarykey)

    # Se usuário não for Professor nem Admin
    if request.user and request.user.tipo_de_usuario != 2 and request.user.tipo_de_usuario != 4:
        configuracao = get_object_or_404(Configuracao)
        alocacoes = Alocacao.objects.filter(aluno=request.user.aluno, projeto=projeto)
        
        liberado = True
        if configuracao.semestre == 1:
            liberado1 = projeto.ano < configuracao.ano
            liberado2 = (projeto.ano == configuracao.ano) and (projeto.semestre == configuracao.semestre)
            liberado = liberado1 or liberado2
        else:
            liberado = projeto.ano <= configuracao.ano

        if (not alocacoes) or (not liberado):
            mensagem = "Você não tem autorização para visualizar projeto"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

    titulo = str(projeto.ano) + '.' + str(projeto.semestre)
    if projeto.proposta.organizacao:
        titulo += " [" + projeto.proposta.organizacao.sigla + "] "
    titulo += projeto.get_titulo()

    context = {
        "titulo": titulo,
        "projeto": projeto,
        }

    return render(request, "projetos/projeto_detalhes.html", context=context)


@login_required
def projeto(request, primarykey):
    """Mostra um projeto conforme usuário."""
    if request.user.tipo_de_usuario == 1:
        return redirect("meuprojeto", primarykey=primarykey)
    elif request.user.tipo_de_usuario in (2, 4):
        return redirect("projeto_completo", primarykey=primarykey)
    elif request.user.tipo_de_usuario == 3:
        return redirect("projeto_organizacao", primarykey=primarykey)
    else:
        return HttpResponse("Erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projeto_completo(request, primarykey):
    """Mostra um projeto por completo."""
    projeto = get_object_or_404(Projeto, pk=primarykey)
    alocacoes = Alocacao.objects.filter(projeto=projeto)

    medias_oo = None
    if alocacoes:
        alocacao = alocacoes.first()
        medias_oo = alocacao.get_medias_oo
        if not (medias_oo["medias_apg"] or medias_oo["medias_afg"] or medias_oo["medias_rig"] or medias_oo["medias_bi"] or medias_oo["medias_rfg"] or medias_oo["medias_bf"]):
            medias_oo = None

    titulo = ""
    if projeto.proposta.organizacao:
        titulo += "[" + projeto.proposta.organizacao.sigla + "]"
    titulo += " " + projeto.get_titulo()
    titulo += " " + str(projeto.ano) + '.' + str(projeto.semestre)

    configuracao = get_object_or_404(Configuracao)
    horarios = json.loads(configuracao.horarios_semanais) if configuracao.horarios_semanais else None

    context = {
        "titulo": { "pt": titulo, "en": titulo },
        "projeto": projeto,
        "alocacoes": alocacoes,
        "medias_oo": medias_oo,
        "conexoes": Conexao.objects.filter(projeto=projeto),
        "coorientadores": Coorientador.objects.filter(projeto=projeto),
        "documentos": Documento.objects.filter(projeto=projeto),
        "projetos_avancados": Projeto.objects.filter(avancado=projeto),
        "cooperacoes": Conexao.objects.filter(projeto=projeto, colaboracao=True),
        "horarios": horarios,
    }
    return render(request, "projetos/projeto_completo.html", context=context)


@login_required
@permission_required("projetos.add_proposta", raise_exception=True)
def projeto_organizacao(request, primarykey):
    """Mostra um projeto por completo."""
    
    usuario_sem_acesso(request, (3, 4,)) # Soh Parc Adm

    projeto = get_object_or_404(Projeto, pk=primarykey)
    
    organizacao = None
    if hasattr(request.user, "parceiro"):
        organizacao = request.user.parceiro.organizacao

    if projeto.proposta.organizacao != organizacao and request.user.tipo_de_usuario != 4:
        return HttpResponse("Algum erro não identificado.", status=401)

    context = {
        "projeto": projeto,
        "alocacoes": Alocacao.objects.filter(projeto=projeto),
        "conexoes": Conexao.objects.filter(projeto=projeto),
        "coorientadores": Coorientador.objects.filter(projeto=projeto),
        "documentos": Documento.objects.filter(projeto=projeto, tipo_documento__projeto=True, tipo_documento__individual=False),
        "projetos_avancados": Projeto.objects.filter(avancado=projeto),
        "cooperacoes": Conexao.objects.filter(projeto=projeto, colaboracao=True),
    }
    return render(request, "projetos/projeto_completo.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def distribuicao_areas(request):
    """Distribuição por área de interesse dos alunos/propostas/projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano              # Ano atual
    semestre = configuracao.semestre    # Semestre atual
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    todas = False  # Para mostrar todos os dados de todos os anos e semestres
    tipo = "estudantes"
    curso = "todos"

    if request.is_ajax():
        if "tipo" in request.POST and "edicao" in request.POST:

            tipo = request.POST["tipo"]

            if request.POST["edicao"] == "todas":
                todas = True
            else:
                ano, semestre = request.POST["edicao"].split('.')

            if tipo == "estudantes" and "curso" in request.POST:
                curso = request.POST["curso"]

        else:
            return HttpResponse("Erro não identificado (POST incompleto)", status=401)

        if tipo == "estudantes":
            alunos = Aluno.objects.all()

            if curso != "T":
                alunos = alunos.filter(curso2__sigla_curta=curso)
            
            # Filtra para estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    alunos = alunos.filter(curso2__sigla_curta=curso)
                else:
                    alunos = alunos.filter(curso2__in=cursos_insper)

            if not todas:
                alunos = alunos.filter(anoPFE=ano, semestrePFE=semestre)
            total_preenchido = 0
            for aluno in alunos:
                if AreaDeInteresse.objects.filter(usuario=aluno.user).count() > 0:
                    total_preenchido += 1
            areaspfe, outras = get_areas_estudantes(alunos)
            context = {
                "total": alunos.count(),
                "total_preenchido": total_preenchido,
                "areaspfe": areaspfe,
                "outras": outras,
            }

        elif tipo == "propostas":
            propostas = Proposta.objects.all()
            if not todas:
                propostas = propostas.filter(ano=ano, semestre=semestre)
            areaspfe, outras = get_areas_propostas(propostas)
            context = {
                "total": propostas.count(),
                "areaspfe": areaspfe,
                "outras": outras,
            }

        elif tipo == "projetos":

            projetos = Projeto.objects.all()
            if not todas:
                projetos = projetos.filter(ano=ano, semestre=semestre)

            # Estudar forma melhor de fazer isso
            propostas = [p.proposta.id for p in projetos]
            propostas_projetos = Proposta.objects.filter(id__in=propostas)

            areaspfe, outras = get_areas_propostas(propostas_projetos)

            context = {
                # "titulo": "Tendência de Áreas de Interesse",
                "total": propostas_projetos.count(),
                "areaspfe": areaspfe,
                "outras": outras,
            }

        else:
            return HttpResponse("Erro não identificado (não encontrado tipo)", status=401)

        return render(request, "projetos/distribuicao_areas.html", context)

    edicoes, _, _ = get_edicoes(Aluno)
    context = {
        "titulo": { "pt": "Tendência de Áreas de Interesse", "en": "Trend of Areas of Interest"},
        "edicoes": edicoes,
        "cursos": cursos_insper,
        "cursos_externos": cursos_externos,
    }

    return render(request, "projetos/distribuicao_areas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_fechados(request):
    """Lista todos os projetos fechados."""
    edicoes = []
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.is_ajax():
        if "edicao" in request.POST and "curso" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = edicao.split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

            curso = request.POST["curso"]    
            
            projetos_filtrados = projetos_filtrados.order_by("-avancado", Lower("organizacao__nome"))

            projetos_filtrados = projetos_filtrados.prefetch_related(
                "alocacao_set__aluno__user",
                "alocacao_set__aluno__curso2",
                "proposta",
                "conexao_set"
            )

            projetos_selecionados = []
            prioridade_list = []
            cooperacoes = []
            conexoes = []
            qtd_est = []

            numero_estudantes = 0
            numero_estudantes_avancado = 0
            numero_estudantes_externos = 0

            numero_projetos = 0
            numero_projetos_avancado = 0
            projetos_time_misto = 0

            for projeto in projetos_filtrados:

                estudantes_pfe = Aluno.objects.filter(alocacao__projeto=projeto)

                # Filtra para projetos com estudantes de um curso específico
                if curso != "TE":
                    if curso != 'T':
                        estudantes_pfe = estudantes_pfe.filter(alocacao__aluno__curso2__sigla_curta=curso)
                    else:
                        estudantes_pfe = estudantes_pfe.filter(alocacao__aluno__curso2__in=cursos_insper)

                qtd_est.append(len(estudantes_pfe))
                projetos_selecionados.append(projeto)

                if projeto.avancado:
                    numero_estudantes_avancado += len(estudantes_pfe)
                    numero_projetos_avancado += 1
                else:
                    numero_estudantes += len(estudantes_pfe)
                    numero_projetos += 1

                if projeto.time_misto:
                    projetos_time_misto += 1

                prioridades = []
                for estudante in estudantes_pfe:
                    opcoes = Opcao.objects.filter(proposta=projeto.proposta,
                                                  aluno__user__tipo_de_usuario=1,
                                                  aluno__alocacao__projeto=projeto,
                                                  aluno=estudante)
                    if opcoes:
                        prioridades.append(opcoes.first().prioridade)
                    else:
                        prioridades.append(0)

                    if estudante.externo:
                        numero_estudantes_externos += 1

                prioridade_list.append(zip(estudantes_pfe, prioridades))
                cooperacoes.append(projeto.conexao_set.filter(colaboracao=True))
                conexoes.append(projeto.conexao_set.filter(colaboracao=False))

            projetos = zip(projetos_selecionados, prioridade_list, cooperacoes, conexoes, qtd_est)

            context = {
                "projetos": projetos,
                "numero_projetos": numero_projetos,
                "numero_projetos_avancado": numero_projetos_avancado,
                "numero_estudantes": numero_estudantes,
                "numero_estudantes_avancado": numero_estudantes_avancado,
                "numero_estudantes_externos": numero_estudantes_externos,
                "projetos_time_misto": projetos_time_misto,
                "configuracao": get_object_or_404(Configuracao),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Projeto)
        informacoes = [
            (".logo", "Logo"),
            (".descricao", "Descrição"),
            (".titulo_original", "Título original"),
            (".resumo", "Resumo"),
            (".abstract", "Abstract"),
            (".palavras_chave", "Palavras-chave"),
            (".apresentacao", "Apresentações"),
            (".orientador", "Orientador"),
            (".coorientador", "Coorientador"),
            (".estudantes", "Estudantes"),
            (".curso", "Cursos"),
            (".organizacao", "Organização"),
            (".website", "Website"),
            (".conexoes", "Conexões"),
            (".papeis", "Papéis"),
            (".totais", "Totais"),
            (".emails", "e-mails"),
            (".avancado", "Avancados"),
            (".grafico", "Gráfico", False),
        ]

        context = {
            "titulo": { "pt": "Projetos", "en": "Projects"},
            "edicoes": edicoes,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
            "informacoes": informacoes,
        }

    return render(request, "projetos/projetos_fechados.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_lista(request):
    """Lista todos os projetos."""
    edicoes = []
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = edicao.split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

            avancados = "avancados" in request.POST and request.POST["avancados"]=="true"

            if not avancados:
                projetos_filtrados = projetos_filtrados.filter(avancado__isnull=True)

            projetos = projetos_filtrados.order_by("ano", "semestre", "organizacao")

            cabecalhos = [{ "pt": "Projeto", "en": "Project" },
                          { "pt": "Estudantes", "en": "Students" },
                          { "pt": "Período", "en": "Semester" },
                          { "pt": "Orientador", "en": "Advisor" },
                          { "pt": "Organização", "en": "Sponsor" },]
            context = {
                "projetos": projetos,
                "cabecalhos": cabecalhos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Projeto)
        context = {
            "titulo": { "pt": "Projetos", "en": "Projects"},
            "edicoes": edicoes,
        }

    return render(request, "projetos/projetos_lista.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def bancas_lista(request):
    """Lista todos os projetos."""
    edicoes = []
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                bancas = Banca.objects.all()
            else:
                ano, semestre = edicao.split('.')
                bancas = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

            cabecalhos = [{"pt": "Tipo", "en": "Type"},
                          {"pt": "Data", "en": "Date"},
                          {"pt": "Projeto", "en": "Project"},
                          {"pt": "Avaliadores", "en": "Evaluators"},]
            
            context = {
                "bancas": bancas,
                "cabecalhos": cabecalhos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Projeto)
        context = {
            "titulo": {"pt": "Bancas", "en": "Evaluation Boards"},
            "edicoes": edicoes,
        }

    return render(request, "projetos/bancas_lista.html", context)


@login_required
def meuprojeto(request, primarykey=None):
    """Mostra o projeto do próprio estudante, se for estudante."""
    usuario_sem_acesso(request, (1, 2, 4,)) # Soh Est Parc Adm

    context = {
        "configuracao": get_object_or_404(Configuracao),
        "Projeto": Projeto,
    }
    
    # Caso seja Professor ou Administrador
    if request.user.tipo_de_usuario in (2, 4):
        context["professor"] = request.user.professor

        # Pegando um estudante de um projeto quando orientador
        if primarykey:
            projeto = get_object_or_404(Projeto, pk=primarykey, orientador=request.user.professor)
        else:
            projeto = Projeto.objects.filter(orientador=request.user.professor).last()

        if projeto:
            alocacao = Alocacao.objects.filter(projeto=projeto).last()
        else:
            return HttpResponse("Nenhum projeto encontrado.", status=401)
        
        alocacao = Alocacao.objects.filter(projeto=projeto).last()
        context["aluno"] = alocacao.aluno if alocacao else None
        
    else:
        # Caso seja estudante
        context["aluno"] = request.user.aluno

    if primarykey:
        context["alocados"] = Alocacao.objects.filter(aluno=context["aluno"], projeto__id=primarykey)
    else:
        context["alocados"] = Alocacao.objects.filter(aluno=context["aluno"]).order_by("id")

    if context["alocados"].count() > 1:
        context["titulo"] = { "pt": "Meus Projetos", "en": "My Projects"}
    else:
        context["titulo"] = { "pt": "Meu Projeto", "en": "My Project"}

    return render(request, "projetos/meuprojeto_estudantes.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projeto_avancado(request, primarykey):
    """cria projeto avançado e avança para ele."""
    projeto = Projeto.objects.get(id=primarykey)

    projetos_avancados = Projeto.objects.filter(avancado=projeto)
    if projetos_avancados:
        novo_projeto = projetos_avancados.last()  # só retorna o último
    else:
        novo_projeto = Projeto.objects.get(id=primarykey)
        novo_projeto.pk = None  # Duplica objeto

        configuracao = get_object_or_404(Configuracao)
        ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

        if projeto.titulo_final:
            novo_projeto.titulo_final = projeto.titulo_final

        novo_projeto.avancado = projeto
        novo_projeto.ano = ano
        novo_projeto.semestre = semestre

        novo_projeto.save()

    return redirect("projeto_completo", primarykey=novo_projeto.id)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def carrega_bancos(request):
    """Rotina que carrega arquivo CSV de bancos para base de dados do servidor."""
    with open("projetos/bancos.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                # ('Nome: {}; Código {}'.format(row[0],row[1]))
                banco = Banco.create(nome=row[0], codigo=row[1])
                banco.save()
            line_count += 1
    mensagem = "Bancos carregados."
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, "generic.html", context=context)


@login_required
@transaction.atomic
def reembolso_pedir(request):
    """Página com sistema de pedido de reembolso."""
    configuracao = get_object_or_404(Configuracao)
    usuario = get_object_or_404(PFEUser, pk=request.user.pk)

    if request.user.tipo_de_usuario == 1:
        aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)

        if aluno.anoPFE > configuracao.ano or\
            (aluno.anoPFE == configuracao.ano and aluno.semestrePFE > configuracao.semestre):
            mensagem = "Projetos ainda não disponíveis para o seu período do Capstone."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        projeto = Projeto.objects.filter(alocacao__aluno=aluno).last()
    else:
        projeto = None

    if request.method == "POST":
        reembolso = Reembolso.create(usuario)
        reembolso.descricao = request.POST["descricao"]

        cpf = int(''.join(i for i in request.POST["cpf"] if i.isdigit()))

        reembolso.conta = request.POST["conta"]
        reembolso.agencia = request.POST["agencia"]

        reembolso.banco = get_object_or_404(Banco, codigo=request.POST["banco"])

        reembolso.valor = request.POST["valor"]

        reembolso.save()  # Preciso salvar para pegar o PK
        nota_fiscal = simple_upload(request.FILES["arquivo"],
                                    path="reembolsos/",
                                    prefix=str(reembolso.pk)+"_")
        reembolso.nota = nota_fiscal[len(settings.MEDIA_URL):]

        reembolso.save()

        subject = "Capstone | Reembolso: " + usuario.username
        recipient_list = configuracao.recipient_reembolso.split(";")
        recipient_list.append(usuario.email)  # mandar para o usuário que pediu o reembolso
        if projeto:
            if projeto.orientador:  # mandar para o orientador se houver
                recipient_list.append(projeto.orientador.user.email)
        message = message_reembolso(usuario, projeto, reembolso, cpf)
        check = email(subject, recipient_list, message)
        if check != 1:
            error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message + ", recipient_list=" + str(recipient_list)
            logger.error(error_message)
            message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
            
        return HttpResponse(message)

    bancos = Banco.objects.all().order_by(Lower("nome"), "codigo")
    context = {
        "usuario": usuario,
        "projeto": projeto,
        "bancos": bancos,
        "configuracao": configuracao,
    }
    return render(request, "projetos/reembolso_pedir.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def comite(request):
    """Exibe os professores que estão no comitê do Capstone."""
    context = {
            "professores": Professor.objects.filter(user__membro_comite=True),
            "cabecalhos": [{"pt": "Nome", "en": "Name"}, {"pt": "e-mail", "en": "e-mail"}, {"pt": "Lattes", "en": "Lattes"}, ],
            "titulo": {"pt": "Comitê do Capstone", "en": "Capstone Committee"},
        }
    return render(request, "projetos/comite_pfe.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_feedback(request):
    """Lista todos os feedback das Organizações Parceiras."""
    edicoes, _, _ = get_edicoes(Projeto)
    
    # primeiro ano foi diferente (edição anual em 2018.2)
    num_projetos = [Projeto.objects.filter(ano=2018, semestre=2).count()]
    num_feedbacks = [Feedback.objects.filter(data__range=["2018-06-01", "2019-05-31"]).count()]

    for ano, semestre in [edicao.split('.') for edicao in edicoes[1:]]:
        num_projetos.append(Projeto.objects.filter(ano=ano, semestre=semestre).count())
        if semestre == '1':
            faixa = [ano+"-06-01", ano+"-12-31"]
        else:
            faixa = [str(int(ano)+1)+"-01-01", str(int(ano)+1)+"-05-31"]
        num_feedbacks.append(Feedback.objects.filter(data__range=faixa).count())

    context = {
        "titulo": {"pt": "Feedbacks das Organizações Parceiras", "en": "Feedback from Partner Organizations"},
        "feedbacks": Feedback.objects.all().order_by("-data"),
        "edicoes": edicoes,
        "num_projetos": num_projetos,
        "num_feedbacks": num_feedbacks,
    }
    return render(request, "projetos/lista_feedback.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_feedback_estudantes(request):
    """Lista todos os feedback das Organizações Parceiras."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, _ = get_edicoes(Projeto)

    if request.is_ajax():

        todos_feedbacks = FeedbackEstudante.objects.all().order_by("-momento")

        num_feedbacks = []
        num_estudantes = []

        for ano, semestre in [edicao.split('.') for edicao in edicoes]:
            
            estudantes = Aluno.objects.filter(anoPFE=ano, semestrePFE=semestre).count()
            num_estudantes.append(estudantes)

            numb_feedb = todos_feedbacks.filter(projeto__ano=ano, projeto__semestre=semestre).\
                values("estudante").distinct().count()
            num_feedbacks.append(numb_feedb)

        estudantes = Aluno.objects.all()

        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao != "todas":
                ano, semestre = edicao.split('.')
                estudantes = estudantes.filter(trancado=False, anoPFE=ano, semestrePFE=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        projetos = []
        feedbacks = []
        for estudante in estudantes:

            alocacao = Alocacao.objects.filter(projeto__ano=ano,
                                            projeto__semestre=semestre,
                                            aluno=estudante).last()

            if alocacao:
                projetos.append(alocacao.projeto)

                feedback = todos_feedbacks.filter(projeto=alocacao.projeto,
                                                estudante=estudante).first()

                feedbacks.append(feedback if feedback else None)

            else:
                projetos.append(None)
                feedbacks.append(None)


        alocacoes = zip(estudantes, projetos, feedbacks)

        context = {
            "edicoes": edicoes,
            "num_estudantes": num_estudantes,
            "num_feedbacks": num_feedbacks,
            "alocacoes": alocacoes,
            "coordenacao": configuracao.coordenacao,

            #"cabecalhos": ["Nome", "Projeto", "Data", "Mensagem", ],
            "cabecalhos": [{"pt": "Nome", "en": "Name"}, 
                           {"pt": "Projeto", "en": "Project"}, 
                           {"pt": "Data", "en": "Date"}, 
                           {"pt": "Mensagem", "en": "Message"}, ],
        }

    else:
        context = {
            "titulo": {"pt": "Feedbacks Finais dos Estudantes", "en": "Final Feedback from Students"},
            "edicoes": edicoes,
        }

    return render(request, "projetos/lista_feedback_estudantes.html", context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_acompanhamento(request):
    """Lista todos os acompanhamentos das Organizações Parceiras."""
    context = {
        "titulo": {"pt": "Acompanhamentos nas Organizações", "en": "Organizations Follow-up"},
        "acompanhamentos": Acompanhamento.objects.all().order_by("-data")
        }
    return render(request, "projetos/lista_acompanhamento.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    context = {"feedback": get_object_or_404(Feedback, id=feedback_id)}
    return render(request, "projetos/mostra_feedback.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mostra_feedback_estudante(request, feedback_id):
    """Detalha os feedbacks dos Estudantes."""
    context = {"feedback": get_object_or_404(FeedbackEstudante, id=feedback_id)}
    return render(request, "estudantes/estudante_feedback.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def validate_aviso(request):
    """Ajax para validar avisos."""
    aviso_id = int(request.GET.get("aviso", None)[len("aviso"):])
    checked = request.GET.get("checked", None) == "true"
    value = request.GET.get("value", None)

    aviso = get_object_or_404(Aviso, id=aviso_id)

    datas_realizado = json.loads(aviso.datas_realizado)

    if checked:
        # Marca a data do aviso
        if value not in datas_realizado:
            datas_realizado.append(value)
            aviso.datas_realizado = json.dumps(datas_realizado)
    else:
        # Desmarca a data do aviso
        if value in datas_realizado:
            datas_realizado.remove(value)
            aviso.datas_realizado = json.dumps(datas_realizado)
    aviso.save()
    return JsonResponse({"atualizado": True,})


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_vs_propostas(request):
    """Mostra graficos das evoluções dos projetos e propostas."""
    configuracao = get_object_or_404(Configuracao)
    edicoes = range(2018, configuracao.ano+1)
    edicoes2, _, _ = get_edicoes(Proposta)

    total_org_propostas = {}
    total_org_projetos = {}

    # PROPOSTAS e ORGANIZACOES COM PROPOSTAS
    num_propostas = []
    org_propostas = []
    nome_propostas = []
    for edicao in edicoes2:

        ano_projeto, semestre = edicao.split('.')

        propostas = Proposta.objects.filter(ano=int(ano_projeto)).\
            filter(semestre=semestre)
        nome_propostas.append(propostas)
        num_propostas.append(propostas.count())
        tmp_org = {}
        for projeto in propostas:
            if projeto.organizacao:
                tmp_org[projeto.organizacao.id] = "True"
                total_org_propostas[projeto.organizacao.id] = "True"
        org_propostas.append(len(tmp_org))

    # PROJETOS e ORGANIZACOES COM PROJETOS
    num_projetos = []
    org_projetos = []
    nome_projetos = []
    for edicao in edicoes2:

        ano_projeto, semestre = edicao.split('.')

        projetos = Projeto.objects.filter(ano=int(ano_projeto)).\
            filter(semestre=semestre)
        nome_projetos.append(projetos)
        num_projetos.append(projetos.count())
        tmp_org = {}
        for projeto in projetos:
            if projeto.organizacao:
                tmp_org[projeto.organizacao.id] = "True"
                total_org_projetos[projeto.organizacao.id] = "True"
        org_projetos.append(len(tmp_org))

    # ORGANIZACOES PROSPECTADAS
    org_prospectadas = []
    todas_organizacoes = Organizacao.objects.all()
    for ano_projeto in edicoes:

        # Diferente dos outros, aqui se olha quem foi prospectado no semestre anterior

        # Primeiro Semestre
        count_organizacoes = 0
        for organizacao in todas_organizacoes:
            if Anotacao.objects.filter(organizacao=organizacao,
                                       momento__year=ano_projeto,
                                       momento__month__lt=7).exists():
                count_organizacoes += 1
        org_prospectadas.append(count_organizacoes)

        # Segundo Semeste
        count_organizacoes = 0
        for organizacao in todas_organizacoes:
            if Anotacao.objects.filter(organizacao=organizacao,
                                       momento__year=ano_projeto,
                                       momento__month__gt=6).exists():
                count_organizacoes += 1
        org_prospectadas.append(count_organizacoes)

    context = {
        "titulo": {"pt": "Organizações, Projetos e Propostas", "en": "Organizations, Projects and Proposals"},
        "num_propostas": num_propostas,
        "nome_propostas": nome_propostas,
        "num_projetos": num_projetos,
        "nome_projetos": nome_projetos,
        "total_propostas": sum(num_propostas),
        "total_projetos": sum(num_projetos),
        "org_prospectadas": org_prospectadas,
        "org_propostas": org_propostas,
        "org_projetos": org_projetos,
        "total_org_propostas": len(total_org_propostas),
        "total_org_projetos": len(total_org_projetos),
        "loop_anos": edicoes,
        "edicoes": edicoes2,
    }

    return render(request, "projetos/projetos_vs_propostas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def analise_notas(request):
    """Mostra analise de notas."""
    configuracao = get_object_or_404(Configuracao)
    edicoes = get_edicoes(Avaliacao2)[0]
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.is_ajax():

        periodo = ["todo", "periodo"]
        
        medias_semestre = Alocacao.objects.all()
        edicao = request.POST.get("edicao")
        curso = request.POST.get("curso")

        if edicao and curso:
            if edicao != "todas":
                periodo = edicao.split('.')
                medias_semestre = medias_semestre.filter(projeto__ano=periodo[0],
                                                         projeto__semestre=periodo[1])

            curso = request.POST["curso"]

            # Filtra para projetos com estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    medias_semestre = medias_semestre.filter(aluno__curso2__sigla_curta=curso)
                else:
                    medias_semestre = medias_semestre.filter(aluno__curso2__in=cursos_insper)
                
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        valor = {"ideal": 7.0, "regular": 5.0}

        # Criando espaço para todos as notas
        notas_keys = ["rii", "rig", "bi", "rfi", "rfg", "bf", "rpl", "ppf", "api", "apg", "afg", "afi", "p"]
        notas = {key: {"ideal": 0, "regular": 0, "inferior": 0} for key in notas_keys}

        notas_lista = [x.get_notas for x in medias_semestre]
        for nota2 in notas_lista:
            for nota in nota2:
                if nota[1] is not None:
                    key = nota[0].lower()
                    if key:
                        if nota[1] >= valor["ideal"]:
                            notas[key]["ideal"] += 1
                        elif nota[1] >= valor["regular"]:
                            notas[key]["regular"] += 1
                        else:
                            notas[key]["inferior"] += 1
        medias_lista = [x.get_media for x in medias_semestre]

        # Somente apresenta as médias que esteja completas (pesso = 100%)
        medias_validas = list(filter(lambda d: d["pesos"] == 1.0, medias_lista))

        medias = {}
        medias["ideal"] = len(list(filter(lambda d: d["media"] >= valor["ideal"], medias_validas)))
        medias["regular"] = len(list(filter(lambda d: valor["ideal"] > d["media"] >= valor["regular"], medias_validas)))
        medias["inferior"] = len(list(filter(lambda d: d["media"] < valor["regular"], medias_validas)))
        medias["total"] = len(medias_validas)

        context = {
            "periodo": periodo,
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "loop_anos": edicoes,
            "medias": medias,
            "notas": notas,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "titulo": {"pt": "Análise de Notas/Conceitos", "en": "Analysis of Grades/Concepts"},
            "edicoes": edicoes,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "projetos/analise_notas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def certificacao_falconi(request):
    """Mostra graficos das certificacões Falconi."""
    configuracao = get_object_or_404(Configuracao)

    edicoes, _, _ = get_edicoes(Projeto)

    # cortando ["2018.2", "2019.1", "2019.2", "2020.1", ....]
    edicoes = edicoes[4:]

    if request.is_ajax():

        if "edicao" in request.POST:
            if request.POST["edicao"] != "todas":
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # conceitos = I, D, C, C+, B, B+, A, A+
        conceitos = [0, 0, 0, 0, 0, 0, 0, 0]
        total = len(projetos)
        selecionados = 0
        projetos_selecionados = []
        for projeto in projetos:
            exame = Exame.objects.get(titulo="Falconi")
            aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                          exame=exame)  # Falc.

            if aval_banc_falconi:
                projetos_selecionados.append(projeto)

            nota_banca_falconi, peso, avaliadores = Aluno.get_banca(None, aval_banc_falconi)
            if peso is not None:
                selecionados += 1
                if nota_banca_falconi >= 9.5:  # conceito A+
                    conceitos[7] += 1
                elif nota_banca_falconi >= 9.0:  # conceito A
                    conceitos[6] += 1
                elif nota_banca_falconi >= 8.0:  # conceito B+
                    conceitos[5] += 1
                elif nota_banca_falconi >= 7.0:  # conceito B
                    conceitos[4] += 1
                elif nota_banca_falconi >= 6.0:  # conceito C+
                    conceitos[3] += 1
                elif nota_banca_falconi >= 5.0:  # conceito C
                    conceitos[2] += 1
                elif nota_banca_falconi >= 1.0:  # Qualquer D
                    conceitos[1] += 1
                else:
                    conceitos[0] += 1  # conceito I

        if selecionados:
            for i in range(8):
                conceitos[i] *= 100/selecionados


        # Para as avaliações individuais
        objetivos = ObjetivosDeAprendizagem.objects.all()

        avaliadores = []

        for projeto in projetos_selecionados:

            avaliadores_falconi = {}

            for objetivo in objetivos:

                # Bancas Falconi
                exame = Exame.objects.get(titulo="Falconi")
                bancas_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                        objetivo=objetivo,
                                                        exame=exame)\
                    .order_by("avaliador", "-momento")

                for banca in bancas_falconi:
                    if banca.avaliador not in avaliadores_falconi:
                        avaliadores_falconi[banca.avaliador] = {}
                    if objetivo not in avaliadores_falconi[banca.avaliador]:
                        avaliadores_falconi[banca.avaliador][objetivo] = banca
                        avaliadores_falconi[banca.avaliador]["momento"] = banca.momento
                    # Senão é só uma avaliação de objetivo mais antiga

            # Bancas Falconi
            exame = Exame.objects.get(titulo="Falconi")
            observacoes = Observacao.objects.filter(projeto=projeto, exame=exame).\
                order_by("avaliador", "-momento")
            for observacao in observacoes:
                if observacao.avaliador not in avaliadores_falconi:
                    avaliadores_falconi[observacao.avaliador] = {}  # Não devia acontecer isso
                if "observacoes_orientador" not in avaliadores_falconi[observacao.avaliador]:
                    avaliadores_falconi[observacao.avaliador]["observacoes_orientador"] = observacao.observacoes_orientador
                # Senão é só uma avaliação de objetivo mais antiga

            avaliadores.append(avaliadores_falconi)

        bancas = zip(projetos_selecionados, avaliadores)

        context = {
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "selecionados": selecionados,
            "nao_selecionados": total - selecionados,
            "conceitos": conceitos,
            "projetos_selecionados": projetos_selecionados,
            "objetivos": objetivos,
            "bancas": bancas,
        }

    else:
        context = {
            "titulo": {"pt": "Análise dos Conceitos das Certificações Falconi", "en": "Analysis of Falconi Certifications"},
            "edicoes": edicoes,
        }

    return render(request, "projetos/certificacao_falconi.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def analise_objetivos(request):
    """Mostra análise de objetivos de aprendizagem."""
    edicoes, _, _ = get_edicoes(Avaliacao2)
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.is_ajax():

        alocacoes = Alocacao.objects.all()

        periodo = ["todo", "periodo"]

        if "edicao" in request.POST:
            if request.POST["edicao"] != "todas":
                periodo = request.POST["edicao"].split('.')
                alocacoes = alocacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        if "curso" in request.POST:
            curso = request.POST["curso"]

            # Filtra para alocações de estudantes de um curso específico
            if curso != "TE":
                if curso != 'T':
                    alocacoes = alocacoes.filter(aluno__curso2__sigla_curta=curso)
                else:
                    alocacoes = alocacoes.filter(aluno__curso2__in=cursos_insper)
                
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        context = calcula_objetivos(alocacoes)
        context["edicoes"] = edicoes
        context["total_geral"] = len(alocacoes)
        context["curso"] = curso
        context["periodo"] = periodo

    else:
        context = {
            "titulo": {"pt": "Análise por Objetivos de Aprendizado", "en": "Analysis by Learning Goals"},
            "edicoes": edicoes,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "projetos/analise_objetivos.html", context)

from collections import defaultdict


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_notas(request):
    """Mostra graficos das evoluções das notas."""
    edicoes, _, _ = get_edicoes(Avaliacao2)
    cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")

    if request.is_ajax():

        avaliacoes = Avaliacao2.objects.all()
        alocacoes = Alocacao.objects.all()

        if "curso" in request.POST:
            curso = request.POST["curso"]
            if curso != 'T':
                avaliacoes = avaliacoes.filter(alocacao__aluno__curso2__sigla_curta=curso)
                alocacoes = alocacoes.filter(aluno__curso2__sigla_curta=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # Para armazenar todas as notas de todos os programas
        notas_total = defaultdict(list)

        # Filter avaliacoes for the specific exames
        exames_titulos = ["Relatório Intermediário Individual", "Relatório Final Individual"]
        avaliacoes = avaliacoes.filter(exame__titulo__in=exames_titulos)

        medias_individuais = []

        for t_curso in cursos:
            notas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
                notas_lista = [x.nota for x in semestre if x.alocacao and x.alocacao.aluno.curso2 == t_curso]
                notas_total[edicao].extend(notas_lista)
                notas.append(media(notas_lista))
            
            if any(nota is not None for nota in notas):  # Check if notas is not empty
                medias_individuais.append({"curso": t_curso, "media": notas})

        if len(medias_individuais) > 1:
            notas = [media(notas_total[edicao]) for edicao in edicoes]
            medias_individuais.append({"curso": {"sigla": "média dos cursos", "cor": "000000"}, "media": notas})

        # Para armazenar todas as notas de todos os programas
            notas_total = defaultdict(list)

        # Médias gerais totais
        medias_gerais = []

        for t_curso in cursos:
            notas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                alocacoes_tmp = alocacoes.filter(projeto__ano=periodo[0],
                                                projeto__semestre=periodo[1],
                                                aluno__curso2=t_curso)
                notas_lista = [alocacao.get_media["media"] for alocacao in alocacoes_tmp if alocacao.get_media["pesos"] == 1]

                notas_total[edicao].extend(notas_lista)
                notas.append(media(notas_lista))
            
            if any(nota is not None for nota in notas):  # Check if notas is not empty
                medias_gerais.append({"curso": t_curso, "media": notas})

        if len(medias_gerais) > 1:
            notas = [media(notas_total[edicao]) for edicao in edicoes]
            medias_gerais.append({"curso": {"sigla": "média dos cursos", "cor": "000000"}, "media": notas})

        context = {
            "medias_individuais": medias_individuais,
            "medias_gerais": medias_gerais,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "titulo": {"pt": "Evolução por Notas/Conceitos", "en": "Evolution by Grades"},
            "edicoes": edicoes,
            "cursos": cursos,
        }

    return render(request, "projetos/evolucao_notas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_objetivos(request):
    """Mostra graficos das evoluções por objetivo de aprendizagem."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    if request.is_ajax():

        if "curso" in request.POST:
            curso = request.POST["curso"]
            grupo = "grupo" in request.POST and request.POST["grupo"]=="true"
            individuais = "individuais" in request.POST and request.POST["individuais"]=="true"
            so_finais = "so_finais" in request.POST and request.POST["so_finais"]=="true"

            if so_finais:
                # Somenete avaliações finais do Capstone
                exames = Exame.objects.filter(titulo__in=[
                    "Banca Final",
                    "Relatório Final de Grupo",
                    "Relatório Final Individual",
                    "Avaliação Final Individual",
                    "Avaliação Final de Grupo"
                ])
                avaliacoes_sep = Avaliacao2.objects.filter(exame__in=exames)
            else:
                avaliacoes_sep = Avaliacao2.objects.all()

            if curso == 'T':

                # Avaliações Individuais
                if (individuais):
                    avaliacoes_ind = avaliacoes_sep.filter(alocacao__isnull=False)
                else:
                    avaliacoes_ind = avaliacoes_sep.none()

                # Avaliações Grupais
                if grupo:
                    avaliacoes_grupo = avaliacoes_sep.filter(alocacao__isnull=True, projeto__isnull=False)
                else:
                    avaliacoes_grupo = avaliacoes_sep.none()

                avaliacoes = avaliacoes_ind | avaliacoes_grupo

            else:

                # Avaliações Individuais
                if (individuais):
                    avaliacoes_ind = avaliacoes_sep.filter(alocacao__aluno__curso2__sigla_curta=curso)
                else:
                    avaliacoes_ind = avaliacoes_sep.none()

                # Avaliações Grupais
                if grupo:
                    # identificando projetos com estudantes do curso (pelo menos um)
                    projetos_selecionados = []
                    projetos = Projeto.objects.all()
                    for projeto in projetos:
                        alocacoes = Alocacao.objects.filter(projeto=projeto)
                        for alocacao in alocacoes:
                            if alocacao.aluno.curso2.sigla_curta == curso:
                                projetos_selecionados.append(projeto)
                                break
                            
                    avaliacoes_grupo = Avaliacao2.objects.filter(alocacao__isnull=True, projeto__in=projetos_selecionados)

                else:
                    avaliacoes_grupo = Avaliacao2.objects.none()

                avaliacoes = avaliacoes_ind | avaliacoes_grupo

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#b76353", "#a48577"]

        medias = []
        objetivos = ObjetivosDeAprendizagem.objects.all()
        count = 0

        # Precompute all avaliacoes and group them by edicao and objetivo
        avaliacoes_by_edicao_objetivo = {
            edicao: {
                objetivo: [
                    x.nota for x in avaliacoes.filter(
                        projeto__ano=edicao.split('.')[0],
                        projeto__semestre=edicao.split('.')[1],
                        objetivo=objetivo,
                        na=False
                    )
                ]
                for objetivo in objetivos
            }
            for edicao in edicoes
        }

        for objetivo in objetivos:
            notas = []
            faixas = []
            for edicao in edicoes:
                notas_lista = avaliacoes_by_edicao_objetivo[edicao][objetivo]
                faixa = divide57(notas_lista)
                soma = sum(faixa)
                if soma > 0:
                    faixa = [100 * f / soma for f in faixa]
                notas.append(media(notas_lista))
                faixas.append(faixa)

            titulo = objetivo.titulo if configuracao.lingua == "pt" else objetivo.titulo_en
            medias.append({"objetivo": titulo, "media": notas, "cor": cores[count], "faixas": faixas})
            count += 1




        # Número de estudantes por semestre
        students = []
        if curso == 'T':
            alunos = Aluno.objects.all()
        else:
            alunos = Aluno.objects.filter(curso2__sigla_curta=curso)
        for edicao in edicoes:
            periodo = edicao.split('.')
            students.append(alunos.filter(anoPFE=periodo[0], semestrePFE=periodo[1]).count())

        context = {
            "medias": medias,
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "curso": curso,
            "students": students,
        }

    else:

        context = {
            "titulo": {"pt": "Evolução por Objetivos de Aprendizado", "en": "Evolution by Learning Goals"},
            "edicoes": edicoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, "projetos/evolucao_objetivos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def filtro_projetos(request):
    """Filtra os projetos."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

            cabecalhos = [{"pt": "Projeto", "en": "Project"},
                            {"pt": "Áreas", "en": "Areas"},
                            {"pt": "Estudantes", "en": "Students"},
                            {"pt": "Período", "en": "Period"},
                            {"pt": "Orientador", "en": "Advisor"},
                            {"pt": "Organização", "en": "Organization"},
                            {"pt": "Orientador", "en": "Advisor"},
                            {"pt": "Bancas", "en": "Boards"},
                            {"pt": "Falconi", "en": "Falconi"},
                            {"pt": "Média", "en": "Average"}
                          ]

            context = {
                "projetos": projetos_filtrados.order_by("ano", "semestre", "organizacao"),
                "cabecalhos": cabecalhos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        context = {
            "titulo": {"pt": "Filtro para Projetos", "en": "Filter for Projects"},
            "edicoes": get_edicoes(Projeto)[0],
            "areast": Area.objects.filter(ativa=True),
        }

    return render(request, "projetos/filtra_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def interesses_projetos(request):
    """Verifica interesse para com projetos (na verdade verifico as propostas)."""
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos = Projeto.objects.all()
                propostas = Proposta.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=ano, semestre=semestre)
                propostas = Proposta.objects.filter(ano=ano, semestre=semestre)
  
            context = {
                "propostas": propostas,
                "projetos": projetos,
                "aprimorar": propostas.filter(aprimorar=True).count(),
                "realizar": propostas.filter(realizar=True).count(),
                "iniciar": propostas.filter(iniciar=True).count(),
                "identificar": propostas.filter(identificar=True).count(),
                "mentorar": propostas.filter(mentorar=True).count(),
                "tipo_interesse": Proposta.TIPO_INTERESSE,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        context = {
            "titulo": {"pt": "Interesses com Projetos", "en": "Interests with Projects"},
            "edicoes": get_edicoes(Projeto)[0],
        }

    return render(request, "projetos/interesses_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_por_objetivo(request):
    """Mostra graficos das evoluções por objetivo de aprendizagem."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    if request.is_ajax():

        if "curso" in request.POST:
            curso = request.POST["curso"]
            grupo = "grupo" in request.POST and request.POST["grupo"]=="true"
            individuais = "individuais" in request.POST and request.POST["individuais"]=="true"

            so_finais = "so_finais" in request.POST and request.POST["so_finais"]=="true"

            if so_finais:
                # Somenete avaliações finais do Capstone
                # tipos = [2, 12, 22, 52, 54]
                exames = Exame.objects.filter(titulo="Banca Final") |\
                         Exame.objects.filter(titulo="Relatório Final de Grupo") |\
                         Exame.objects.filter(titulo="Relatório Final Individual") |\
                         Exame.objects.filter(titulo="Avaliação Final Individual") |\
                         Exame.objects.filter(titulo="Avaliação Final de Grupo")
                avaliacoes_sep = Avaliacao2.objects.filter(exame__in=exames)
            else:
                avaliacoes_sep = Avaliacao2.objects.all()

            if curso == 'T':

                # Avaliações Individuais
                if (individuais):
                    avaliacoes_ind = avaliacoes_sep.filter(alocacao__isnull=False)
                else:
                    avaliacoes_ind = avaliacoes_sep.none()

                # Avaliações Grupais
                if grupo:
                    avaliacoes_grupo = avaliacoes_sep.filter(alocacao__isnull=True, projeto__isnull=False)
                else:
                    avaliacoes_grupo = avaliacoes_sep.none()

                avaliacoes = avaliacoes_ind | avaliacoes_grupo

            else:

                # Avaliações Individuais
                if (individuais):
                    avaliacoes_ind = avaliacoes_sep.filter(alocacao__aluno__curso2__sigla_curta=curso)
                else:
                    avaliacoes_ind = avaliacoes_sep.none()

                # Avaliações Grupais
                if grupo:
                    # identificando projetos com estudantes do curso (pelo menos um)
                    projetos_selecionados = []
                    projetos = Projeto.objects.all()
                    for projeto in projetos:
                        alocacoes = Alocacao.objects.filter(projeto=projeto)
                        for alocacao in alocacoes:
                            if alocacao.aluno.curso2.sigla_curta == curso:
                                projetos_selecionados.append(projeto)
                                break
                            
                    avaliacoes_grupo = Avaliacao2.objects.filter(alocacao__isnull=True, projeto__in=projetos_selecionados)

                else:
                    avaliacoes_grupo = Avaliacao2.objects.none()

                avaliacoes = avaliacoes_ind | avaliacoes_grupo

        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        low = []
        mid = []
        high = []
        
        id_objetivo = request.POST["objetivo"]
        objetivo = ObjetivosDeAprendizagem.objects.get(id=id_objetivo)

        alocacoes = []

        for edicao in edicoes:
            periodo = edicao.split('.')
            semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
            notas_lista = [x.nota for x in semestre if x.objetivo == objetivo and not x.na]
            notas = divide57(notas_lista)
            soma = sum(notas)
            if soma > 0:
                low.append(100*notas[0]/soma)
                mid.append(100*notas[1]/soma)
                high.append(100*notas[2]/soma)
            else:
                low.append(0)
                mid.append(0)
                high.append(0)

            alocacoes_tmp = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                    projeto__semestre=periodo[1])

            if curso != 'T':
                alocacoes_tmp = alocacoes_tmp.filter(aluno__curso2__sigla_curta=curso)

            alocacoes.append(alocacoes_tmp.count())

        estudantes = zip(edicoes, alocacoes)

        context = {
            "low": low,
            "mid": mid,
            "high": high,
            "curso": curso,
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "objetivo": objetivo,
            "objetivos": objetivos,
            "estudantes": estudantes,
            "lingua": configuracao.lingua,
        }

    else:

        context = {
            "titulo": {"pt": "Evolução por Objetivos de Aprendizado", "en": "Evolution by Learning Goals"},
            "edicoes": edicoes,
            "objetivos": objetivos,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, "projetos/evolucao_por_objetivo.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def correlacao_medias_cr(request):
    """Mostra graficos da correlação entre notas e o CR dos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")

    if request.is_ajax():

        periodo = ["todo", "periodo"]
        alocacoes = None
        estudantes = {}

        if "edicao" in request.POST:

            curso = request.POST["curso"]

            if request.POST["edicao"] != "todas":
                periodo = request.POST["edicao"].split('.')
                alocacoes_tmp = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                        projeto__semestre=periodo[1])

                if curso != 'T':
                    curso_sel = Curso.objects.get(sigla_curta=curso)
                    estudantes[curso_sel] = alocacoes_tmp.filter(aluno__curso2__sigla_curta=curso)
                else:
                    for curso_sel in Curso.objects.filter(curso_do_insper=True):
                        aloc = alocacoes_tmp.filter(aluno__curso2__sigla_curta=curso_sel.sigla_curta)
                        if aloc:
                            estudantes[curso_sel] = aloc

            else:
                alocacoes = {}
                for edicao in edicoes:
                    periodo = edicao.split('.')
                    semestre = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                       projeto__semestre=periodo[1])
                    if curso == 'T':
                        alocacoes[periodo[0]+"_"+periodo[1]] = semestre
                    else:
                        semestre = semestre.filter(aluno__curso2__sigla_curta=curso)
                        alocacoes[periodo[0]+"_"+periodo[1]] = semestre
                periodo = ["todo", "periodo"]

        else:
            return HttpResponse("Algum erro não identificado.", status=401)


        context = {
            "alocacoes": alocacoes,
            "estudantes": estudantes,
            "periodo": periodo,
            "ano": configuracao.ano,
            "semestre": configuracao.semestre,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "titulo": {"pt": "Correlação entre Médias e CR", "en": "Correlation between Grades and CR"},
            "edicoes": edicoes,
            "cursos": cursos_insper,
        }

    return render(request, "projetos/correlacao_medias_cr.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def editar_projeto(request, primarykey):
    """Editar Projeto."""

    if request.user.tipo_de_usuario != 4:  # Administrador
        return HttpResponse("Somente administradores podem editar projetos.", status=401)

    projeto = Projeto.objects.get(id=primarykey)

    if request.method == "POST":

        # Atualiza título
        titulo = request.POST.get("titulo", None)
        if titulo and ( projeto.titulo_final or projeto.titulo_final != titulo):
            projeto.titulo_final = titulo
        else:
            projeto.titulo_final = None
            
        projeto.resumo = request.POST.get("resumo", None)
        projeto.abstract = request.POST.get("abstract", None)
        projeto.palavras_chave = request.POST.get("palavras_chave", None)
        
        # Realoca orientador
        orientador_id = request.POST.get("orientador", None)
        if orientador_id:
            orientador = get_object_or_404(Professor, pk=orientador_id)
            projeto.orientador = orientador
        else:
            projeto.orientador = None

        # Realoca coorientador
        coorientador_id = request.POST.get("coorientador", None)
        if coorientador_id:
            coorientador = get_object_or_404(PFEUser, pk=coorientador_id)
            (reg, _) = Coorientador.objects.get_or_create(projeto=projeto)
            reg.usuario = coorientador
            reg.save()
        else:
            coorientadores = Coorientador.objects.filter(projeto=projeto)
            for coorientador in coorientadores:
                coorientador.delete()

        # Realoca estudantes
        estudantes_ids = []
        estudantes = request.POST.getlist("estudante")
        for estudante_id in estudantes:
            if estudante_id:
                estudantes_ids.append(int(estudante_id))

        # Apaga os estudantes que não estão mais no projeto
        Alocacao.objects.filter(projeto=projeto).exclude(aluno__id__in=estudantes_ids).delete()

        # Aloca os estudantes que não estavam alocados
        for estudante_id in estudantes_ids:
            if not Alocacao.objects.filter(projeto=projeto, aluno__id=estudante_id).exists():
                estudante = get_object_or_404(Aluno, pk=estudante_id)
                alocacao = Alocacao.create(estudante, projeto)
                alocacao.save()

        # Define projeto com time misto (estudantes de outras instituições)
        projeto.time_misto = "time_misto" in request.POST

        projeto.save()

        return redirect("projeto_completo", primarykey=primarykey)

    context = {
        "projeto": projeto,
        "professores": Professor.objects.all(),
        "alocacoes": Alocacao.objects.filter(projeto=projeto),
        "estudantes": Aluno.objects.all(),
        "coorientadores": Coorientador.objects.filter(projeto=projeto),
    }
    return render(request, "projetos/editar_projeto.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def nomes(request):
    """Acerta maiúsculas de nomes."""

    message = "Os seguintes nomes foram alterados:<br><br>"
    for usuario in PFEUser.objects.all():

        first_name = cap_name(usuario.first_name)
        last_name = cap_name(usuario.last_name)

        if (first_name != usuario.first_name) or (last_name != usuario.last_name):

            message += "&bull; " + usuario.first_name + " " + usuario.last_name
            message += "   \t &nbsp; >>>> &nbsp; \t   "
            message += first_name + " " + last_name + "<br>"

            usuario.first_name = first_name
            usuario.last_name = last_name

            usuario.save()

    message += "<br>&nbsp;&nbsp;<a href='" + request.build_absolute_uri("/administracao") + "'>voltar</a><br>"

    return HttpResponse(message)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def acompanhamento_view(request):
    """Cria um anotação para uma organização parceira."""
    if request.is_ajax() and "texto" in request.POST:
        acompanhamento = Acompanhamento.create()

        try:
            parceiro_id = int(request.POST["parceiro"])
            parceiro = get_object_or_404(Parceiro, id=parceiro_id)
        except ValueError:
            return HttpResponse("Erro: Parceiro não foi informado corretamente.", status=401)
        
        acompanhamento.autor = parceiro.user

        acompanhamento.texto = request.POST["texto"]

        if "data_hora" in request.POST:
            try:
                acompanhamento.data = dateutil.parser\
                    .parse(request.POST["data_hora"])
            except (ValueError, OverflowError):
                acompanhamento.data = datetime.datetime.now()

        acompanhamento.save()

        data = {
            "data": acompanhamento.data.strftime("%Y.%m.%d"),
            "autor": str(acompanhamento.autor.get_full_name()),
            "autor_id": acompanhamento.autor.parceiro.id,
            "org": str(parceiro.organizacao),
            "org_id": parceiro.organizacao.id,
            "atualizado": True,
        }

        return JsonResponse(data)

    context = {
        "parceiros": Parceiro.objects.all(),
        "data_hora": datetime.datetime.now(),
    }

    return render(request,
                  "projetos/acompanhamento_view.html",
                  context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def reenvia_avisos(request):
    """Reenvia avisos do dia."""
    usuario_sem_acesso(request, (4,)) # Soh Adm
    avisos_do_dia()
    eventos_do_dia()
    return redirect("avisos_listar")


@login_required
def upload_estudantes_projeto(request, projeto_id):

    if request.method == "POST":
        projeto = get_object_or_404(Projeto, id=projeto_id)
        projeto.titulo_final = request.POST.get("titulo_final", None)
        projeto.resumo = request.POST.get("resumo", None)
        projeto.abstract = request.POST.get("abstract", None)
        projeto.palavras_chave = request.POST.get("palavras_chave", None)

        projeto.atualizacao_estudantes = datetime.datetime.now()

        projeto.save()

    return redirect("/projetos/meuprojeto")


def grupos_formados(request):

    return render(request, "projetos/grupos_formados.html", context={})

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

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from users.models import PFEUser, Aluno, Professor, Opcao, Alocacao
from users.models import Parceiro
from users.support import adianta_semestre
from users.support import get_edicoes

from operacional.models import Curso

from .models import Projeto, Proposta, Configuracao, Observacao
from .models import Coorientador, Avaliacao2, ObjetivosDeAprendizagem

from .models import Feedback, Acompanhamento, Anotacao, Organizacao
from .models import Documento, FeedbackEstudante
from .models import Banco, Reembolso, Aviso, Conexao
from .models import Area, AreaDeInteresse, Banca

from .messages import email, message_reembolso

from academica.models import Exame

from .support import simple_upload, calcula_objetivos, cap_name

from .tasks import avisos_do_dia, eventos_do_dia

def get_areas_estudantes(alunos):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {}

    usuarios = []
    for aluno in alunos:
        usuarios.append(aluno.user)

    todas_areas = Area.objects.filter(ativa=True)
    for area in todas_areas:
        areas = AreaDeInteresse.objects.filter(usuario__in=usuarios, area=area)
        areaspfe[area.titulo] = (areas, area.descricao)

    outras = AreaDeInteresse.objects.filter(usuario__in=usuarios, area__isnull=True)

    return areaspfe, outras


def get_areas_propostas(propostas):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""
    areaspfe = {}

    areas = Area.objects.filter(ativa=True)
    for area in areas:
        areas = AreaDeInteresse.objects.filter(proposta__in=propostas, area=area)
        areaspfe[area.titulo] = (areas, area.descricao)

    outras = AreaDeInteresse.objects.filter(proposta__in=propostas, area__isnull=True)

    return areaspfe, outras


@login_required
@permission_required("projetos.view_projeto", raise_exception=True)
def index_projetos(request):
    """Página principal dos Projetos."""
    return render(request, "projetos/index_projetos.html")


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

    context = {
        "projeto": projeto,
        "MEDIA_URL": settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_detalhes.html', context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projeto_completo(request, primarykey):
    """Mostra um projeto por completo."""
    projeto = get_object_or_404(Projeto, pk=primarykey)
    alocacoes = Alocacao.objects.filter(projeto=projeto)
    opcoes = Opcao.objects.filter(proposta=projeto.proposta)
    conexoes = Conexao.objects.filter(projeto=projeto)
    coorientadores = Coorientador.objects.filter(projeto=projeto)

    medias_oo = None
    if alocacoes:
        alocacao = alocacoes.first()
        medias_oo = alocacao.get_medias_oo

        if not (medias_oo['medias_apg'] or medias_oo['medias_afg'] or medias_oo['medias_rig'] or medias_oo['medias_bi'] or medias_oo['medias_rfg'] or medias_oo['medias_bf']):
            medias_oo = None

    documentos = Documento.objects.filter(projeto=projeto, tipo_documento__projeto=True)

    projetos_avancados = Projeto.objects.filter(avancado=projeto)

    cooperacoes = Conexao.objects.filter(projeto=projeto, colaboracao=True)

    context = {
        "projeto": projeto,
        "alocacoes": alocacoes,
        "medias_oo": medias_oo,
        "opcoes": opcoes,
        "conexoes": conexoes,
        "coorientadores": coorientadores,
        "documentos": documentos,  # checar se necessário
        "projetos_avancados": projetos_avancados,
        "cooperacoes": cooperacoes,
        "MEDIA_URL": settings.MEDIA_URL,
    }
    return render(request, 'projetos/projeto_completo.html', context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def distribuicao_areas(request):
    """Distribuição por área de interesse dos alunos/propostas/projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano              # Ano atual
    semestre = configuracao.semestre    # Semestre atual

    todas = False  # Para mostrar todos os dados de todos os anos e semestres
    tipo = "estudantes"
    curso = "todos"

    if request.is_ajax():
        if "tipo" in request.POST and "edicao" in request.POST:

            tipo = request.POST["tipo"]

            if request.POST["edicao"] == "todas":
                todas = True
            else:
                periodo = request.POST["edicao"].split('.')
                ano = int(periodo[0])
                semestre = int(periodo[1])

            if tipo == "estudantes" and "curso" in request.POST:
                curso = request.POST["curso"]

        else:
            return HttpResponse("Erro não identificado (POST incompleto).",
                                status=401)

        if tipo == "estudantes":
            alunos = Aluno.objects.all()
            if curso != "T":
                alunos = alunos.filter(curso2__sigla_curta=curso)
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
                'total': propostas_projetos.count(),
                'areaspfe': areaspfe,
                'outras': outras,
            }

        else:
            return HttpResponse("Erro não identificado (não encontrado tipo).",
                            status=401)

        return render(request, 'projetos/distribuicao_areas.html', context)

    edicoes, _, _ = get_edicoes(Aluno)
    context = {
        "edicoes": edicoes,
        "cursos": Curso.objects.filter(curso_do_insper=True),
    }

    return render(request, "projetos/distribuicao_areas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_fechados(request):
    """Lista todos os projetos fechados."""
    edicoes = []

    if request.is_ajax():
        if "edicao" in request.POST and "curso" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano,
                                                            semestre=semestre)

            curso = request.POST["curso"]    
            
            projetos_filtrados = projetos_filtrados.order_by("-avancado", Lower("organizacao__nome"))

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
                if curso != 'T':
                    estudantes_pfe = estudantes_pfe.filter(alocacao__aluno__curso2__sigla_curta=curso)

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
                    opcoes = Opcao.objects.filter(proposta=projeto.proposta)
                    opcoes = opcoes.filter(aluno__user__tipo_de_usuario=1)
                    opcoes = opcoes.filter(aluno__alocacao__projeto=projeto)
                    opcoes = opcoes.filter(aluno=estudante)
                    if opcoes:
                        prioridade = opcoes.first().prioridade
                        prioridades.append(prioridade)
                    else:
                        prioridades.append(0)
                    if estudante.externo:
                        numero_estudantes_externos += 1
                prioridade_list.append(zip(estudantes_pfe, prioridades))
                cooperacoes.append(Conexao.objects.filter(projeto=projeto,
                                                            colaboracao=True))
                conexoes.append(Conexao.objects.filter(projeto=projeto,
                                                        colaboracao=False))

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
            "edicoes": edicoes,
            "cursos": Curso.objects.all().order_by("id"),
            "informacoes": informacoes,
        }

    return render(request, "projetos/projetos_fechados.html", context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def projetos_lista(request):
    """Lista todos os projetos."""
    edicoes = []
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            if edicao == "todas":
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = request.POST["edicao"].split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano,
                                                            semestre=semestre)

            avancados = "avancados" in request.POST and request.POST["avancados"]=="true"

            if not avancados:
                projetos_filtrados = projetos_filtrados.filter(avancado__isnull=True)

            projetos = projetos_filtrados.order_by("ano", "semestre", "organizacao", "titulo",)

            #cabecalhos = ["Projeto", "Estudantes", "Período", "Orientador", "Organização", ]
            cabecalhos = ["Project" ,"Students", "Semester", "Advisor", "Sponsor",]
            
            context = {
                "projetos": projetos,
                "cabecalhos": cabecalhos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Projeto)
        #titulo = "Projetos"
        titulo = "Projects"
        context = {
            "titulo": titulo,
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
                ano, semestre = request.POST["edicao"].split('.')
                bancas = Banca.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

            cabecalhos = ["Tipo" ,"Data", "Projeto", "Avaliadores",]
            
            context = {
                "bancas": bancas,
                "cabecalhos": cabecalhos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Projeto)
        titulo = "Bancas"
        context = {
            "titulo": titulo,
            "edicoes": edicoes,
        }

    return render(request, "projetos/bancas_lista.html", context)


@login_required
def meuprojeto(request):
    """Mostra o projeto do próprio aluno, se for aluno."""

    # Caso não seja Aluno, Professor ou Administrador (ou seja Parceiro)
    if request.user.tipo_de_usuario != 1 and request.user.tipo_de_usuario != 2 and request.user.tipo_de_usuario != 4:
        mensagem = "Você não está cadastrado como aluno ou professor!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    # Caso seja Professor ou Administrador
    if request.user.tipo_de_usuario in (2, 4):
        return redirect('professor_detail', primarykey=request.user.professor.pk)

    # Caso seja um aluno
    context = {
        "aluno": request.user.aluno,
        "configuracao": get_object_or_404(Configuracao),
    }

    return render(request, "projetos/meuprojeto_aluno.html", context=context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
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
            novo_projeto.titulo = projeto.titulo_final
            novo_projeto.titulo_final = None

        novo_projeto.avancado = projeto
        novo_projeto.ano = ano
        novo_projeto.semestre = semestre

        novo_projeto.save()

    return redirect('projeto_completo', primarykey=novo_projeto.id)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def carrega_bancos(request):
    """Rotina que carrega arquivo CSV de bancos para base de dados do servidor."""
    with open('projetos/bancos.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                pass
            else:
                # ('Nome: {}; Código {}'.format(row[0],row[1]))
                banco = Banco.create(nome=row[0], codigo=row[1])
                banco.save()
            line_count += 1
    mensagem = "Bancos carregados."
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, 'generic.html', context=context)


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
            mensagem = "Projetos ainda não disponíveis para o seu período de PFE."
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        projeto = Projeto.objects.filter(alocacao__aluno=aluno).last()
    else:
        projeto = None

    if request.method == 'POST':
        reembolso = Reembolso.create(usuario)
        reembolso.descricao = request.POST['descricao']

        cpf = int(''.join(i for i in request.POST['cpf'] if i.isdigit()))

        reembolso.conta = request.POST['conta']
        reembolso.agencia = request.POST['agencia']

        reembolso.banco = get_object_or_404(Banco, codigo=request.POST['banco'])

        reembolso.valor = request.POST['valor']

        reembolso.save()  # Preciso salvar para pegar o PK
        nota_fiscal = simple_upload(request.FILES['arquivo'],
                                    path="reembolsos/",
                                    prefix=str(reembolso.pk)+"_")
        reembolso.nota = nota_fiscal[len(settings.MEDIA_URL):]

        reembolso.save()

        subject = 'Reembolso PFE : '+usuario.username
        recipient_list = configuracao.recipient_reembolso.split(";")
        recipient_list.append('pfeinsper@gmail.com')  # sempre mandar para a conta do gmail
        recipient_list.append(usuario.email)  # mandar para o usuário que pediu o reembolso
        if projeto:
            if projeto.orientador:
                # mandar para o orientador se houver
                recipient_list.append(projeto.orientador.user.email)
        message = message_reembolso(usuario, projeto, reembolso, cpf)
        check = email(subject, recipient_list, message)
        if check != 1:
            message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
        return HttpResponse(message)

    bancos = Banco.objects.all().order_by(Lower("nome"), "codigo")
    context = {
        'usuario': usuario,
        'projeto': projeto,
        'bancos': bancos,
        'configuracao': configuracao,
    }
    return render(request, 'projetos/reembolso_pedir.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def comite(request):
    """Exibe os professores que estão no comitê do PFE."""
    context = {
        "professores": Professor.objects.filter(user__membro_comite=True),
        "cabecalhos": ["Nome", "e-mail", "Lattes", ],
        "titulo": "Comitê PFE",
        }
    return render(request, 'projetos/comite_pfe.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_feedback(request):
    """Lista todos os feedback das Organizações Parceiras."""
    configuracao = get_object_or_404(Configuracao)

    edicoes = range(2018, configuracao.ano+1)

    # PROJETOS
    num_projetos = []
    for ano_projeto in edicoes:

        projetos = Projeto.objects.filter(ano=ano_projeto).\
            filter(semestre=2).\
            count()
        num_projetos.append(projetos)

        projetos = Projeto.objects.filter(ano=ano_projeto+1).\
            filter(semestre=1).\
            count()
        num_projetos.append(projetos)

    feedbacks = Feedback.objects.all().order_by("-data")
    num_feedbacks = []

    # primeiro ano foi diferente
    numb_feedb = Feedback.objects.filter(data__range=["2018-06-01", "2019-05-31"]).\
        count()
    num_feedbacks.append(numb_feedb)

    for ano_projeto in edicoes[1:]:
        numb_feedb = Feedback.objects.filter(data__range=[str(ano_projeto)+"-06-01",
                                                          str(ano_projeto)+"-12-31"]).\
            count()
        num_feedbacks.append(numb_feedb)
        numb_feedb = Feedback.objects.filter(data__range=[str(ano_projeto+1)+"-01-01",
                                                          str(ano_projeto+1)+"-05-31"]).\
            count()
        num_feedbacks.append(numb_feedb)

    context = {
        'feedbacks': feedbacks,
        'SERVER_URL': settings.SERVER,
        'loop_anos': edicoes,
        'num_projetos': num_projetos,
        'num_feedbacks': num_feedbacks,
    }
    return render(request, 'projetos/lista_feedback.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_feedback_estudantes(request):
    """Lista todos os feedback das Organizações Parceiras."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, ano_atual, semestre_atual = get_edicoes(Projeto)

    if request.is_ajax():

        todos_feedbacks = FeedbackEstudante.objects.all().order_by("-momento")

        num_feedbacks = []
        num_estudantes = []

        for edicao in edicoes:

            ano, semestre = edicao.split('.')

            estudantes = Aluno.objects.filter(anoPFE=ano).\
                filter(semestrePFE=semestre).\
                count()
            num_estudantes.append(estudantes)

            numb_feedb = todos_feedbacks.filter(projeto__ano=ano).\
                filter(projeto__semestre=semestre).\
                values('estudante').distinct().\
                count()
            num_feedbacks.append(numb_feedb)

        estudantes = Aluno.objects.all()

        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao != 'todas':
                ano, semestre = request.POST['edicao'].split('.')
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

                if feedback:
                    feedbacks.append(feedback)
                else:
                    feedbacks.append(None)

            else:
                projetos.append(None)
                feedbacks.append(None)


        alocacoes = zip(estudantes, projetos, feedbacks)

        configuracao = get_object_or_404(Configuracao)
        coordenacao = configuracao.coordenacao

        cabecalhos = ["Nome", "Projeto", "Data", "Mensagem", ]

        context = {
            "SERVER_URL": settings.SERVER,
            "loop_anos": edicoes,
            "num_estudantes": num_estudantes,
            "num_feedbacks": num_feedbacks,
            "alocacoes": alocacoes,
            "coordenacao": coordenacao,
            "edicoes": edicoes,
            "cabecalhos": cabecalhos,
        }

    else:
        context = {
            "edicoes": edicoes,
            "titulo": "Listagem de Feedbacks Finais dos Estudantes",
        }

    return render(request, 'projetos/lista_feedback_estudantes.html', context)



@login_required
@permission_required("users.altera_professor", raise_exception=True)
def lista_acompanhamento(request):
    """Lista todos os acompanhamentos das Organizações Parceiras."""
    context = {
        "acompanhamentos": Acompanhamento.objects.all().order_by("-data"),
    }
    return render(request, 'projetos/lista_acompanhamento.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    context = {
        "feedback": get_object_or_404(Feedback, id=feedback_id),
    }
    return render(request, 'projetos/mostra_feedback.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def mostra_feedback_estudante(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    context = {
        "feedback": get_object_or_404(FeedbackEstudante, id=feedback_id),
    }
    return render(request, 'estudantes/estudante_feedback.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
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
    """Mostra graficos das evoluções do PFE."""
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
        "lingua": configuracao.lingua,
    }

    return render(request, 'projetos/projetos_vs_propostas.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def analise_notas(request):
    """Mostra graficos das evoluções do PFE."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, _ = get_edicoes(Avaliacao2)

    if request.is_ajax():

        periodo = ["todo", "periodo"]
        
        medias_semestre = Alocacao.objects.all()

        if 'edicao' in request.POST and 'curso' in request.POST:
            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
                medias_semestre = medias_semestre.filter(projeto__ano=periodo[0],
                                                         projeto__semestre=periodo[1])
            curso = request.POST['curso']
            if curso != 'T':
                medias_semestre = medias_semestre.filter(aluno__curso2__sigla_curta=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        valor = {}
        valor["ideal"] = 7.0
        valor["regular"] = 5.0

        notas = {
            "rii": {"ideal": 0, "regular":0, "inferior": 0},
            "rig": {"ideal": 0, "regular":0, "inferior": 0},
            "bi":  {"ideal": 0, "regular":0, "inferior": 0},
            "rfi": {"ideal": 0, "regular":0, "inferior": 0},
            "rfg": {"ideal": 0, "regular":0, "inferior": 0},
            "bf":  {"ideal": 0, "regular":0, "inferior": 0},
            "rpl": {"ideal": 0, "regular":0, "inferior": 0},
            "ppf": {"ideal": 0, "regular":0, "inferior": 0},
            "api": {"ideal": 0, "regular":0, "inferior": 0},
            "apg": {"ideal": 0, "regular":0, "inferior": 0},
            "afg": {"ideal": 0, "regular":0, "inferior": 0},
            "afi": {"ideal": 0, "regular":0, "inferior": 0},
        }

        notas_lista = [x.get_notas for x in medias_semestre]
        for nota2 in notas_lista:
            for nota in nota2:
                if nota[0] == "RII":
                    if nota[1] >= valor["ideal"]:
                        notas["rii"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["rii"]["regular"] += 1
                    else:
                        notas["rii"]["inferior"] += 1
                elif nota[0] == "RIG":
                    if nota[1] >= valor["ideal"]:
                        notas["rig"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["rig"]["regular"] += 1
                    else:
                        notas["rig"]["inferior"] += 1
                elif nota[0] == "BI":
                    if nota[1] >= valor["ideal"]:
                        notas["bi"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["bi"]["regular"] += 1
                    else:
                        notas["bi"]["inferior"] += 1
                elif nota[0] == "RFI":
                    if nota[1] >= valor["ideal"]:
                        notas["rfi"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["rfi"]["regular"] += 1
                    else:
                        notas["rfi"]["inferior"] += 1
                elif nota[0] == "RFG":
                    if nota[1] >= valor["ideal"]:
                        notas["rfg"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["rfg"]["regular"] += 1
                    else:
                        notas["rfg"]["inferior"] += 1
                elif nota[0] == "BF":
                    if nota[1] >= valor["ideal"]:
                        notas["bf"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["bf"]["regular"] += 1
                    else:
                        notas["bf"]["inferior"] += 1
                elif nota[0] == "RPL":
                    if nota[1] >= valor["ideal"]:
                        notas["rpl"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["rpl"]["regular"] += 1
                    else:
                        notas["rpl"]["inferior"] += 1
                elif nota[0] == "PPF":
                    if nota[1] >= valor["ideal"]:
                        notas["ppf"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["ppf"]["regular"] += 1
                    else:
                        notas["ppf"]["inferior"] += 1
                elif nota[0] == "APG":
                    if nota[1] >= valor["ideal"]:
                        notas["apg"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["apg"]["regular"] += 1
                    else:
                        notas["apg"]["inferior"] += 1
                elif nota[0] == "API":
                    if nota[1] >= valor["ideal"]:
                        notas["api"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["api"]["regular"] += 1
                    else:
                        notas["api"]["inferior"] += 1
                elif nota[0] == "AFG":
                    if nota[1] >= valor["ideal"]:
                        notas["afg"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["afg"]["regular"] += 1
                    else:
                        notas["afg"]["inferior"] += 1
                elif nota[0] == "AFI":
                    if nota[1] >= valor["ideal"]:
                        notas["afi"]["ideal"] += 1
                    elif nota[1] >= valor["regular"]:
                        notas["afi"]["regular"] += 1
                    else:
                        notas["afi"]["inferior"] += 1

        medias_lista = [x.get_media for x in medias_semestre]

        # Somente apresenta as médias que esteja completas (pesso = 100%)
        medias_validas = list(filter(lambda d: d['pesos'] == 1.0, medias_lista))

        medias = {}
        medias["ideal"] = len(list(filter(lambda d: d['media'] >= valor["ideal"], medias_validas)))
        medias["regular"] = len(list(filter(lambda d: valor["ideal"] > d['media'] >= valor["regular"], medias_validas)))
        medias["inferior"] = len(list(filter(lambda d: d['media'] < valor["regular"], medias_validas)))
        medias["total"] = len(medias_validas)

        context = {
            'periodo': periodo,
            'ano': configuracao.ano,
            'semestre': configuracao.semestre,
            'loop_anos': edicoes,
            'medias': medias,
            "notas": notas,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "edicoes": edicoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, 'projetos/analise_notas.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def certificacao_falconi(request):
    """Mostra graficos das certificacões Falconi."""
    configuracao = get_object_or_404(Configuracao)

    edicoes, _, _ = get_edicoes(Projeto)

    # cortando ["2018.2", "2019.1", "2019.2", "2020.1", ....]
    edicoes = edicoes[4:]

    if request.is_ajax():

        periodo = ""

        if "edicao" in request.POST:
            if request.POST["edicao"] != "todas":
                periodo = request.POST["edicao"].split('.')
                projetos = Projeto.objects.filter(ano=periodo[0], semestre=periodo[1])
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # if 'curso' in request.POST:
        #     curso = request.POST['curso']
        #     if curso != 'T':
        #         medias_semestre = medias_semestre.filter(aluno__curso2__sigla_curta=curso)
        # else:
        #     return HttpResponse("Algum erro não identificado.", status=401)

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
            "edicoes": edicoes,
        }

    return render(request, "projetos/certificacao_falconi.html", context)


def media(notas_lista):
    soma = 0
    total = 0
    for i in notas_lista:
        if i:
            soma += float(i)
            total += 1
    if total == 0:
        return None
    return soma / total

# Didide pela proporção de 5 e 7
def divide57(notas_lista):
    if notas_lista:
        valores = [0, 0, 0]
        for i in notas_lista:
            if i:
                if i < 5:
                    valores[0] += 1
                elif i > 7:
                    valores[2] += 1
                else:
                    valores[1] += 1
        return valores
    else:
        return [0, 0, 0]

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def analise_objetivos(request):
    """Mostra graficos das evoluções do PFE."""
    edicoes, _, _ = get_edicoes(Avaliacao2)

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
            if curso != 'T':
                alocacoes = alocacoes.filter(aluno__curso2__sigla_curta=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        context = calcula_objetivos(alocacoes)
        context["edicoes"] = edicoes
        context["total_geral"] = len(alocacoes)
        context["curso"] = curso
        context["periodo"] = periodo

    else:
        context = {
            "edicoes": edicoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, 'projetos/analise_objetivos.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_notas(request):
    """Mostra graficos das evoluções do PFE."""
    edicoes, _, _ = get_edicoes(Avaliacao2)
    cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")

    if request.is_ajax():

        avaliacoes = Avaliacao2.objects.all()
        alocacoes = Alocacao.objects.all()

        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                avaliacoes = avaliacoes.filter(alocacao__aluno__curso2__sigla_curta=curso)
                alocacoes = alocacoes.filter(aluno__curso2__sigla_curta=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # Para armazenar todas as notas de todos os programas de engenharia
        notas_total = {}
        for edicao in edicoes:
            notas_total[edicao] = []

        avaliacoes = avaliacoes.filter(exame=Exame.objects.get(titulo="Relatório Intermediário Individual")) | avaliacoes.filter(exame=Exame.objects.get(titulo="Relatório Final Individual"))

        medias_individuais = []
        count = 0
        
        for t_curso in cursos:
            notas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
                notas_lista = [x.nota for x in semestre if (x.alocacao != None and x.alocacao.aluno.curso2 == t_curso)]
                notas_total[edicao] += notas_lista
                notas.append(media(notas_lista))
            if notas != [None] * len(notas):  # não está vazio
                medias_individuais.append({"curso": t_curso, "media": notas})
            count += 1
            
        if len(medias_individuais) > 1:
            notas = []
            for edicao in edicoes:
                notas.append(media(notas_total[edicao]))
            medias_individuais.append({"curso": {"sigla": "média engenharia", "cor": "000000"}, "media": notas})


        ################################


        # Para armazenar todas as notas de todos os programas de engenharia
        notas_total = {}
        for edicao in edicoes:
            notas_total[edicao] = []

        # médias gerais totais
        medias_gerais = []
        count = 0
        for t_curso in cursos:
            notas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                alocacoes_tmp = alocacoes.filter(projeto__ano=periodo[0],
                                                 projeto__semestre=periodo[1],
                                                 aluno__curso2=t_curso)
                notas_lista = []
                for alocacao in alocacoes_tmp:
                    media_loc = alocacao.get_media
                    if media_loc["pesos"] == 1:
                        notas_lista.append(media_loc["media"])

                notas_total[edicao] += notas_lista
                notas.append(media(notas_lista))
            if notas != [None] * len(notas):  # não está vazio
                medias_gerais.append({"curso": t_curso, "media": notas})
            count += 1

        if len(medias_gerais) > 1:
            notas = []
            for edicao in edicoes:
                notas.append(media(notas_total[edicao]))
            medias_gerais.append({"curso": {"sigla": "média engenharia", "cor": "000000"}, "media": notas})

        context = {
            "medias_individuais": medias_individuais,
            "medias_gerais": medias_gerais,
            "edicoes": edicoes,
            "curso": curso,
        }

    else:
        context = {
            "edicoes": edicoes,
            "cursos": cursos,
        }

    return render(request, 'projetos/evolucao_notas.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_objetivos(request):
    """Mostra graficos das evoluções do PFE."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    if request.is_ajax():

        if 'curso' in request.POST:
            curso = request.POST['curso']
            grupo = 'grupo' in request.POST and request.POST["grupo"]=="true"
            individuais = 'individuais' in request.POST and request.POST["individuais"]=="true"
            so_finais = "so_finais" in request.POST and request.POST["so_finais"]=="true"

            if so_finais:
                # Somenete avaliações finais do PFE
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

        cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#b76353", "#a48577"]

        medias = []
        objetivos = ObjetivosDeAprendizagem.objects.all()
        count = 0
        for objetivo in objetivos:
            notas = []
            faixas = []
            for edicao in edicoes:
                periodo = edicao.split('.')
                semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
                notas_lista = [x.nota for x in semestre if x.objetivo == objetivo and not x.na]
                
                faixa = divide57(notas_lista)
                soma = sum(faixa)
                if soma > 0:
                    faixa[0] = 100*faixa[0]/soma
                    faixa[1] = 100*faixa[1]/soma
                    faixa[2] = 100*faixa[2]/soma
                
                notas.append(media(notas_lista))
                faixas.append(faixa)

            if configuracao.lingua == "pt":
                titulo = objetivo.titulo
            else:
                titulo = objetivo.titulo_en

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
            "edicoes": edicoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, 'projetos/evolucao_objetivos.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def filtro_projetos(request):
    """Filtra os projetos."""
    edicoes = []
    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano,
                                                            semestre=semestre)
            projetos = projetos_filtrados.order_by("ano", "semestre", "organizacao", "titulo",)
            context = {
                'projetos': projetos,
            }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Projeto)

        areas = Area.objects.filter(ativa=True)
        
        context = {
            "edicoes": edicoes,
            "areast": areas,
        }

    return render(request, 'projetos/filtra_projetos.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def evolucao_por_objetivo(request):
    """Mostra graficos das evoluções do PFE."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    if request.is_ajax():

        if "curso" in request.POST:
            curso = request.POST['curso']
            grupo = "grupo" in request.POST and request.POST["grupo"]=="true"
            individuais = "individuais" in request.POST and request.POST["individuais"]=="true"

            so_finais = "so_finais" in request.POST and request.POST["so_finais"]=="true"

            if so_finais:
                # Somenete avaliações finais do PFE
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

        # cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#375330", "#a48577"]

        low = []
        mid = []
        high = []
        
        id_objetivo = request.POST['objetivo']
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
            'curso': curso,
            'ano': configuracao.ano,
            'semestre': configuracao.semestre,
            'edicoes': edicoes,
            "objetivo": objetivo,
            "objetivos": objetivos,
            "estudantes": estudantes,
            "lingua": configuracao.lingua,
        }

    else:

        context = {
            "edicoes": edicoes,
            "objetivos": objetivos,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, 'projetos/evolucao_por_objetivo.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def correlacao_medias_cr(request):
    """Mostra graficos da correlação entre notas e o CR dos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    if request.is_ajax():

        periodo = ["todo", "periodo"]
        alocacoes = None
        estudantes = {}

        if 'edicao' in request.POST:

            curso = request.POST['curso']

            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
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
            'periodo': periodo,
            'ano': configuracao.ano,
            'semestre': configuracao.semestre,
            'edicoes': edicoes,
            "curso": curso,
        }

    else:
        context = {
            "edicoes": edicoes,
            "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        }

    return render(request, 'projetos/correlacao_medias_cr.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def editar_projeto(request, primarykey):
    """Editar Projeto."""

    projeto = Projeto.objects.get(id=primarykey)

    if request.method == 'POST':

        # Atualiza título
        titulo = request.POST.get('titulo', None)
        if titulo and ( projeto.titulo_final or projeto.titulo != titulo):
            projeto.titulo_final = titulo

        # Atualiza descrição
        descricao = request.POST.get('descricao', None)
        if descricao and ( projeto.descricao or projeto.proposta.descricao != descricao):
            projeto.descricao = descricao

        # Realoca orientador
        orientador_id = request.POST.get('orientador', None)
        if orientador_id:
            orientador = get_object_or_404(Professor, pk=orientador_id)
            projeto.orientador = orientador

        # Realoca coorientador
        coorientador_id = request.POST.get('coorientador', None)
        if coorientador_id:
            coorientador = get_object_or_404(PFEUser, pk=coorientador_id)
            (reg, _created) = Coorientador.objects.get_or_create(projeto=projeto)
            reg.usuario = coorientador
            reg.save()
        else:
            coorientadores = Coorientador.objects.filter(projeto=projeto)
            for coorientador in coorientadores:
                coorientador.delete()
        

        # Realoca estudantes
        estudantes_ids = []
        # estudantes = request.POST.get('estudante', None)
        estudantes = request.POST.getlist('estudante')
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
        projeto.time_misto = 'time_misto' in request.POST


        projeto.save()

        return redirect('projeto_completo', primarykey=primarykey)


    professores = Professor.objects.all()
    alocacoes = Alocacao.objects.filter(projeto=projeto)

    estudantes = Aluno.objects.all()

    coorientadores = Coorientador.objects.filter(projeto=projeto)

    context = {
        "projeto": projeto,
        "professores": professores,
        "alocacoes": alocacoes,
        "estudantes": estudantes,
        "coorientadores": coorientadores,
    }
    return render(request, 'projetos/editar_projeto.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
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

        parceiro_id = int(request.POST["parceiro"])
        parceiro = get_object_or_404(Parceiro, id=parceiro_id)
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
            "org": str(parceiro.organizacao),
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

    # Caso não seja Administrador
    if request.user.tipo_de_usuario != 4:
        return HttpResponse("Você não tem privilégios!", status=401)
    
    avisos_do_dia()
    eventos_do_dia()

    return redirect("avisos_listar")

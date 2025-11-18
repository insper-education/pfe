#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import string
import random
import datetime
import tablib
import logging
import json
import csv

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context, Template
from django.urls import reverse_lazy
from django.utils import html
from django.views import generic

import coordenacao


from .forms import PFEUserCreationForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao
from .models import Alocacao, OpcaoTemporaria
from .support import get_edicoes, adianta_semestre, retrocede_semestre

from academica.models import Composicao, CodigoColuna, Exame, CodigoConduta
from academica.support import filtra_composicoes #, get_respostas_estilos
from academica.support3 import get_media_alocacao_i

from administracao.models import Carta, Estrutura
from administracao.support import get_limite_propostas, usuario_sem_acesso

from estudantes.models import EstiloComunicacao

from operacional.models import Curso

from projetos.models import Certificado, Configuracao, Projeto, Conexao, Evento
from projetos.models import Area, Coorientador, Avaliacao2, Observacao, Reprovacao
from projetos.messages import email
from projetos.support3 import calcula_objetivos, get_notas_alocacao
from projetos.support4 import get_objetivos_atuais

# Get an instance of a logger
logger = logging.getLogger("django")

@login_required
def user_detail(request, primarykey=None):
    """Retorna a página conforme o perfil do usuário."""

    if primarykey:
        user = get_object_or_404(PFEUser, pk=primarykey)
    else:
        user = request.user

    if user.eh_estud:  # estudante
        return redirect("estudante_detail", user.aluno.id)
    elif user.eh_prof:  # professor
        return redirect("professor_detail", user.professor.id)
    elif user.eh_parc:  # parceiro
        return redirect("parceiro_detail", user.parceiro.id)
    elif user.eh_admin:  # administrador (supor administrador como professor)
        return redirect("professor_detail", user.professor.id)

    return HttpResponse("Usuário não encontrado.", status=401)


@login_required
def perfil(request):
    """Retorna a página conforme o perfil do usuário."""
    context = {"titulo": {"pt": "Perfil", "en": "Profile"}}
    return render(request, "users/profile_detail.html", context=context)


class SignUp(generic.CreateView):
    """Rotina para fazer o login."""
    form_class = PFEUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"


class Usuario(generic.DetailView):
    """Usuário."""
    model = Aluno


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_lista(request):
    """Gera lista com todos os alunos já registrados."""
    configuracao = get_object_or_404(Configuracao)
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        edicao = request.POST["edicao"]
        
        ano = 0
        semestre = 0

        tabela_alunos = {}
        cursos = []
        totais = {"total": 0}

        # Conta soh estudantes
        alunos = Aluno.objects.all()

        # Filtra para estudantes de um curso específico
        curso_sel = request.POST.get("curso")
        if curso_sel:
            if curso_sel == "T":  # Todos os estudantes (sem externos)
                alunos = alunos.filter(curso2__in=cursos_insper)
            elif curso_sel != "TE":  # Todos os estudantes (com externos)
                alunos = alunos.filter(curso2__sigla_curta=curso_sel)
        
        if edicao not in ("todas", "trancou"):
            # Estudantes de um semestre em particular
            ano, semestre = map(int, edicao.split('.'))

            alunos_list = alunos.filter(trancado=False)

            alunos_semestre = alunos_list\
                .filter(alocacao__projeto__ano=ano,
                        alocacao__projeto__semestre=semestre)\
                .distinct()
            
            tabela_alunos[ano] = {semestre: {}}

            for curso in Curso.objects.all().order_by("id"):
                count_estud = alunos_semestre.filter(curso2__sigla=curso.sigla).count()
                if count_estud > 0:
                    if curso not in cursos:
                        cursos.append(curso)
                    tabela_alunos[ano][semestre][curso.sigla] = count_estud
                    totais[curso.sigla] = count_estud
                    totais["total"] += count_estud

            tabela_alunos[ano][semestre]["total"] = alunos_semestre.count()
            
            alunos_list = alunos_semestre |\
                alunos_list.filter(ano=ano, semestre=semestre).distinct()

        else:
            
            # Essa parte está em loop para pegar todos os alunos de todos os semestres
            if edicao == "todas":
                alunos_list = alunos.filter(trancado=False)
            else:
                alunos_list = alunos.filter(trancado=True)
                ano = "trancou"

            # Rotina para contar quantidade de alunos
            ano_tmp = 2018
            semestre_tmp = 2
            while True:
                alunos_semestre = alunos_list\
                    .filter(alocacao__projeto__ano=ano_tmp,
                            alocacao__projeto__semestre=semestre_tmp)\
                    .distinct()

                if ano_tmp > configuracao.ano + 6:
                    break

                if not alunos_semestre:
                    if semestre_tmp == 1:
                        semestre_tmp = 2
                    else:
                        ano_tmp += 1
                        semestre_tmp = 1
                    continue

                if ano_tmp not in tabela_alunos:
                    tabela_alunos[ano_tmp] = {}
                if semestre_tmp not in tabela_alunos[ano_tmp]:
                    tabela_alunos[ano_tmp][semestre_tmp] = {}

                tabela_alunos[ano_tmp][semestre_tmp]["total"] = 0
                for curso in Curso.objects.all().order_by("id"):
                    count_estud = alunos_semestre.filter(curso2__sigla__exact=curso.sigla).count()
                    if count_estud > 0:
                        if curso not in cursos:
                            cursos.append(curso)
                        tabela_alunos[ano_tmp][semestre_tmp][curso.sigla] = count_estud
                        if curso.sigla in totais:
                            totais[curso.sigla] += count_estud
                        else:
                            totais[curso.sigla] = count_estud
                        tabela_alunos[ano_tmp][semestre_tmp]["total"] += count_estud
                        totais["total"] += count_estud

                if semestre_tmp == 1:
                    semestre_tmp = 2
                else:
                    ano_tmp += 1
                    semestre_tmp = 1


        total_estudantes = alunos_list.count()
        num_estudantes = {}
        for curso in Curso.objects.all().order_by("id"):
            count_estud = alunos_list.filter(curso2__sigla=curso.sigla).count()
            if count_estud > 0:
                num_estudantes[curso] = count_estud

        num_alunos = {  # Estudantes por genero
            'M': alunos_list.filter(user__genero='M').count(),
            'F': alunos_list.filter(user__genero='F').count(),
        }

        cabecalhos = [{"pt": "Nome", "en": "Name"},
                        {"pt": "Matrícula", "en": "Enrollment", "esconder": True},
                        {"pt": "e-mail", "en": "e-mail"},
                        {"pt": "Curso", "en": "Program"},
                        {"pt": "Período", "en": "Period"},
                        {"pt": "Projeto", "en": "Project"},
                        {"pt": "Linkedin", "en": "Linkedin", "esconder": True},
                        {"pt": "Celular", "en": "Cellphone", "esconder": True},
                        ]
        
        context = {
            "alunos_list": alunos_list,
            "total_estudantes": total_estudantes,
            "num_estudantes": num_estudantes,
            "num_alunos": num_alunos,
            "configuracao": configuracao,
            "cursos": cursos,
            "tabela_alunos": tabela_alunos,
            "totais": totais,
            "ano": ano,
            "semestre": semestre,
            "cabecalhos": cabecalhos,
            "curso_sel": curso_sel,
        }

    else:

        context = {
            "edicoes": get_edicoes(Aluno)[0],
            "titulo": {"pt": "Estudantes", "en": "Students"},
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "users/estudantes_lista.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_notas(request, professor=None):
    """Gera lista os estudantes com suas notas."""

    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        ano, semestre = map(int, request.POST["edicao"].split('.'))

        alunos_list = Aluno.objects.filter(trancado=False, externo__isnull=True)
        alunos_list = alunos_list.order_by(Lower("user__first_name"), Lower("user__last_name"))

        if professor is not None:  # A chamada padrão é com o argumento "meus_projetos"
            user = get_object_or_404(PFEUser, pk=request.user.pk)
            if not user.eh_prof_a:
                mensagem_erro = {"pt": "Você não está cadastrado como professor!",
                                 "en": "You are not registered as a professor!"}
                context = {
                    "area_principal": True,
                    "mensagem_erro": mensagem_erro,
                }
                return render(request, "generic_ml.html", context=context)
            
            # Incluindo também se coorientação
            coorientacoes = Coorientador.objects.filter(usuario=user, projeto__ano=ano, projeto__semestre=semestre).values_list("projeto", flat=True)
            projetos = Projeto.objects.filter(ano=ano, semestre=semestre, orientador=user.professor) | Projeto.objects.filter(id__in=coorientacoes, ano=ano, semestre=semestre)
            alunos_list = alunos_list.filter(alocacao__projeto__in=projetos)
            
        # Buscando estudantes que tiveram alocação no semestre
        alunos_semestre = alunos_list.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre).distinct()
        
        # Incluindo os alunos que estão cursando o semestre em algum projeto
        alunos_list = alunos_semestre |\
            alunos_list.filter(ano=ano, semestre=semestre, alocacao__isnull=False).distinct()

        cabecalhos = [{"pt": "Nome", "en": "Name"},
                        {"pt": "e-mail", "en": "e-mail", "esconder": True},
                        {"pt": "Curso", "en": "Program"},
                        {"pt": "Projeto", "en": "Project"},
                        {"pt": "Notas", "en": "Grades"},
                        {"pt": "Individual", "en": "Individual", "tipo": "numeral"},
                        {"pt": "Descontos", "en": "Discounts", "tipo": "numeral"},
                        {"pt": "Média Parcial", "en": "Partial Average", "tipo": "numeral"},
                        {"pt": "Média Final", "en": "Final Average", "tipo": "numeral"},
                    ]

        captions = [ [
            {"sigla": "XX", "pt": "Abaixo da Média", "en": "Below Average", "cor": "red"},
            {"sigla": "XX", "pt": "Peso da Média Incompleto", "en": "Incomplete Average Weight", "cor": "orange"},
        ], 
        [
            {"sigla": "BI", "pt": "Banca Intermediária", "en": "Midterm Jury"},
            {"sigla": "BF", "pt": "Banca Final", "en": "Final Jury"},
            {"sigla": "RIG", "pt": "Relatório Intermediário de Grupo", "en": "Midterm Group Report"},
            {"sigla": "RFG", "pt": "Relatório Final de Grupo", "en": "Final Group Report"},
            {"sigla": "RII", "pt": "Relatório Intermediário Individual", "en": "Midterm Individual Report"},
            {"sigla": "RFI", "pt": "Relatório Final Individual", "en": "Final Individual Report"},
        ],
        [
            {"sigla": "Individual", "pt": "Média só das avaliações individuais", "en": "Average of individual assessments only"},
            {"sigla": "Descontos", "pt": "Total de descontos na média final a ser aplicado", "en": "Total discounts on the final average to be applied"},
            {"sigla": "Média Parcial", "pt": "Média das avaliações até o momento já com descontos", "en": "Average of assessments so far with discounts"},
            {"sigla": "Média Final", "pt": "Média final do estudante no projeto", "en": "Student's final average in the project"},
        ] ]

        context = {
            "alunos_list": alunos_list,
            "ano": ano,
            "semestre": semestre,
            "ano_semestre": str(ano)+"."+str(semestre),
            "cabecalhos": cabecalhos,
            "captions": captions,
        }

    else:
        informacoes = [
                (".pesos_aval", "Pesos", "Weights", False),
            ]

        context = {
            "titulo": {"pt": "Avaliações por Estudante", "en": "Assessments by Student"},
            "edicoes": get_edicoes(Projeto)[0],
            "informacoes": informacoes,
        }

    return render(request, "users/estudantes_notas.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def blackboard_notas(request, anosemestre):
    """Gera notas para o blackboard."""
    ano, semestre = map(int, anosemestre.split('.'))
    
    composicoes = filtra_composicoes(Composicao.objects.filter(pesos__isnull=False), ano, semestre)  # (entregavel=True):
    exames = set()
    for composicao in composicoes:
        exames.add(composicao.exame)
    exames.add(Exame.objects.get(sigla="D"))  # Descontos
    exames.add(Exame.objects.get(sigla="M"))  # Média

    if request.method == "POST":
        colunas = {}
        for exame in exames:
            if exame.sigla in request.POST:
                if request.POST[exame.sigla] == "":
                    CodigoColuna.objects.filter(exame=exame, ano=ano, semestre=semestre).delete()
                else:
                    colunas[exame.titulo], _ = CodigoColuna.objects.get_or_create(exame=exame, ano=ano, semestre=semestre)
                    colunas[exame.titulo].coluna = request.POST[exame.sigla]
                    colunas[exame.titulo].save()

        dataset = tablib.Dataset()

        headers=["Nome", "Sobrenome", "Nome do usuário"]
        for coluna in colunas:
            if coluna and colunas[coluna].coluna:
                headers.append(coluna + " [Total de pontos: 10 Pontuação] |" + colunas[coluna].coluna)

        dataset.headers = headers

        cursos = request.POST.getlist("curso")
        ext_cursos = ""
        for curso in cursos:
            sigla = Curso.objects.get(id=curso).sigla_curta
            ext_cursos += "_" + sigla

        alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre, aluno__trancado=False, aluno__curso2__id__in=cursos).order_by("aluno__user__last_name", "aluno__user__first_name")

        tipo = request.POST["tipo"]
        
        for alocacao in alocacoes:
            notas = get_notas_alocacao(alocacao, checa_banca=False)
            linha = [alocacao.aluno.user.first_name]
            linha += [alocacao.aluno.user.last_name]
            linha += [alocacao.aluno.user.username]

            # Convertendo lista de notas para dicionário
            avaliacao = {}
            for nota in notas:
                avaliacao[nota["nome"]] = nota["nota"]
            
            media = get_media_alocacao_i(alocacao)
            for coluna in colunas:
                if coluna in avaliacao:
                    linha += [f"{avaliacao[coluna]:.2f}".replace('.',',')]
                else:
                    if coluna == "Média":
                        if media["media"]:
                            linha += [f"{media['media']:.2f}".replace('.',',')]
                        else:
                            linha += [""]
                    elif coluna == "Descontos":
                        if media["descontos"]:
                            linha += [f"{media['descontos']:.2f}".replace('.',',')]
                        else:
                            linha += [""]
                    else:
                        linha += [""]
                    
            dataset.append(linha)


        if tipo == "xls":
            xls_dataset = dataset.export("csv", delimiter="\t", quotechar='"', dialect="excel", quoting=csv.QUOTE_ALL)
            response = HttpResponse(content_type="text/csv")
            response.write(u"\ufeff".encode("utf-16le"))
            response.write(xls_dataset.encode("utf-16le"))  # Encode the content in UTF-16LE
            response["Content-Disposition"] = "attachment; filename=notas_"+str(ano)+"_"+str(semestre)+ext_cursos+".xls"
        elif tipo == "csv":
            csv_dataset = dataset.export("csv", quotechar='"', dialect="excel")
            #csv_with_trailing_commas = csv_dataset.replace("\r\n", ",\r\n")  # Caso precise colocar uma vírgula no final de cada linha
            response = HttpResponse(csv_dataset, content_type="text/csv")
            response.write(u"\ufeff".encode("utf-8-sig"))
            response["Content-Disposition"] = "attachment; filename=notas_"+str(ano)+"_"+str(semestre)+ext_cursos+".csv"
        
        return response

    context = {
        "titulo": {"pt": "Notas para Blackboard", "en": "Grades for Blackboard"},
        "exames": exames,
        "colunas": CodigoColuna.objects.filter(exame__in=exames, ano=ano, semestre=semestre),
        "anosemestre": anosemestre,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
    }
    return render(request, "users/blackboard_notas.html", context=context)
    

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_objetivos(request):
    """Gera lista com todos os alunos já registrados."""

    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        
        ano, semestre = map(int, request.POST["edicao"].split('.'))
        alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

        # Filtra os Objetivos de Aprendizagem do semestre (Todos: individuais e juntando com os de grupo)
        objetivos_t = get_objetivos_atuais(ano, semestre)

        ### ISSO ESTA DESATUALIZADO E PRECISA USAR UM ESQUEMA MAIS ATUAL USANDO OS EXAMES
        objetivos_i = objetivos_t.filter(avaliacao_aluno=True) # Somentes objetivos de avaliação individual

        cabecalhos = [{"pt": "Nome", "en": "Name"},
                        {"pt": "e-mail", "en": "e-mail"},
                        {"pt": "Curso", "en": "Program"},
                        {"pt": "Projeto", "en": "Project"},
                        ]
        
        individual = True
        for objetivo in objetivos_i:
            cabecalhos.append({
                "pt": objetivo.titulo + ("<br>(individual)" if individual else "<br>(grp+ind)"),
                "en": objetivo.titulo_en + ("<br>(individual)" if individual else "<br>(grp+ind)"),
                "individual": True,
            })

        individual = False
        for objetivo in objetivos_t:
            cabecalhos.append({
                "pt": objetivo.titulo + ("<br>(individual)" if individual else "<br>(grp+ind)"),
                "en": objetivo.titulo_en + ("<br>(individual)" if individual else "<br>(grp+ind)"),
                "todas": True,
            })

        captions = []
        for curso in Curso.objects.filter(curso_do_insper=True).order_by("id"):
            captions.append({
                "sigla": curso.sigla_curta,
                "pt": curso.nome,
                "en": curso.nome_en,
            })

        context = {
            "alocacoes": alocacoes,
            "objetivos_i": objetivos_i,
            "objetivos_t": objetivos_t,
            "cabecalhos": cabecalhos,
            "captions": [captions],
        }

    else:
        context = {
            "titulo": {"pt": "Objetivos de Aprendizagem por Estudante", "en": "Learning Goals by Student"},
            "edicoes": get_edicoes(Aluno)[0],
            }
    return render(request, "users/estudantes_objetivos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def projetos_objetivos(request):
    """Gera lista com todos os alunos já registrados."""
    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        
        ano, semestre = map(int, request.POST["edicao"].split('.'))
        projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

        # Filtra os Objetivos de Aprendizagem do semestre
        objetivos = get_objetivos_atuais(ano, semestre)
        
        individual = False

        cabecalhos = [{"pt": "Projeto", "en": "Project"},]
        for objetivo in objetivos:
            cabecalhos.append({
                "pt": objetivo.titulo + ("<br>(individual)" if individual else "<br>(grupo)"),
                "en": objetivo.titulo_en + ("<br>(individual)" if individual else "<br>(group)"),
            })

        captions = []
        for curso in Curso.objects.filter(curso_do_insper=True).order_by("id"):
            captions.append({
                "sigla": curso.sigla_curta,
                "pt": curso.nome,
                "en": curso.nome_en,
            })

        context = {
            "projetos": projetos,
            "objetivos": objetivos,
            "cabecalhos": cabecalhos,
            "captions": [captions],
        }

    else:
        context = {
            "titulo": {"pt": "Objetivos de Aprendizagem por Projeto", "en": "Learning Goals by Project"},
            "edicoes": get_edicoes(Aluno)[0],
            }
    return render(request, "users/projetos_objetivos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_inscritos(request):
    """Mostra todos os estudantes que estão se inscrevendo em projetos."""
    configuracao = get_object_or_404(Configuracao)
    
    if request.method == "POST":
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        ano, semestre = map(int, request.POST["edicao"].split('.'))
        lista_estudantes = Aluno.objects.filter(trancado=False, ano=ano, semestre=semestre)
        cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")  # Conta estudantes de cada curso

        min_props = configuracao.min_props

        inscritos = {"sim": [], "nao": [], "tmp": []}
        opcoes, opcoestemp = [], []

        for aluno in lista_estudantes:
            opcao = Opcao.objects.filter(aluno=aluno, proposta__ano=ano, proposta__semestre=semestre)
            opcaotmp = OpcaoTemporaria.objects.filter(aluno=aluno, proposta__ano=ano, proposta__semestre=semestre)
            opcoes.append(opcao)
            opcoestemp.append(opcaotmp)
            if opcao.exists():
                inscritos["sim"].append(aluno.user)
            elif opcaotmp.count() >= min_props:
                inscritos["tmp"].append(aluno.user)
            else:
                inscritos["nao"].append(aluno.user)

        estudantes = zip(lista_estudantes, opcoes, opcoestemp)

        num_estudantes_curso = {}
        for curso in cursos:
            qtd = lista_estudantes.filter(curso2__sigla__exact=curso.sigla).count()
            if qtd:
                num_estudantes_curso[curso] = qtd

        rano, rsemestre = retrocede_semestre(ano, semestre)

        evento = Evento.get_evento(nome="Indicação de interesse nas propostas pelos estudante", ano=rano, semestre=rsemestre)

        cabecalhos = [
            {"pt": "C", "en": "C"},
            {"pt": "Estudante", "en": "Student"},
            {"pt": "Curso", "en": "Program"},
            {"pt": "e-mail", "en": "e-mail", "esconder": True},
            {"pt": "CR", "en": "CR/GPA", "tipo": "numeral", "esconder": True},
        ]

        context = {
            "estudantes": estudantes,
            "num_estudantes": lista_estudantes.count(),
            "inscritos": inscritos,
            "cursos": cursos,
            "num_estudantes_curso": num_estudantes_curso,
            "cabecalhos": cabecalhos,
            "prazo_vencido": evento.endDate < datetime.date.today() if evento and evento.endDate else True,
            "ano": ano,
            "semestre": semestre,
        }

    else:
        
        ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)
        context = {
            "titulo": {"pt": "Estudantes Inscritos", "en": "Enrolled Students"},
            "edicoes": get_edicoes(Aluno)[0],
            "selecionada_edicao": f"{ano}.{semestre}",
        }

    return render(request, "users/estudantes_inscritos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def converte_opcoes(request, ano, semestre):
    """Mostra todos os estudantes que estão se inscrevendo em projetos."""
    min_props = get_object_or_404(Configuracao).min_props
    for estudante in Aluno.objects.filter(trancado=False, ano=ano, semestre=semestre):
        opcoes = Opcao.objects.filter(aluno=estudante, proposta__ano=ano, proposta__semestre=semestre)
        if opcoes.count() >= min_props:
            continue
        opcoes_tmp = OpcaoTemporaria.objects.filter(aluno=estudante, proposta__ano=ano, proposta__semestre=semestre)
        if opcoes_tmp.count() >= min_props:
            for otmp in opcoes_tmp:
                if otmp.prioridade > 0:  # Caso seja zero, era para ser removido e deve ser ignorado
                    Opcao.objects.create(aluno=estudante, proposta=otmp.proposta, prioridade=otmp.prioridade)
    return redirect("estudantes_inscritos")


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_notas(request, primarykey):
    """Edita as notas do estudante."""
    alocacao = get_object_or_404(Alocacao, pk=primarykey)

    # Seleciona os tipos de avaliações para o período do projeto
    d = datetime.datetime(alocacao.projeto.ano, (3 if alocacao.projeto.semestre == 1 else 9), 1)
    composicoes = Composicao.objects.filter(data_inicial__lte=d)
    composicoes = composicoes.filter(data_final__gte=d) | composicoes.filter(data_final__isnull=True)

    # Filtra avaliações e observações individuais e de grupo
    avaliacoes = Avaliacao2.objects.filter(alocacao=alocacao, exame__grupo=False) | Avaliacao2.objects.filter(projeto=alocacao.projeto, exame__grupo=True)
    observacoes = Observacao.objects.filter(alocacao=alocacao, exame__grupo=False) | Observacao.objects.filter(projeto=alocacao.projeto, exame__grupo=True)

    # Reprovação
    falha = Reprovacao.objects.filter(alocacao=alocacao)
    reprovacao = falha.last().nota if falha else None

    if request.method == "POST":

        usuario_sem_acesso(request, (4,)) # Soh Admin

        aval_id = str(alocacao.projeto.orientador.user.id)

        for composicao in composicoes:
            if composicao.exame:
                for peso in composicao.peso_set.all():
                    peso_name = "a" + str(composicao.exame.id) + "_peso_" + (str(peso.objetivo.id) if peso.objetivo else "") + "_p" + aval_id
                    nota_name = "a" + str(composicao.exame.id) + "_nota_" + (str(peso.objetivo.id) if peso.objetivo else "") + "_p" + aval_id
                    peso_value = request.POST.get(peso_name, "")
                    nota_value = request.POST.get(nota_name, "")
                    
                    if nota_value != "":
                        if composicao.exame.grupo:
                            (reg, _created) = avaliacoes.get_or_create(projeto=alocacao.projeto,
                                                                       exame=composicao.exame,
                                                                       objetivo=peso.objetivo,
                                                                       avaliador = alocacao.projeto.orientador.user)
                        else:
                            (reg, _created) = avaliacoes.get_or_create(projeto=alocacao.projeto,
                                                                       exame=composicao.exame,
                                                                       objetivo=peso.objetivo,
                                                                       alocacao=alocacao,
                                                                       avaliador = alocacao.projeto.orientador.user)
                        reg.peso = float(peso_value)
                        reg.nota = float(nota_value)
                        
                        if _created:
                            if alocacao.projeto.orientador:
                                reg.avaliador = alocacao.projeto.orientador.user

                        reg.save()

            obs_name_orientador = "a" + str(composicao.exame.id) + "_obs_orientador" + "_p" + aval_id
            obs_name_estudantes = "a" + str(composicao.exame.id) + "_obs_estudantes" + "_p" + aval_id
            obs_value_orientador = request.POST.get(obs_name_orientador, "")
            obs_value_estudantes = request.POST.get(obs_name_estudantes, "")
            if obs_value_orientador != "" or obs_value_estudantes != "":
                if composicao.exame.grupo:
                    (reg, _created) = observacoes.get_or_create(projeto=alocacao.projeto,
                                                                exame=composicao.exame,
                                                                avaliador = alocacao.projeto.orientador.user)
                else:
                    (reg, _created) = observacoes.get_or_create(projeto=alocacao.projeto,
                                                                exame=composicao.exame,
                                                                alocacao=alocacao,
                                                                avaliador = alocacao.projeto.orientador.user)
                if obs_value_orientador != "":
                    reg.observacoes_orientador = obs_value_orientador

                if obs_value_estudantes != "":
                    reg.observacoes_estudantes = obs_value_estudantes

                if _created:
                    if alocacao.projeto.orientador:
                        reg.avaliador = alocacao.projeto.orientador.user

                reg.save()

        # Reprovacao
        rep = request.POST.get("reprovacao", "")
        if rep:
            reg = falha.last()
            if not reg:
                reg = Reprovacao(alocacao=alocacao)
            reg.nota = rep
            reg.save()
        else:
            for f in falha:
                f.delete()

        mensagem = "Notas de <b>" + alocacao.aluno.user.get_full_name()
        mensagem += "</b> atualizadas:<br>\n"

        media = get_media_alocacao_i(alocacao)
        if media is not None:
            if media["pesos"] is not None:
                mensagem += "&nbsp;&nbsp;Peso Final = "
                mensagem += str(round(media["pesos"]*100, 2)) + "% <br>\n"
            if media["media"] is not None:
                mensagem += "&nbsp;&nbsp;Média Final = "
                mensagem += str(round(media["media"], 2)) + "<br>\n"
            mensagem += "<br>\n"

        for avaliacao in avaliacoes:
            mensagem += str(avaliacao.exame)
            mensagem += " [" + str(avaliacao.avaliador) + "]"
            if(avaliacao.objetivo):
                mensagem += " - Objetivo de Aprendizagem: " + str(avaliacao.objetivo.titulo) + ", "
            if (avaliacao.peso is not None) and (avaliacao.nota is not None):
                mensagem += " peso: " + str(round(avaliacao.peso, 2)) + ", "
                mensagem += " nota: " +str(round(avaliacao.nota, 2))
            else:
                mensagem += " NA (Não Avaliado)"
            mensagem += "<br>\n"

        mensagem = html.urlize(mensagem)
        context = {
            "area_principal": True,
            "mensagem": {"pt": mensagem, "en": mensagem},
        }
        return render(request, "generic_ml.html", context=context)

    context = {
        "titulo": {"pt": "Edição de Notas", "en": "Edit Grades"},
        "alocacao": alocacao,
        "composicoes": composicoes,
        "avaliacoes": avaliacoes,
        "observacoes": observacoes,
        "reprovacao": reprovacao,
    }

    return render(request, "users/edita_nota.html", context=context)


@login_required
def estudante_detail(request, primarykey=None):
    """Mostra detalhes sobre o estudante."""
    if primarykey:
        estudante = Aluno.objects.filter(pk=primarykey).first()
    elif request.user.eh_estud:
        estudante = request.user.aluno
    else:
        raise Http404("Estudante não encontrado.")

    if not estudante:
        raise Http404("Estudante não encontrado.")

    if request.user.eh_estud and request.user.aluno != estudante:
        return HttpResponse("Você não tem permissão para acessar essa página.", status=401)
    if request.user.eh_parc:
        return HttpResponse("Você não tem permissão para acessar essa página.", status=401)

    alocacoes = Alocacao.objects.filter(aluno=estudante).reverse()
    context = calcula_objetivos(alocacoes)
    context.update({
        "titulo": {"pt": "Estudante", "en": "Student"},
        "aluno": estudante,
        "alocacoes": alocacoes,
        "certificados": Certificado.objects.filter(usuario=estudante.user),
        "areas_de_interesse_possiveis": Area.objects.filter(ativa=True),
    })

    # Estilos de Comunicação
    # estilos_respostas = get_respostas_estilos(estudante.user)
    # if estilos_respostas:
    #     context["estilos"] = EstiloComunicacao.objects.all()
    #     context["estilos_respostas"] = estilos_respostas

    # Funcionalidade do Grupo
    funcionalidade_grupo = estudante.user.funcionalidade_grupo
    if funcionalidade_grupo:
        context["questoes_funcionalidade"] = Estrutura.loads(nome="Questões de Funcionalidade")
        context["funcionalidade_grupo"] = {estudante.user: funcionalidade_grupo}

    # Código de Conduta Individual
    codigo_conduta = CodigoConduta.objects.filter(content_type=ContentType.objects.get_for_model(estudante.user), object_id=estudante.user.id).last()
    if codigo_conduta:
        context["perguntas_codigo_conduta"] = Estrutura.loads(nome="Código de Conduta Individual")
        context["respostas_conduta"] = json.loads(codigo_conduta.codigo_conduta) if codigo_conduta.codigo_conduta else None

    return render(request, "users/estudante_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def professor_detail(request, primarykey):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=primarykey)
    context = {
            "titulo": {"pt": "Professor", "en": "Professor"},
            "professor": professor,
            "projetos": Projeto.objects.filter(orientador=professor, proposta__intercambio=False),
            "responsavel": Projeto.objects.filter(orientador=professor, proposta__intercambio=True),
        }
    return render(request, "users/professor_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def parceiro_detail(request, primarykey=None):
    """Mostra detalhes sobre o parceiro."""

    if not primarykey:
        return HttpResponse("Parceiro não encontrado.", status=401)
    
    parceiro = get_object_or_404(Parceiro, pk=primarykey)

    context = {
        "titulo": {"pt": "Parceiro", "en": "Partner"},
        "parceiro": parceiro,
        "conexoes": Conexao.objects.filter(parceiro=parceiro),
    }
    return render(request, "users/parceiro_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def contas_senhas(request, edicao=None):
    """permite selecionar os estudantes para enviar conta e senha."""
    usuario_sem_acesso(request, (4,)) # Soh Adm
    
    cursos_insper = Curso.objects.filter(curso_do_insper=True).order_by("id")
    cursos_externos = Curso.objects.filter(curso_do_insper=False).order_by("id")

    if request.method == "POST": 
        if "edicao" not in request.POST:
            return HttpResponse("Algum erro não identificado.", status=401)
        edicao = request.POST["edicao"]
        estudantes = Aluno.objects.all()
        if edicao != "todas":
            ano, semestre = edicao.split('.')
            estudantes = estudantes.filter(ano=ano, semestre=semestre, trancado=False)

        curso = request.POST.get("curso")
        if curso != "TE":  # Filtra para projetos com estudantes de um curso específico
            if curso != 'T':
                estudantes = estudantes.filter(curso2__sigla_curta=curso)
            else:
                estudantes = estudantes.filter(curso2__in=cursos_insper)


        context = {
                "estudantes": estudantes,
                "template": Carta.objects.filter(template="Envio de Conta para Estudantes").last(),
                "Carta": Carta,
            }

    else:
        
        variaveis = {
            "estudante": { "pt": "Conta do Estudante", "en": "Student Account" },
            "limite_propostas": { "pt": "Data limite para envio de propostas", "en": "Deadline for proposal submission" },
            "senha": { "pt": "Nova senha criada", "en": "New password created" },
            "coordenacao": { "pt": "Conta da Coordenação do Capstone", "en": "Capstone Coordination Account" },
        }

        context = {
            "titulo": {"pt": "Enviar Contas e Senhas para Estudantes", "en": "Send Accounts and Passwords to Students"},
            "edicoes": get_edicoes(Aluno)[0],
            "variaveis": variaveis,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }
        if edicao:
            context["selecionada_edicao"] = edicao

    return render(request, "users/contas_senhas.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.view_administrador", raise_exception=True)
def envia_contas_senhas(request):
    """Envia conta e senha para todos os estudantes que estão no semestre."""
    usuario_sem_acesso(request, (4,)) # Soh Adm

    if request.method == "POST":

        configuracao = get_object_or_404(Configuracao)
        coordenacao = configuracao.coordenacao
        limite_propostas = get_limite_propostas(configuracao)

        texto = request.POST.get("texto", None)

        if "acao" in request.POST and request.POST["acao"] == "atualiza":

            if texto:
                carta = get_object_or_404(Carta, template="Envio de Conta para Estudantes")
                carta.texto = texto
                carta.save()
                mensagem = "Carta atualizada com sucesso."
            else:
                mensagem = "Erro ao atualizar a carta."


        if "acao" in request.POST and request.POST["acao"] == "teste":

            mensagem = "Teste de envio de e-mail:<br>\n<br>\n"
            mensagem += "Enviado para: " + request.user.get_full_name() + " "+\
                        "&lt;" + request.user.email + "&gt;<br>\n"
            
            template_carta = Template(texto)
            estudante = Aluno(user=request.user, ano=configuracao.ano, semestre=configuracao.semestre)  # Apenas para teste
            senha = "SENHA"

            context_carta = {
                    "estudante": estudante,
                    "limite_propostas": limite_propostas.strftime("%d/%m/%Y") if limite_propostas else None,
                    "senha": senha,
                    "coordenacao": coordenacao,
                }

            message_email = template_carta.render(Context(context_carta))
            message_email = html.urlize(message_email) # Faz links de e-mail, outros sites funcionarem

            # Enviando e-mail com mensagem para usuário.
            subject = "Capstone | Conta: Exemplo de Conta"
            recipient_list = [request.user.email, ]
            email(subject, recipient_list, message_email)


        elif "acao" in request.POST and request.POST["acao"] == "enviar":
            estudantes = request.POST.getlist("estudante", None)
            
            template_carta = Template(texto)

            mensagem = "Enviado para:<br>\n<br>\n"
            for estudante_id in estudantes:

                estudante = Aluno.objects.get(id=estudante_id)

                mensagem += estudante.user.get_full_name() + " " +\
                            "&lt;" + estudante.user.email + "&gt;<br>\n"

                # Atualizando senha do usuário.
                senha = ''.join(random.SystemRandom().
                                choice(string.ascii_lowercase + string.digits)
                                for _ in range(6))
                estudante.user.set_password(senha)
                estudante.user.save()

                context_carta = {
                    "estudante": estudante,
                    "limite_propostas": limite_propostas.strftime("%d/%m/%Y") if limite_propostas else None,
                    "senha": senha,
                    "coordenacao": coordenacao,
                }
                
                message_email = template_carta.render(Context(context_carta))
                message_email = html.urlize(message_email) # Faz links de e-mail, outros sites funcionarem

                # Enviando e-mail com mensagem para usuário.
                subject = "Capstone | Conta: " + estudante.user.get_full_name()
                recipient_list = [estudante.user.email, ]
                email(subject, recipient_list, message_email)

            mensagem = html.urlize(mensagem)

        context = {
            "area_principal": True,
            "mensagem": {"pt": mensagem, "en": mensagem},
        }
        return render(request, "generic_ml.html", context=context)

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
def projeto_user(request):
    """Retorna o projeto id associado ao usuário mais recentemente."""
    
    if request.method != "POST" or "user_id" not in request.POST:
        return HttpResponse("Algum erro não identificado.", status=401)
    
    user_id = request.POST["user_id"]
    user = get_object_or_404(PFEUser, pk=user_id)

    projeto_id = 0
    if user.eh_estud:
        alocacao = Alocacao.objects.filter(aluno=user.aluno).last()
        if alocacao:
            projeto_id = alocacao.projeto.id
    elif user.eh_prof_a:
        projeto = Projeto.objects.filter(orientador=user.professor).last()
        if projeto:
            projeto_id = projeto.id
    elif user.eh_parc:
        conexao = Conexao.objects.filter(parceiro=user.parceiro).last()
        if conexao:
            projeto_id = conexao.projeto.id
    else: 
        return HttpResponse("Algum erro não identificado.", status=401)
    
    return JsonResponse({"projeto_id": projeto_id,})


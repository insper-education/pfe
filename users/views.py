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


from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template import Context, Template
from django.urls import reverse_lazy
from django.utils import html
from django.views import generic

from .forms import PFEUserCreationForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao
from .models import Alocacao, OpcaoTemporaria
from .support import get_edicoes, adianta_semestre, retrocede_semestre

from academica.models import Composicao, CodigoColuna, Exame
from academica.support import filtra_composicoes, get_respostas_estilos
from academica.support3 import get_media_alocacao_i

from administracao.models import Carta
from administracao.support import get_limite_propostas, usuario_sem_acesso

from estudantes.models import EstiloComunicacao

from operacional.models import Curso

from projetos.models import Certificado, Configuracao, Projeto, Conexao, Encontro
from projetos.models import Banca, Area, Coorientador, Avaliacao2, Observacao, Reprovacao
from projetos.models import ObjetivosDeAprendizagem, Evento
from projetos.messages import email
from projetos.support3 import calcula_objetivos, get_objetivos_atuais


# Get an instance of a logger
logger = logging.getLogger("django")

@login_required
def user_detail(request, primarykey=0):
    """Retorna a página conforme o perfil do usuário."""

    if primarykey == 0:
        user = request.user
    else:
        user = get_object_or_404(PFEUser, pk=primarykey)

    try:
        if user.tipo_de_usuario == 1:  # estudante
            return redirect("estudante_detail", user.aluno.id)
        elif user.tipo_de_usuario == 2:  # professor
            return redirect("professor_detail", user.professor.id)
        elif user.tipo_de_usuario == 3:  # parceiro
            return redirect("parceiro_detail", user.parceiro.id)
        elif user.tipo_de_usuario == 4:  # administrador (supor administrador como professor)
            return redirect("professor_detail", user.professor.id)
    except:
        return HttpResponse("Usuário com problema em registro.", status=401)    

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

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            
            # Conta soh estudantes
            alunos_todos = Aluno.objects.order_by(Lower("user__first_name"), Lower("user__last_name"))

            ano = 0
            semestre = 0

            tabela_alunos = {}
            cursos = []
            totais = {}
            totais["total"] = 0

            # Filtra para estudantes de um curso específico
            if "curso" in request.POST:
                curso_sel = request.POST["curso"]
                if curso_sel != "TE":  # Todos os estudantes (com externos)
                    if curso_sel != 'T':  # Todos os estudantes (sem externos)
                        alunos_todos = alunos_todos.filter(curso2__sigla_curta=curso_sel)
                    else:
                        alunos_todos = alunos_todos.filter(curso2__in=cursos_insper)
        
            
            if edicao not in ("todas", "trancou"):
                # Estudantes de um semestre em particular
                ano, semestre = map(int, edicao.split('.'))

                alunos_list = alunos_todos.filter(trancado=False)

                alunos_semestre = alunos_list\
                    .filter(alocacao__projeto__ano=ano,
                            alocacao__projeto__semestre=semestre)\
                    .distinct()
                
                tabela_alunos[ano] = {}
                tabela_alunos[ano][semestre] = {}

                for curso in Curso.objects.all().order_by("id"):
                    count_estud = alunos_semestre.filter(curso2__sigla__exact=curso.sigla).count()
                    if count_estud > 0:
                        if curso not in cursos:
                            cursos.append(curso)
                        tabela_alunos[ano][semestre][curso.sigla] = count_estud
                        totais[curso.sigla] = count_estud
                        totais["total"] += count_estud

                tabela_alunos[ano][semestre]["total"] = alunos_semestre.count()
                
                alunos_list = alunos_semestre |\
                    alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            else:
                
                # Essa parte está em loop para pegar todos os alunos de todos os semestres
                if edicao == "todas":
                    alunos_list = alunos_todos.filter(trancado=False)
                else:
                    alunos_list = alunos_todos.filter(trancado=True)
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
                count_estud = alunos_list.filter(curso2__sigla__exact=curso.sigla).count()
                if count_estud > 0:
                    num_estudantes[curso] = count_estud

            # Estudantes por genero
            num_alunos_masculino = alunos_list.filter(user__genero='M').count()
            num_alunos_feminino = alunos_list.filter(user__genero='F').count()

            cabecalhos = [{"pt": "Nome", "en": "Name"},
                          {"pt": "Matrícula", "en": "Enrollment"},
                          {"pt": "e-mail", "en": "e-mail"},
                          {"pt": "Curso", "en": "Program"},
                          {"pt": "Período", "en": "Period"},
                          {"pt": "Projeto", "en": "Project"},
                          {"pt": "Linkedin", "en": "Linkedin"},
                          {"pt": "Celular", "en": "Cellphone"},
                          ]
            
            context = {
                "alunos_list": alunos_list,
                "total_estudantes": total_estudantes,
                "num_estudantes": num_estudantes,
                "num_alunos_masculino": num_alunos_masculino,
                "num_alunos_feminino": num_alunos_feminino,
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
            return HttpResponse("Algum erro não identificado.", status=401)
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
    """Gera lista com todos os alunos já registrados."""

    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = map(int, request.POST["edicao"].split('.'))

            alunos_list = Aluno.objects.filter(trancado=False, externo__isnull=True)
            alunos_list = alunos_list.order_by(Lower("user__first_name"), Lower("user__last_name"))

            if professor is not None:
                user = get_object_or_404(PFEUser, pk=request.user.pk)
                if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
                    mensagem = "Você não está cadastrado como professor!"
                    context = {
                        "area_principal": True,
                        "mensagem": mensagem,
                    }
                    return render(request, "generic.html", context=context)
                
                # Incluindo também se coorientação
                coorientacoes = Coorientador.objects.filter(usuario=user).values_list("projeto", flat=True)
                projetos = Projeto.objects.filter(orientador=user.professor) | Projeto.objects.filter(id__in=coorientacoes)
                alunos_list = alunos_list.filter(alocacao__projeto__in=projetos)

            # Caso o aluno tenha repetido e esteja fazendo de novo o Capstone
            alunos_semestre = alunos_list.filter(alocacao__projeto__ano=ano, alocacao__projeto__semestre=semestre).distinct()

            # Caso o aluno tenha repetido e esteja fazendo de novo o Capstone
            alunos_list = alunos_semestre |\
                alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            cabecalhos = [{"pt": "Nome", "en": "Name"},
                            {"pt": "e-mail", "en": "e-mail"},
                            {"pt": "Curso", "en": "Program"},
                            {"pt": "Projeto", "en": "Project"},
                            {"pt": "Notas", "en": "Grades"},
                            {"pt": "Indi.", "en": "Indi."},
                            {"pt": "Média", "en": "Average"},
                        ]

            captions = [
                {"sigla": "BI", "pt": "Banca Intermediária", "en": "Midterm Jury"},
                {"sigla": "BF", "pt": "Banca Final", "en": "Final Jury"},
                {"sigla": "RIG", "pt": "Relatório Intermediário de Grupo", "en": "Midterm Group Report"},
                {"sigla": "RFG", "pt": "Relatório Final de Grupo", "en": "Final Group Report"},
                {"sigla": "RII", "pt": "Relatório Intermediário Individual", "en": "Midterm Individual Report"},
                {"sigla": "RFI", "pt": "Relatório Final Individual", "en": "Final Individual Report"},
            ]

            context = {
                "alunos_list": alunos_list,
                "ano": ano,
                "semestre": semestre,
                "ano_semestre": str(ano)+"."+str(semestre),
                "cabecalhos": cabecalhos,
                "captions": captions,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        informacoes = [
            (".pesos_aval", "Pesos", "Weights", False),
        ]
        
        context = {
            "titulo": {"pt": "Avaliações por Estudante", "en": "Assessments by Student"},
            "edicoes": get_edicoes(Aluno)[0],
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
    exames.add(Exame.objects.get(sigla="M"))  # Média

    if request.method == "POST":
        colunas = {}
        for exame in exames:
            if exame.sigla in request.POST:
                if request.POST[exame.sigla] == "":
                    CodigoColuna.objects.filter(exame=exame, ano=ano, semestre=semestre).delete()
                else:
                    colunas[exame.sigla], _created = CodigoColuna.objects.get_or_create(exame=exame, ano=ano, semestre=semestre)
                    colunas[exame.sigla].coluna = request.POST[exame.sigla]
                    colunas[exame.sigla].save()

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
            notas = alocacao._alocacao(checa_banca=False)
            linha = [alocacao.aluno.user.first_name]
            linha += [alocacao.aluno.user.last_name]
            linha += [alocacao.aluno.user.username]

            # Convertendo lista de notas para dicionário
            avaliacao = {}
            for nota in notas:
                avaliacao[nota[0]] = nota[1]
            
            for coluna in colunas:
                if coluna in avaliacao:
                    linha += [f"{avaliacao[coluna]:.4f}".replace('.',',')]
                else:
                    if coluna == "M":
                        media = get_media_alocacao_i(alocacao)["media"]
                        if media:
                            linha += [f"{media:.4f}".replace('.',',')]
                        else:
                            linha += [""]
                    else:
                        linha += [""]
                    
            dataset.append(linha)


        if tipo == "xls":
            xls = dataset.export("csv", delimiter="\t", quotechar='"', dialect="excel")
            response = HttpResponse(content_type="text/csv")
            response.write(u"\ufeff".encode("utf-16le"))
            response.write(xls.encode("utf-16le"))  # Encode the content in UTF-16LE
            response["Content-Disposition"] = "attachment; filename=notas_"+str(ano)+"_"+str(semestre)+ext_cursos+".xls"
        elif tipo == "csv":
            csv = dataset.export("csv", quotechar='"', dialect="excel")
            #csv_with_trailing_commas = csv.replace("\r\n", ",\r\n")  # Caso precise colocar uma vírgula no final de cada linha
            response = HttpResponse(csv, content_type="text/csv")
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
    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = map(int, request.POST["edicao"].split('.'))
            alocacaoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)

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
                "alocacaoes": alocacaoes,
                "objetivos_i": objetivos_i,
                "objetivos_t": objetivos_t,
                "cabecalhos": cabecalhos,
                "captions": captions,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
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
    if request.is_ajax():
        if "edicao" in request.POST:
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
                "captions": captions,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
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
    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = map(int, request.POST["edicao"].split('.'))
            alunos = Aluno.objects.filter(trancado=False, anoPFE=ano, semestrePFE=semestre)

            # Conta estudantes de cada curso
            cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")
            num_estudantes_curso = {}
            for curso in cursos:
                qtd = alunos.filter(curso2__sigla__exact=curso.sigla).count()
                if qtd:
                    num_estudantes_curso[curso] = qtd

            inscritos = 0
            inscritos_emails = []
            ninscritos = 0
            ninscritos_emails = []
            tmpinscritos = 0
            tmpinscritos_emails = []
            opcoes = []
            opcoestemp = []
            
            for aluno in alunos:
                opcao = Opcao.objects.filter(aluno=aluno, proposta__ano=ano, proposta__semestre=semestre)
                opcoes.append(opcao)
                opcaotmp = OpcaoTemporaria.objects.filter(aluno=aluno, proposta__ano=ano, proposta__semestre=semestre)
                opcoestemp.append(opcaotmp)
                if opcao.count() >= 5:
                    inscritos += 1
                    inscritos_emails.append(aluno.user.email)
                elif opcaotmp.count() >= 5:
                    tmpinscritos += 1
                    tmpinscritos_emails.append(aluno.user.email)
                else:
                    ninscritos += 1
                    ninscritos_emails.append(aluno.user.email)
            alunos_list = zip(alunos, opcoes, opcoestemp)

            rano, rsemestre = retrocede_semestre(ano, semestre)

            evento = Evento.get_evento(nome="Indicação de interesse nas propostas pelos estudante", ano=rano, semestre=rsemestre)

            cabecalhos = [
                {"pt": "C", "en": "C"},
                {"pt": "Estudante", "en": "Student"},
                {"pt": "Curso", "en": "Program"},
                {"pt": "e-mail", "en": "e-mail"},
                {"pt": "CR", "en": "CR/GPA", "tipo": "numeral"},
            ]

            context = {
                "alunos_list": alunos_list,
                "num_alunos": alunos.count(),  # Conta soh alunos,
                "inscritos": inscritos,
                "ninscritos": ninscritos,
                "tmpinscritos": tmpinscritos,
                "inscritos_emails": inscritos_emails,
                "ninscritos_emails": ninscritos_emails,
                "tmpinscritos_emails": tmpinscritos_emails,
                "cursos": cursos,
                "num_estudantes_curso": num_estudantes_curso,
                "cabecalhos": cabecalhos,
                "prazo_vencido": evento.endDate < datetime.date.today() if evento and evento.endDate else True,
                "ano": ano,
                "semestre": semestre,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:

        configuracao = get_object_or_404(Configuracao)
        ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)
        selecionada = str(ano) + "." + str(semestre)

        context = {
            "titulo": {"pt": "Estudantes Inscritos", "en": "Enrolled Students"},
            "edicoes": get_edicoes(Aluno)[0],
            "selecionada": selecionada,
        }

    return render(request, "users/estudantes_inscritos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def converte_opcoes(request, ano, semestre):
    """Mostra todos os estudantes que estão se inscrevendo em projetos."""
    for estudante in Aluno.objects.filter(trancado=False, anoPFE=ano, semestrePFE=semestre):
        opcao = Opcao.objects.filter(aluno=estudante, proposta__ano=ano, proposta__semestre=semestre)
        opcaotmp = OpcaoTemporaria.objects.filter(aluno=estudante, proposta__ano=ano, proposta__semestre=semestre)
        if opcao.count() >= 5:
            pass
        elif opcaotmp.count() >= 5:
            for otmp in opcaotmp:
                if otmp.prioridade > 0:  # Caso seja zero, era para ser removido e deve ser ignorado    
                    opcao_final = Opcao.objects.create(aluno=estudante, proposta=otmp.proposta, prioridade=otmp.prioridade)
                    opcao_final.save()
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
    if falha:
        reprovacao = falha.last().nota
    else:
        reprovacao = None

    if request.method == "POST":

        if request.user and request.user.tipo_de_usuario != 4:  # não é admin
            mensagem = "Você não tem autorização de modificar notas!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

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

        media = get_media_alocacao_i(alocacao)["media"]
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
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

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
#@permission_required("users.altera_professor", raise_exception=True)
def estudante_detail(request, primarykey=None):
    """Mostra detalhes sobre o estudante."""
    if primarykey:
        estudante = Aluno.objects.filter(pk=primarykey).first()
    else:
        if request.user.tipo_de_usuario == 1:
            estudante = request.user.aluno
        else:
            return HttpResponse("Estudante não encontrado.", status=401)

    if request.user.tipo_de_usuario == 1 and request.user.aluno != estudante:
        return HttpResponse("Você não tem permissão para acessar essa página.", status=401)
    if request.user.tipo_de_usuario == 3:   # (3, "parceiro")
        return HttpResponse("Você não tem permissão para acessar essa página.", status=401)

    if not estudante:
        return HttpResponse("Estudante não encontrado.", status=401)
    alocacoes = Alocacao.objects.filter(aluno=estudante)

    context = calcula_objetivos(alocacoes)
    context["titulo"] = {"pt": "Estudante", "en": "Student"}
    context["aluno"] = estudante
    context["alocacoes"] = alocacoes
    context["certificados"] = Certificado.objects.filter(usuario=estudante.user)
    context["areast"] = Area.objects.filter(ativa=True)

    # Estilos de Comunicação
    context["estilos"] = EstiloComunicacao.objects.all()
    context["estilos_respostas"] = get_respostas_estilos(estudante.user)

    # Funcionalidade do Grupo
    configuracao = get_object_or_404(Configuracao)
    context["questoes_funcionalidade"] = json.loads(configuracao.questoes_funcionalidade) if configuracao.questoes_funcionalidade else None
    context["funcionalidade_grupo"] = request.user.funcionalidade_grupo

    return render(request, "users/estudante_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def professor_detail(request, primarykey):
    """Mostra detalhes sobre o professor."""
    professor = get_object_or_404(Professor, pk=primarykey)
    context = {
            "titulo": {"pt": "Professor", "en": "Professor"},
            "professor": professor,
            "projetos": Projeto.objects.filter(orientador=professor),
            "coorientacoes": Coorientador.objects.filter(usuario=professor.user).order_by("projeto__ano", "projeto__semestre"),
            "bancas": Banca.get_bancas_com_membro(professor.user),
            "mentorias": Encontro.objects.filter(facilitador=professor.user, projeto__isnull=False).order_by("startDate"),
            "aulas": Evento.objects.filter(tipo_evento__sigla="A", responsavel=professor.user),
            "estilos": EstiloComunicacao.objects.all(),
            "estilos_respostas": get_respostas_estilos(professor.user),
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
        "mentorias": Encontro.objects.filter(facilitador=parceiro.user),
        "aulas": Evento.objects.filter(tipo_evento__sigla="A", responsavel=parceiro.user),
        "bancas": Banca.get_bancas_com_membro(parceiro.user).order_by("startDate"),
    }
    return render(request, "users/parceiro_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def contas_senhas(request, edicao=None):
    """permite selecionar os estudantes para enviar conta e senha."""
    usuario_sem_acesso(request, (4,)) # Soh Adm

    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            estudantes = Aluno.objects.all()
            if edicao != "todas":
                ano, semestre = edicao.split('.')
                estudantes = estudantes.filter(anoPFE=ano, semestrePFE=semestre, trancado=False)
            context = {
                "estudantes": estudantes,
                "template": Carta.objects.filter(template="Envio de Conta para Estudantes").last(),
                "Carta": Carta,
                }
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
        
    else:
        
        context = {
            "titulo": {"pt": "Enviar Contas e Senhas para Estudantes", "en": "Send Accounts and Passwords to Students"},
            "edicoes": get_edicoes(Aluno)[0],
        }
        if edicao:
            context["selecionada"] = edicao

    return render(request, "users/contas_senhas.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def envia_contas_senhas(request):
    """Envia conta e senha para todos os estudantes que estão no semestre."""
    usuario_sem_acesso(request, (4,)) # Soh Adm

    configuracao = get_object_or_404(Configuracao)

    if request.method == "POST":

        estudantes = request.POST.getlist("estudante", None)

        carta = get_object_or_404(Carta, template="Envio de Conta para Estudantes")
        texto = request.POST.get("texto", None)
        if texto:
            carta.texto = texto
            carta.save()

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

            coordenacao = configuracao.coordenacao

            limite_propostas = get_limite_propostas(configuracao)

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

        context = {
            "area_principal": True,
            "mensagem": html.urlize(mensagem),
        }
        return render(request, "generic.html", context=context)

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
def projeto_user(request):
    """Retorna o projeto id associado ao usuário mais recentemente."""
    
    if not request.is_ajax():
        return HttpResponse("Algum erro não identificado.", status=401)
    
    if "user_id" in request.POST:

        user_id = request.POST["user_id"]

        user = get_object_or_404(PFEUser, pk=user_id)

        projeto_id = 0
        if user.tipo_de_usuario == 1: # (1, "estudante"),
            alocacao = Alocacao.objects.filter(aluno=user.aluno).last()
            if alocacao:
                projeto_id = alocacao.projeto.id
        elif user.tipo_de_usuario in [2, 4]: # (2, "professor"),
            projeto = Projeto.objects.filter(orientador=user.professor).last()
            if projeto:
                projeto_id = projeto.id
        elif user.tipo_de_usuario == 3: # (3, "parceiro"),
            conexao = Conexao.objects.filter(parceiro=user.parceiro).last()
            if conexao:
                projeto_id = conexao.projeto.id
        else: 
            return HttpResponse("Algum erro não identificado.", status=401)
    else: 
        return HttpResponse("Algum erro não identificado.", status=401)
    
    return JsonResponse({"projeto_id": projeto_id,})

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

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import html
from django.views import generic
from django.template import Context, Template

from projetos.models import Certificado, Configuracao, Projeto, Conexao, Encontro
from projetos.models import Banca, Area, Coorientador, Avaliacao2, Observacao, Reprovacao
from projetos.models import ObjetivosDeAprendizagem, Evento

from projetos.messages import email
from projetos.support import calcula_objetivos

from administracao.support import get_limite_propostas, usuario_sem_acesso
from administracao.models import Carta

from academica.models import Composicao, CodigoColuna
from academica.support import filtra_composicoes

from operacional.models import Curso

from .forms import PFEUserCreationForm
from .models import PFEUser, Aluno, Professor, Parceiro, Opcao, Administrador
from .models import Alocacao, OpcaoTemporaria, UsuarioEstiloComunicacao
from .support import get_edicoes, adianta_semestre

from academica.models import Exame

from estudantes.models import EstiloComunicacao

# Get an instance of a logger
logger = logging.getLogger(__name__)

@login_required
def user_detail(request, primarykey=0):
    """Retorna a página conforme o perfil do usuário."""

    if primarykey == 0:
        user = request.user
    else:
        user = get_object_or_404(PFEUser, pk=primarykey)

    try:
        if user.tipo_de_usuario == 1:  # aluno
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
    return render(request, "users/profile_detail.html")


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
            if edicao == "todas":
                anosemestre = "todos"
            elif edicao == "trancou":
                anosemestre = "trancou"
            else:
                anosemestre = edicao

            # Conta soh estudantes
            alunos_todos = Aluno.objects\
                .order_by(Lower("user__first_name"), Lower("user__last_name"))

            ano = 0
            semestre = 0

            tabela_alunos = {}
            cursos = []
            totais = {}
            totais["total"] = 0

            # Filtra para estudantes de um curso específico
            if "curso" in request.POST:
                curso_sel = request.POST["curso"]
                if curso_sel != "TE":
                    if curso_sel != 'T':
                        alunos_todos = alunos_todos.filter(curso2__sigla_curta=curso_sel)
                    else:
                        alunos_todos = alunos_todos.filter(curso2__in=cursos_insper)
        
            
            if anosemestre not in ("todos", "trancou"):
                # Estudantes de um semestre em particular
                ano, semestre = map(int, anosemestre.split('.'))

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
                        tabela_alunos[ano][semestre][curso.sigla] =\
                            alunos_semestre.filter(curso2__sigla__exact=curso.sigla).count()
                        totais[curso.sigla] = tabela_alunos[ano][semestre][curso.sigla]
                        totais["total"] += tabela_alunos[ano][semestre][curso.sigla]


                tabela_alunos[ano][semestre]["total"] =\
                    alunos_semestre.count()
                
                alunos_list = alunos_semestre |\
                    alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            else:
                
                # Essa parte está em loop para pegar todos os alunos de todos os semestres
                if anosemestre == "todos":
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
                            tabela_alunos[ano_tmp][semestre_tmp][curso.sigla] =\
                                alunos_semestre.filter(curso2__sigla__exact=curso.sigla).count()
                            if curso.sigla in totais:
                                totais[curso.sigla] += tabela_alunos[ano_tmp][semestre_tmp][curso.sigla]
                            else:
                                totais[curso.sigla] = tabela_alunos[ano_tmp][semestre_tmp][curso.sigla]
                            tabela_alunos[ano_tmp][semestre_tmp]["total"] += tabela_alunos[ano_tmp][semestre_tmp][curso.sigla]
                            totais["total"] += tabela_alunos[ano_tmp][semestre_tmp][curso.sigla]

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

            cabecalhos = ["Nome", "Matrícula", "e-mail", "Curso", "Período", "Projeto", "Linkedin", "Celular", ]
            
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
                "ano_semestre": str(ano)+"."+str(semestre),
                "loop_anos": range(2018, configuracao.ano+1),
                "cabecalhos": cabecalhos,
                "curso_sel": curso_sel,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Aluno)
        titulo = "Estudantes"
        context = {
            "edicoes": edicoes,
            "titulo": titulo,
            "cursos": cursos_insper,
            "cursos_externos": cursos_externos,
        }

    return render(request, "users/estudantes_lista.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_notas(request, professor=None):
    """Gera lista com todos os alunos já registrados."""
    configuracao = get_object_or_404(Configuracao)

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
                projetos = Projeto.objects.all()
                coorientacoes = Coorientador.objects.filter(usuario=user).values_list("projeto", flat=True)
                projetos = projetos.filter(orientador=user.professor) | projetos.filter(id__in=coorientacoes)
                alunos_list = alunos_list.filter(alocacao__projeto__in=projetos)

            # Caso o aluno tenha repetido e esteja fazendo de novo o Capstone
            alunos_semestre = alunos_list\
                .filter(alocacao__projeto__ano=ano,
                        alocacao__projeto__semestre=semestre)\
                .distinct()

            # Caso o aluno tenha repetido e esteja fazendo de novo o Capstone
            alunos_list = alunos_semestre |\
                alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            context = {
                "alunos_list": alunos_list,
                "configuracao": configuracao,
                "ano": ano,
                "semestre": semestre,
                "ano_semestre": str(ano)+"."+str(semestre),
                "loop_anos": range(2018, configuracao.ano+1),
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        informacoes = [
            (".pesos_aval", "Pesos", False),
        ]
        edicoes, _, _ = get_edicoes(Aluno)
        context = {
            "titulo": "Avaliações por Estudante",
            "edicoes": edicoes,
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

        alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre, aluno__trancado=False, aluno__externo__isnull=True)
        for alocacao in alocacoes:
            notas = alocacao.get_notas
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
                        linha += [f"{alocacao.get_media['media']:.4f}".replace('.',',')]
                        #linha += ["MMM"]
                    else:
                        linha += [""]
                    
            dataset.append(linha)

        csv = dataset.export("csv", quotechar='"', dialect="excel")
        #csv_with_trailing_commas = csv.replace("\r\n", ",\r\n")  # Caso precise colocar uma vírgula no final de cada linha
        response = HttpResponse(csv, content_type="text/csv")
        response.write(u"\ufeff".encode("utf-8-sig"))

        response["Content-Disposition"] = "attachment; filename=notas_"+str(ano)+"_"+str(semestre)+".csv"
        
        return response
    
    colunas = CodigoColuna.objects.filter(exame__in=exames, ano=ano, semestre=semestre)

    context = {
        "exames": exames,
        "colunas": colunas,
        "anosemestre": anosemestre,
    }
    return render(request, "users/blackboard_notas.html", context=context)
    

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_objetivos(request):
    """Gera lista com todos os alunos já registrados."""
    configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = map(int, request.POST["edicao"].split('.'))
            
            # Conta soh alunos não trancados
            alunos_list = Aluno.objects.filter(trancado=False).order_by(Lower("user__first_name"), Lower("user__last_name"))

            alunos_semestre = alunos_list\
                .filter(alocacao__projeto__ano=ano,
                        alocacao__projeto__semestre=semestre)\
                .distinct()

            alunos_list = alunos_semestre |\
                alunos_list.filter(anoPFE=ano, semestrePFE=semestre).distinct()

            # Filtra os Objetivos de Aprendizagem do semestre
            objetivos = ObjetivosDeAprendizagem.objects.all()

            #Nao está filtrando todos os semestres
            mes = 3 if semestre == 1 else 9
            
            data_projeto = datetime.datetime(ano, mes, 1)

            objetivos = objetivos.filter(data_inicial__lt=data_projeto)
            objetivos = objetivos.filter(data_final__gt=data_projeto) | objetivos.filter(data_final__isnull=True)

            objetivos = objetivos.order_by("ordem")

            context = {
                "alunos_list": alunos_list,
                "configuracao": configuracao,
                "ano": ano,
                "semestre": semestre,
                "ano_semestre": str(ano)+'.'+str(semestre),
                "loop_anos": range(2018, configuracao.ano+1),
                "objetivos": objetivos,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, _, _ = get_edicoes(Aluno)
        context = {
            "titulo": "Objetivos de Aprendizagem por Estudante",
            "edicoes": edicoes,
            }

    return render(request, "users/estudantes_objetivos.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudantes_inscritos(request):
    """Mostra todos os alunos que estão se inscrevendo em projetos."""
    if request.is_ajax():
        if "edicao" in request.POST:
            ano, semestre = map(int, request.POST["edicao"].split('.'))

            alunos = Aluno.objects.filter(trancado=False)\
                .filter(anoPFE=ano, semestrePFE=semestre)

            # Conta soh alunos
            num_alunos = alunos.count()

            # Conta estudantes de cada curso
            cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")
            num_estudantes_curso = {}
            for curso in cursos:
                qtd = alunos.filter(curso2__sigla__exact=curso.sigla).count()
                if qtd: num_estudantes_curso[curso] = qtd

            inscritos = 0
            ninscritos = 0
            tmpinscritos = 0
            opcoes = []
            opcoestemp = []
            
            for aluno in alunos:
                opcao = Opcao.objects.filter(aluno=aluno)\
                    .filter(proposta__ano=ano, proposta__semestre=semestre)
                opcoes.append(opcao)
                opcaotmp = OpcaoTemporaria.objects.filter(aluno=aluno)\
                    .filter(proposta__ano=ano, proposta__semestre=semestre)
                opcoestemp.append(opcaotmp)
                if opcao.count() >= 5:
                    inscritos += 1
                elif opcaotmp.count() >= 5:
                    tmpinscritos += 1
                else:
                    ninscritos += 1
            alunos_list = zip(alunos, opcoes, opcoestemp)

            context = {
                "alunos_list": alunos_list,
                "num_alunos": num_alunos,
                "inscritos": inscritos,
                "ninscritos": ninscritos,
                "tmpinscritos": tmpinscritos,
                "cursos": cursos,
                "num_estudantes_curso": num_estudantes_curso,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:

        edicoes, _, _ = get_edicoes(Aluno)

        configuracao = get_object_or_404(Configuracao)
        ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)
        selecionada = str(ano) + "." + str(semestre)

        informacoes = [
            ("#EstudantesTable tr > *:nth-child(3)", "Curso"),
            ("#EstudantesTable tr > *:nth-child(4)", "CR", False),
        ]

        context = {
            "titulo": "Estudantes Inscritos",
            "edicoes": edicoes,
            "selecionada": selecionada,
            "informacoes": informacoes,
        }

    return render(request, "users/estudantes_inscritos.html", context=context)


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
                reg = Reprovacao.create(alocacao=alocacao)
            reg.nota = rep
            reg.save()

        mensagem = "Notas de <b>" + alocacao.aluno.user.get_full_name()
        mensagem += "</b> atualizadas:<br>\n"

        mensagem += "&nbsp;&nbsp;Peso Final = "
        mensagem += str(round(alocacao.get_media["pesos"]*100, 2)) + "% <br>\n"

        mensagem += "&nbsp;&nbsp;Média Final = "
        mensagem += str(round(alocacao.get_media["media"], 2)) + "<br>\n"
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
        "alocacao": alocacao,
        "composicoes": composicoes,
        "avaliacoes": avaliacoes,
        "observacoes": observacoes,
        "reprovacao": reprovacao,
    }

    return render(request, "users/edita_nota.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def estudante_detail(request, primarykey):
    """Mostra detalhes sobre o estudante."""
    estudante = Aluno.objects.filter(pk=primarykey).first()
    if not estudante:
        return HttpResponse("Estudante não encontrado.", status=401)
    alocacoes = Alocacao.objects.filter(aluno=estudante)

    context = calcula_objetivos(alocacoes)
    context["titulo"] = estudante.user.get_full_name()
    context["aluno"] = estudante
    context["alocacoes"] = alocacoes
    context["certificados"] = Certificado.objects.filter(usuario=estudante.user)
    context["TIPO_DE_CERTIFICADO"] = Certificado.TIPO_DE_CERTIFICADO
    context["areast"] = Area.objects.filter(ativa=True)

    return render(request, "users/estudante_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def professor_detail(request, primarykey):
    """Mostra detalhes sobre o professor."""
    context = {"professor": get_object_or_404(Professor, pk=primarykey)}
    context["titulo"] = context["professor"].user.get_full_name()

    context["projetos"] = Projeto.objects.filter(orientador=context["professor"]).order_by("ano", "semestre")

    context["coorientacoes"] = Coorientador.objects.filter(usuario=context["professor"].user).order_by("projeto__ano", "projeto__semestre")

    context["bancas"] = ((Banca.objects.filter(membro1=context["professor"].user) |
                          Banca.objects.filter(membro2=context["professor"].user) |
                          Banca.objects.filter(membro3=context["professor"].user) |
                          Banca.objects.filter(projeto__orientador=context["professor"])
                            )).order_by("startDate")
    
    context["mentorias"] = Encontro.objects.filter(facilitador=context["professor"].user, projeto__isnull=False).order_by("startDate")
    
    context["aulas"] = Evento.objects.filter(tipo_de_evento=12, responsavel=context["professor"].user) # (12, 'Aula', 'lightgreen'),

    context["estilos"] = EstiloComunicacao.objects.all()
    context["estilos_usuario"] = UsuarioEstiloComunicacao.objects.filter(usuario=context["professor"].user)
    # for estilo in context["estilos_usuario"]:
    #     print(estilo.estilo_comunicacao)
    #     print(estilo.prioridade_resposta1, estilo.prioridade_resposta2, estilo.prioridade_resposta3, estilo.prioridade_resposta4)

        


    return render(request, "users/professor_detail.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def parceiro_detail(request, primarykey=None):
    """Mostra detalhes sobre o parceiro."""

    if not primarykey:
        return HttpResponse("Parceiro não encontrado.", status=401)
    
    parceiro = get_object_or_404(Parceiro, pk=primarykey)
    
    bancas = (Banca.objects.filter(membro1=parceiro.user) |
              Banca.objects.filter(membro2=parceiro.user) |
              Banca.objects.filter(membro3=parceiro.user))

    bancas = bancas.order_by("startDate")

    context = {
        "titulo": parceiro.user.get_full_name(),
        "parceiro": parceiro,
        "conexoes": Conexao.objects.filter(parceiro=parceiro),
        "mentorias": Encontro.objects.filter(facilitador=parceiro.user),
        "aulas": Evento.objects.filter(tipo_de_evento=12, responsavel=parceiro.user),
        "bancas": bancas,
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
            "titulo": "Enviar Contas e Senhas para Estudantes",
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
            check = email(subject, recipient_list, message_email)
            if check != 1:
                error_message = "Problema no envio de e-mail, subject=" + subject + ", message=" + message_email + ", recipient_list=" + str(recipient_list)
                logger.error(error_message)
                mensagem = "Erro de conexão, contacte:lpsoares@insper.edu.br"

        context = {
            "area_principal": True,
            "mensagem": html.urlize(mensagem),
        }
        return render(request, "generic.html", context=context)

    return HttpResponse("Algum erro não identificado.", status=401)


#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import os
import datetime
import re           #regular expression (para o import)
import csv
import sys

from io import BytesIO # Para gerar o PDF
import dateutil.parser

import tablib
from tablib import Databook
from icalendar import Calendar, Event, vCalAddress

from xhtml2pdf import pisa # Para gerar o PDF

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models.functions import Lower
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.template.loader import get_template
from django.utils import timezone

from django.utils import text

from users.models import PFEUser, Aluno, Professor, Parceiro, Administrador, Opcao, Alocacao, Areas
from .models import Projeto, Proposta, Organizacao, Configuracao, Evento, Anotacao, Coorientador
from .models import Feedback, Certificado
from .models import Banca, Documento, Encontro, Banco, Reembolso, Aviso, Entidade, Conexao
#from .models import Disciplina
from .models import ObjetidosDeAprendizagem, Avaliacao

from .models import get_upload_path

from .resources import ProjetosResource, OrganizacoesResource, OpcoesResource, UsuariosResource
from .resources import AlunosResource, ProfessoresResource
from .resources import ConfiguracaoResource, DisciplinasResource
from .messages import email, create_message, message_reembolso

@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    if Configuracao.objects.all().first().manutencao:
        return render(request, 'projetos/manutencao.html')
    #num_visits = request.session.get('num_visits', 0) # Numero de visitas a página.
    #request.session['num_visits'] = num_visits + 1
    configuracao = Configuracao.objects.first()
    context = {
        'configuracao': configuracao,
    }
    #'num_visits': num_visits,
    return render(request, 'index.html', context=context)

@login_required
def index_aluno(request):
    """Mostra página principal do usuário aluno."""

    usuario = PFEUser.objects.get(pk=request.user.pk)
    if usuario.tipo_de_usuario == 1:
        aluno = Aluno.objects.get(pk=request.user.pk)
        projeto = Projeto.objects.filter(alocacao__aluno=aluno).last()
    else:
        projeto = None

    professor_id = 0
    if usuario.tipo_de_usuario == 2 or usuario.tipo_de_usuario == 4:
        try:
            professor_id = Professor.objects.get(user__pk=request.user.pk).id
        except Professor.DoesNotExist:
            pass
            # Administrador não possui também conta de professor

    configuracao = Configuracao.objects.first()
    vencido = timezone.now() > configuracao.prazo
    context = {
        'projeto': projeto,
        'configuracao': configuracao,
        'vencido': vencido,
        'professor_id': professor_id,
    }
    return render(request, 'index_aluno.html', context=context)

@login_required
def projeto_detalhe(request, primarykey):
    """Exibe um projeto para o aluno aplicar nele, com seus detalhes."""
    projeto = Projeto.objects.get(pk=primarykey)
    context = {
        'projeto': projeto,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/projeto_detalhe.html', context=context)

@login_required
def selecao_projetos(request):
    """Exibe todos os projetos para os alunos aplicarem."""
    warnings = ""
    configuracao = Configuracao.objects.first()
    projeto_list = Projeto.objects.filter(ano=configuracao.ano).\
                                   filter(semestre=configuracao.semestre).\
                                   filter(disponivel=True)
    if request.method == 'POST':
        if timezone.now() > configuracao.prazo:
            #return HttpResponse("Prazo para seleção de projetos vencido!")
            #<br>Hora atual:  "+str(timezone.now())+"<br>Hora limite:"+str(configuracao.prazo)
            mensagem = "Prazo para seleção de projetos vencido!"
            context = {
                "area_aluno": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)
        prioridade = {}
        for projeto in projeto_list:
            check_values = request.POST.get('selection'+str(projeto.pk), "0")
            prioridade[projeto.pk] = check_values
        for i in range(1, len(projeto_list)+1):
            if i < 6 and list(prioridade.values()).count(str(i)) == 0:
                warnings += "Nenhum projeto com prioridade "+str(i)+"\n"
            if list(prioridade.values()).count(str(i)) > 1:
                warnings += "Mais de um projeto com prioridade "+str(i)+"\n"
        if warnings == "":
            aluno = Aluno.objects.get(pk=request.user.pk)
            for projeto in projeto_list:
                if prioridade[projeto.pk] != "0":
                    if not aluno.opcoes.filter(pk=projeto.pk): # Se lista for vazia
                        Opcao.objects.create(aluno=aluno, projeto=projeto,
                                             prioridade=int(prioridade[projeto.pk]))
                    elif Opcao.objects.get(aluno=aluno, projeto=projeto).\
                                       prioridade != int(prioridade[projeto.pk]):
                        opc = Opcao.objects.get(aluno=aluno, projeto=projeto)
                        opc.prioridade = int(prioridade[projeto.pk])
                        opc.save()
                else:
                    if aluno.opcoes.filter(pk=projeto.pk): # Se lista não for vazia
                        Opcao.objects.filter(aluno=aluno, projeto=projeto).delete()
            message = create_message(aluno, configuracao.ano, configuracao.semestre)

            subject = 'PFE : '+aluno.user.username
            recipient_list = ['pfeinsper@gmail.com', aluno.user.email,]
            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

            context = {'message': message,}
            return render(request, 'projetos/confirmacao.html', context)
        else:
            context = {'warnings': warnings,}
            return render(request, 'projetos/projetosincompleto.html', context)
    else:
        opcoes_list = Opcao.objects.filter(aluno=Aluno.objects.get(pk=request.user.pk))
        context = {
            'projeto_list': projeto_list,
            'opcoes_list': opcoes_list,
            'configuracao': configuracao,
            'warnings': warnings,
        }
        return render(request, 'projetos/selecao_projetos.html', context)

# PROVAVELMENTE NAO MAIS USADA
def ordena_projetos(disponivel=True, ano=0, semestre=0):
    """Gera lista com projetos ordenados pelos com maior interesse pelos alunos."""
    configuracao = Configuracao.objects.all().first()

    if ano == 0:
        ano = configuracao.ano
    if semestre == 0:
        semestre = configuracao.semestre

    opcoes_list = []
    if disponivel:
        projetos = Projeto.objects.filter(ano=ano).\
                               filter(semestre=semestre).\
                               filter(disponivel=True)
    else:
        projetos = Projeto.objects.filter(ano=ano).\
                               filter(semestre=semestre)
    for projeto in projetos:
        opcoes = Opcao.objects.filter(projeto=projeto)
        opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
        opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=ano).\
                                       filter(aluno__semestrePFE=semestre)
        count = 0
        for opcao in opcoes_validas:
            if opcao.prioridade <= 5:
                count += 1
        opcoes_list.append(count)
    mylist = zip(projetos, opcoes_list)
    mylist = sorted(mylist, key=lambda x: x[1], reverse=True)
    return mylist


def ordena_propostas(disponivel=True, ano=0, semestre=0):
    """Gera lista com propostas ordenados pelos com maior interesse pelos alunos."""
    configuracao = Configuracao.objects.all().first()

    if ano == 0:
        ano = configuracao.ano
    if semestre == 0:
        semestre = configuracao.semestre

    opcoes_list = []
    if disponivel:
        propostas = Proposta.objects.filter(ano=ano).\
                               filter(semestre=semestre).\
                               filter(disponivel=True)
    else:
        propostas = Proposta.objects.filter(ano=ano).\
                               filter(semestre=semestre)
    for proposta in propostas:
        opcoes = Opcao.objects.filter(proposta=proposta)
        opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
        opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=ano).\
                                       filter(aluno__semestrePFE=semestre)
        count = 0
        for opcao in opcoes_validas:
            if opcao.prioridade <= 5:
                count += 1
        opcoes_list.append(count)
    mylist = zip(propostas, opcoes_list)
    mylist = sorted(mylist, key=lambda x: x[1], reverse=True)
    return mylist

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def histograma(request):
    """Exibe um histograma com a procura dos projetos pelos alunos."""

    if request.is_ajax():
        if 'topicId' in request.POST:
            # if request.POST['topicId'] != 'todas':
            periodo = request.POST['topicId'].split('.')
            #     projetos = Areas.objects.filter(projeto__ano=int(periodo[0])).\
            #                                 filter(projeto__semestre=int(periodo[1]))
            mylist = ordena_propostas(ano=int(periodo[0]), semestre=int(periodo[1]))
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        mylist = ordena_propostas()

    context = {'mylist': mylist}
    return render(request, 'projetos/histograma.html', context)

def get_next_opcao(numb, opcoes):
    """Busca proxima opcao do aluno."""
    numb += 1
    lopcoes = opcoes.filter(prioridade=numb)
    num_total_projetos = Projeto.objects.all().count() # Depois filtrar melhor
    while (not lopcoes) and (numb <= num_total_projetos):
        numb += 1
        lopcoes = opcoes.filter(prioridade=numb)
    if lopcoes: # Se a lista tem algum elemento
        return numb
    else:
        return 0

def get_opcao(numb, opcoes, min_group, max_group, projetos_ajustados):
    """Pega a opcao de preferencia do aluno se possivel."""
    configuracao = Configuracao.objects.all().first()
    opcao = opcoes.get(prioridade=numb)
    while True:
        opcoesp = Opcao.objects.filter(projeto=opcao.projeto)
        opcoesp_alunos = opcoesp.filter(aluno__user__tipo_de_usuario=1)
        opcoesp_validas = opcoesp_alunos.filter(aluno__anoPFE=configuracao.ano).\
                                         filter(aluno__semestrePFE=configuracao.semestre)

        if len(opcoesp_validas) >= min_group: #Checa se projeto tem numero minimo de aplicantes
            pass
            # checa se alunos no projeto ja tem CR maior dos que ja estao no momento no projeto
        crh = 0
        for optv in projetos_ajustados[opcao.projeto]:
            if optv.aluno.cr > opcao.aluno.cr:
                crh += 1 #conta cada aluno com cr maior que o aluno sendo alocado
        if crh < max_group:
            break #se tudo certo retorna esse projeto mesmo
        # Nao achou tentando outra opcao
        numbx = get_next_opcao(numb, opcoes)
        if numbx != 0:
            opcao = opcoes.get(prioridade=numbx)
            break
        else:  # caso nao encontre mais nenhuma opcao valida
            return None
    return opcao

def limita_grupo(max_group, ano, semestre, projetos_ajustados):
    """
        Removendo alunos de grupos superlotados.
        max_group: quantidade máxima de alunos por grupo    """

    pref_pri_cr = 0.1  #talvez remover

    balanceado = True
    balanceado_max = False
    count = 200 # Numero máximo de iterações, para não travar
    while (not balanceado_max) and (count > 0):
        count -= 1 # para nao correr o risco de um loop infinito
        balanceado_max = True
        for projeto, ops in projetos_ajustados.items():
            if len(ops) > max_group: # Checa se projeto esta superlotado
                remove_opcao = None
                for option in ops:
                    if option.prioridade < 5: #Nao move se prioridade < que 5 (REVER)
                        if remove_opcao is None:
                            remove_opcao = option
                        elif (\
                option.aluno.cr * (1-((option.prioridade-1)*pref_pri_cr))) \
                < (remove_opcao.aluno.cr * (1-((remove_opcao.prioridade-1) * pref_pri_cr))):
                            remove_opcao = option
                if remove_opcao is not None:
                    opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno).\
                                            filter(projeto__ano=ano).\
                                            filter(projeto__semestre=semestre)
                    next_op = get_next_opcao(remove_opcao.prioridade, opcoes)
                    if next_op != 0:
                        #busca nas opcoes do aluno
                        #op2 = get_opcao(next_op, opcoes, min_group,
                        op2 = get_opcao(next_op, opcoes, 3,
                                        max_group, projetos_ajustados)
                        if op2: #op2 != None
                            balanceado_max = False
                            balanceado = False
                            #menor_grupo = 1
                            projetos_ajustados[projeto].remove(remove_opcao)
                            projetos_ajustados[op2.projeto].append(op2)
                            #print("Movendo(a) "+remove_opcao.aluno.user.first_name.lower()\
                            #+" (DE): "+projeto.titulo+" (PARA):"+op2.projeto.titulo)
    return balanceado

def desmonta_grupo(min_group, ano, semestre, projetos_ajustados):
    """Realocando alunos de grupos muito pequenos (um aluno por vez)."""

    #menor_grupo = 1 # usado para elimnar primeiro grupos de 1, depois de 2, etc


    remove_opcao = None
    remove_projeto = None
    menor_opcao = sys.maxsize

    # identifica projeto potencial para desmontar
    for projeto, ops in projetos_ajustados.items():
        menor_opcao_tmp = 0
        if ops and (len(ops) < min_group):
            opcoes = Opcao.objects.filter(projeto=projeto)
            for opt in opcoes:
                if opt.prioridade <= 5:
                    menor_opcao_tmp += (6-opt.prioridade)**2 # prioridade 1 tem mais chances
            if menor_opcao_tmp < menor_opcao:
                remove_projeto = projeto
                menor_opcao = menor_opcao_tmp
    #print(remove_projeto)

    if remove_projeto:
        for remove_opcao in projetos_ajustados[remove_projeto]:
            opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno).\
                                    filter(projeto__ano=ano).\
                                    filter(projeto__semestre=semestre)
            next_op = get_next_opcao(remove_opcao.prioridade, opcoes)
            if next_op != 0:
                #busca nas opcoes do aluno
                #op2 = get_opcao(next_op, opcoes, min_group, max_group, projetos_ajustados)
                op2 = get_opcao(next_op, opcoes, min_group, 5, projetos_ajustados)
                if op2: #op2 != None:
                    #balanceado = False
                    #menor_grupo = 1
                    projetos_ajustados[remove_projeto].remove(remove_opcao)
                    projetos_ajustados[op2.projeto].append(op2)
                    #print("Movendo(b) "+remove_opcao.aluno.user.first_name.lower()+\
                    # " (DE): "+remove_projeto.titulo+" (PARA):"+op2.projeto.titulo)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def propor(request):
    """Monta grupos de PFE."""
    ############################################
    ## COLOCAR ESSE VALOR ACESSIVEL NO SISTEMA #
    ############################################
    #pref_pri_cr = 0.1  # Ficar longe da prioridade tem um custo de 5% na selecao do projeto

    configuracao = Configuracao.objects.all().first()
    projeto_list = []
    opcoes_list = []
    projetos = Projeto.objects.filter(disponivel=True).\
                               filter(ano=configuracao.ano).\
                               filter(semestre=configuracao.semestre)

    if request.method == 'POST':
        min_group = int(request.POST.get('min', 1))
        max_group = int(request.POST.get('max', 5))
        projetos_ajustados = {}
        alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
                               filter(anoPFE=configuracao.ano).\
                               filter(semestrePFE=configuracao.semestre)

        for aluno in alunos: #Checa se o CR de todos os alunos esta coreto
            if aluno.cr < 5.0:
                #return HttpResponse("Aluno: "+aluno.user.first_name+" "+aluno.user.last_name+\
                #                    " ("+aluno.user.username+') com CR = '+str(aluno.cr))
                mensagem = "Detectado aluno: "+aluno.user.first_name+" "+aluno.user.last_name+\
                                    " ("+aluno.user.username+') com CR = '+str(aluno.cr)
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)

        #Cria Lista para todos os projetos
        for projeto in projetos:
            projetos_ajustados[projeto] = []

        #Posiciona os alunos nas suas primeiras opcoes (supondo projeto permitir)
        for aluno in alunos:
            opcoes = Opcao.objects.filter(aluno=aluno).\
                                   filter(projeto__ano=configuracao.ano).\
                                   filter(projeto__semestre=configuracao.semestre)
            if len(opcoes) >= 5: # checa se aluno preencheu formulario
                #busca nas opcoes do aluno
                opcoes1 = get_opcao(1, opcoes, min_group, max_group, projetos_ajustados)
                projetos_ajustados[opcoes1.projeto].append(opcoes1)

        #Posiciona os alunos nas suas melhores opcoes sem estourar o tamanho do grupo
        balanceado = False
        #count = 200
        count = 8
        while (not balanceado) and (count > 0):
            #balanceado = True
            balanceado = False

            limita_grupo(max_group, configuracao.ano, configuracao.semestre, projetos_ajustados)
            desmonta_grupo(min_group, configuracao.ano, configuracao.semestre, projetos_ajustados)

            # Próxima estapa seria puxar de volta os alunos que ficaram muito para frente nas opções

            count -= 1


        # if (menor_grupo < min_group) and balanceado: #caso todos grupos com menor_grupo ja foram
        #     menor_grupo += 1
        #     balanceado = False

        #Cria lista para enviar para o template html
        for projeto, ops in projetos_ajustados.items():
            if ops: #len(ops) > 0
                projeto_list.append(projeto)
                opcoes_list.append(ops)
    else:
        for projeto in projetos:
            opcoes = Opcao.objects.filter(projeto=projeto)
            opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
            opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).\
                                           filter(aluno__semestrePFE=configuracao.semestre)
            opcoes1 = opcoes_validas.filter(prioridade=1)
            if opcoes1: #len(opcoes1) > 0
                projeto_list.append(projeto)
                opcoes_list.append(opcoes1)

    mylist = zip(projeto_list, opcoes_list)
    context = {
        'mylist': mylist,
        'length': len(projeto_list),
    }
    return render(request, 'projetos/propor.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def administracao(request):
    """Mostra página principal para administração do sistema."""
    return render(request, 'index_admin.html')

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def index_operacional(request):
    """Mostra página principal para equipe operacional."""
    return render(request, 'index_operacional.html')

@login_required
@permission_required("users.altera_valores", login_url='/projetos/')
def index_organizacao(request):
    """Mostra página principal do usuário que é um parceiro de uma organização."""
    return render(request, 'index_organizacao.html')

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def index_professor(request):
    """Mostra página principal do usuário professor."""

    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        #return HttpResponse("Você não está cadastrado como professor")
        mensagem = "Você não está cadastrado como professor!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    professor_id = 0
    try:
        professor_id = Professor.objects.get(user__pk=request.user.pk).id
    except Professor.DoesNotExist:
        pass
        # Administrador não possui também conta de professor

    context = {
        'professor_id': professor_id,
    }
    return render(request, 'index_professor.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def projeto_completo(request, primakey):
    """Mostra um projeto por completo."""
    configuracao = Configuracao.objects.all().first()
    projeto = Projeto.objects.filter(pk=primakey).first()  # acho que tem de ser get
    opcoes = Opcao.objects.filter(projeto=projeto)
    conexoes = Conexao.objects.filter(projeto=projeto)
    coorientadores = Coorientador.objects.filter(projeto=projeto)
    context = {
        'configuracao': configuracao,
        'projeto': projeto,
        'opcoes': opcoes,
        'conexoes': conexoes,
        'coorientadores': coorientadores,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/projeto_completo.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def proposta_completa(request, primakey):
    """Mostra um projeto por completo."""
    configuracao = Configuracao.objects.all().first()
    proposta = Proposta.objects.get(pk=primakey)
    projeto = None
    if proposta.fechada:
        projeto = Projeto.objects.get(proposta=proposta)
    
    opcoes = Opcao.objects.filter(proposta=proposta)
    context = {
        'configuracao': configuracao,
        'proposta': proposta,
        'opcoes': opcoes,
        'MEDIA_URL' : settings.MEDIA_URL,
        'projeto' : projeto,
    }
    return render(request, 'projetos/proposta_completa.html', context=context)


def get_areas(entrada):
    """Retorna dicionário com as áreas de interesse da lista de entrada."""

    areaspfe = {}

    areaspfe['Inovação Social'] =\
        entrada.filter(inovacao_social=True).count()

    areaspfe['Ciência dos Dados'] =\
        entrada.filter(ciencia_dos_dados=True).count()

    areaspfe['Modelagem 3D'] =\
        entrada.filter(modelagem_3D=True).count()

    areaspfe['Manufatura'] =\
        entrada.filter(manufatura=True).count()

    areaspfe['Resistência dos Materiais'] =\
        entrada.filter(resistencia_dos_materiais=True).count()

    areaspfe['Modelagem de Sistemas'] =\
        entrada.filter(modelagem_de_sistemas=True).count()

    areaspfe['Controle e Automação'] =\
        entrada.filter(controle_e_automacao=True).count()

    areaspfe['Termodinâmica'] =\
        entrada.filter(termodinamica=True).count()

    areaspfe['Fluidodinâmica'] =\
        entrada.filter(fluidodinamica=True).count()

    areaspfe['Eletrônica Digital'] =\
        entrada.filter(eletronica_digital=True).count()

    areaspfe['Programação'] =\
        entrada.filter(programacao=True).count()

    areaspfe['Inteligência Artificial'] =\
        entrada.filter(inteligencia_artificial=True).count()

    areaspfe['Banco de Bados'] =\
        entrada.filter(banco_de_dados=True).count()

    areaspfe['Computação em Nuvem'] =\
        entrada.filter(computacao_em_nuvem=True).count()

    areaspfe['Visão Computacional'] =\
        entrada.filter(visao_computacional=True).count()

    areaspfe['Computação de Alto Desempenho'] =\
        entrada.filter(computacao_de_alto_desempenho=True).count()

    areaspfe['Robótica'] =\
        entrada.filter(robotica=True).count()

    areaspfe['Realidade Virtual e Aumentada'] =\
        entrada.filter(realidade_virtual_aumentada=True).count()

    areaspfe['Protocolos de Comunicação'] =\
        entrada.filter(protocolos_de_comunicacao=True).count()

    areaspfe['Eficiencia Energética'] =\
        entrada.filter(eficiencia_energetica=True).count()

    areaspfe['Administração, Economia e Finanças'] =\
        entrada.filter(administracao_economia_financas=True).count()

    return areaspfe

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def distribuicao_areas(request, tipo):
    """Mostra distribuição por área de interesse dos alunos, propostas e projetos."""

    periodo = ""
    if tipo == "alunos":

        alunos = Aluno.objects.filter(user__tipo_de_usuario=1)

        if request.is_ajax():
            if 'topicId' in request.POST:
                if request.POST['topicId'] != 'todas':
                    periodo = request.POST['topicId'].split('.')
                    alunos = alunos.filter(anoPFE=int(periodo[0])).\
                                    filter(semestrePFE=int(periodo[1]))
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

        context = {
            'areaspfe': get_areas(alunos),
            'tipo': tipo,
            'periodo': periodo,
        }

    elif tipo == "propostas":

        propostas = Areas.objects.all()

        if request.is_ajax():
            if 'topicId' in request.POST:
                if request.POST['topicId'] != 'todas':
                    periodo = request.POST['topicId'].split('.')

                    propostas = Areas.objects.filter(proposta__ano=int(periodo[0])).\
                                             filter(proposta__semestre=int(periodo[1]))
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

        context = {
            'areaspfe': get_areas(propostas),
            'tipo': tipo,
            'periodo': periodo,
        }

    elif tipo == "projetos":

        projetos = Areas.objects.all()

        if request.is_ajax():
            if 'topicId' in request.POST:
                if request.POST['topicId'] != 'todas':
                    periodo = request.POST['topicId'].split('.')
                    projetos = Areas.objects.filter(projeto__ano=int(periodo[0])).\
                                             filter(projeto__semestre=int(periodo[1]))
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

        context = {
            'areaspfe': get_areas(projetos),
            'tipo': tipo,
            'periodo': periodo,
        }

    else:
        return HttpResponse("Algum erro não identificado.", status=401)

    return render(request, 'projetos/distribuicao_areas.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacoes_lista(request):
    """Exibe todas as organizações que já submeteram projetos."""
    organizacoes = Organizacao.objects.all()
    fechados = []
    desde = []
    contato = []
    for organizacao in organizacoes:
        projetos = Projeto.objects.filter(organizacao=organizacao).order_by("ano", "semestre")
        if projetos.first():
            desde.append(str(projetos.first().ano)+"."+str(projetos.first().semestre))
        else:
            desde.append("---------")

        #anot = Anotacao.objects.filter(organizacao=organizacao).order_by("momento").last()
        anot = Anotacao.objects.filter(organizacao=organizacao).order_by("momento").last()
        if anot:
            contato.append(anot)
        else:
            contato.append("---------")

        fechados.append(projetos.filter(alocacao__isnull=False).distinct().count())

    organizacoes_list = zip(organizacoes, fechados, desde, contato)
    total_organizacoes = Organizacao.objects.all().count()
    total_submetidos = Projeto.objects.all().count()
    total_fechados = Projeto.objects.filter(alocacao__isnull=False).distinct().count()
    context = {
        'organizacoes_list': organizacoes_list,
        'total_organizacoes': total_organizacoes,
        'total_submetidos': total_submetidos,
        'total_fechados': total_fechados,
        'meses3': datetime.date.today() - datetime.timedelta(days=100),
        'filtro': "todas",
        }
    return render(request, 'projetos/organizacoes_lista.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacao_completo(request, org): #acertar isso para pk
    """Exibe detalhes das organizações parceiras."""
    try:
        organizacao = Organizacao.objects.get(id=org)
    except Organizacao.DoesNotExist:
        return HttpResponseNotFound('<h1>Organização não encontrada!</h1>')
    context = {
        'organizacao': organizacao,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/organizacao_completo.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def cria_anotacao(request, login): #acertar isso para pk
    """Cria um anotação para uma organização parceira."""
    try:
        organizacao = Organizacao.objects.get(id=login)
    except Proposta.DoesNotExist:
        return HttpResponseNotFound('<h1>Organização não encontrada!</h1>')

    if request.method == 'POST':
        if 'anotacao' in request.POST:
            anotacao = Anotacao.create(organizacao)
            anotacao.autor = PFEUser.objects.get(pk=request.user.pk)
            anotacao.texto = request.POST['anotacao']
            anotacao.tipo_de_retorno = int(request.POST['contato'])
            anotacao.save()
            if 'data_hora' in request.POST:
                try:
                    anotacao.momento = dateutil.parser.parse(request.POST['data_hora'])
                except (ValueError, OverflowError):
                    anotacao.momento = datetime.datetime.now()
            anotacao.save()
            mensagem = "Anotação criada."
        else:
            mensagem = "<h3 style='color:red'>Anotação não criada.<h3>"
        context = {
            "area_principal": True,
            "organizacao_completo": login,
            "organizacoes_lista": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    else:
        context = {
            'organizacao': organizacao,
            'data_hora': datetime.datetime.now(),
        }
        return render(request, 'projetos/cria_anotacao.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def export(request, modelo, formato):
    """Exporta dados direto para o navegador nos formatos CSV, XLS e JSON."""
    if modelo == "projetos":
        resource = ProjetosResource()
    elif modelo == "organizacoes":
        resource = OrganizacoesResource()
    elif modelo == "opcoes":
        resource = OpcoesResource()
    elif modelo == "usuarios":
        resource = UsuariosResource()
    elif modelo == "alunos":
        resource = AlunosResource()
    elif modelo == "professores":
        resource = ProfessoresResource()
    elif modelo == "configuracao":
        resource = ConfiguracaoResource()
    else:
        #return HttpResponse("Chamada irregular : Base de dados desconhecida = "+modelo)
        mensagem = "Chamada irregular : Base de dados desconhecida = " + modelo
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    dataset = resource.export()
    if(formato == "xls" or formato == "xlsx"):
        response = HttpResponse(dataset.xlsx, content_type='application/ms-excel')
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(dataset.json, content_type='application/json')
    elif formato == "csv":
        response = HttpResponse(dataset.csv, content_type='text/csv')
    else:
        #return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)
        mensagem = "Chamada irregular : Formato desconhecido = " + formato
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    response['Content-Disposition'] = 'attachment; filename="'+modelo+'.'+formato+'"'
    return response

def create_backup():
    """Rotina para criar um backup."""
    databook = Databook()

    data_projetos = ProjetosResource().export()
    data_projetos.title = "Projetos"
    databook.add_sheet(data_projetos)

    data_organizacoes = OrganizacoesResource().export()
    data_organizacoes.title = "Organizacoes"
    databook.add_sheet(data_organizacoes)

    data_opcoes = OpcoesResource().export()
    data_opcoes.title = "Opcoes"
    databook.add_sheet(data_opcoes)

    data_usuarios = UsuariosResource().export()
    data_usuarios.title = "Usuarios"
    databook.add_sheet(data_usuarios)

    data_alunos = AlunosResource().export()
    data_alunos.title = "Alunos"
    databook.add_sheet(data_alunos)

    data_professores = ProfessoresResource().export()
    data_professores.title = "Professores"
    databook.add_sheet(data_professores)

    data_configuracao = ConfiguracaoResource().export()
    data_configuracao.title = "Configuracao"
    databook.add_sheet(data_configuracao)

    return databook

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def backup(request, formato):
    """Gera um backup de tudo."""
    databook = create_backup()
    if formato == "xls" or formato == "xlsx":
        response = HttpResponse(databook.xlsx, content_type='application/ms-excel')
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(databook.json, content_type='application/json')
    else:
        #return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)
        mensagem = "Chamada irregular : Formato desconhecido = " + formato
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    response['Content-Disposition'] = 'attachment; filename="backup.'+formato+'"'
    return response

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def email_backup(request):
    """Envia um e-mail com os backups."""
    subject = 'BACKUP PFE'
    message = "Backup PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com', 'lpsoares@gmail.com',]
    mail = EmailMessage(subject, message, email_from, recipient_list)
    databook = create_backup()
    mail.attach("backup.xlsx", databook.xlsx, 'application/ms-excel')
    mail.attach("backup.json", databook.json, 'application/json')
    mail.send()
    #return HttpResponse("E-mail enviado.")
    mensagem = "E-mail enviado."
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, 'generic.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def servico(request):
    """Caso servidor esteja em manutenção."""
    configuracao = Configuracao.objects.all().first()
    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        if 'manutencao' in check_values:
            configuracao.manutencao = True
        else:
            configuracao.manutencao = False
        configuracao.save()
        return redirect('/projetos/administracao/')
    else:
        context = {'manutencao': configuracao.manutencao,}
        return render(request, 'projetos/servico.html', context)

def render_to_pdf(template_src, context_dict=None):
    """Renderiza um documento em PDF."""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return result
        #return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def get_calendario_context():
    """Contexto para gerar calendário."""
    eventos = Evento.objects.exclude(tipo_de_evento=12).\
                             exclude(tipo_de_evento=40).\
                             exclude(tipo_de_evento=41).\
                             exclude(tipo_de_evento=20).\
                             exclude(tipo_de_evento=30).\
                             exclude(tipo_de_evento__gte=100)
    #aulas = Evento.objects.filter(name="Aula PFE")
    aulas = Evento.objects.filter(tipo_de_evento=12) #12, 'Aula PFE'
    #laboratorios = Evento.objects.filter(name="Laboratório")
    laboratorios = Evento.objects.filter(tipo_de_evento=40) #40, 'Laboratório'
    #provas = Evento.objects.filter(name="Semana de Provas")
    provas = Evento.objects.filter(tipo_de_evento=41) #41, 'Semana de Provas'
    #quinzenais = Evento.objects.filter(name="Relato Quinzenal")
    quinzenais = Evento.objects.filter(tipo_de_evento=20) #20, 'Relato Quinzenal'
    #feedbacks = Evento.objects.filter(name="Feedback dos Alunos sobre PFE")
    feedbacks = Evento.objects.filter(tipo_de_evento=30) #30, 'Feedback dos Alunos sobre PFE'

    coordenacao = Evento.objects.filter(tipo_de_evento__gte=100) # Eventos da coordenação

    # ISSO NAO ESTA BOM, FAZER ALGO MELHOR

    # TAMBÉM ESTOU USANDO NO CELERY PARA AVISAR DOS EVENTOS

    context = {
        'eventos': eventos,
        'aulas': aulas,
        'laboratorios': laboratorios,
        'provas' : provas,
        'quinzenais' : quinzenais,
        'feedbacks' : feedbacks,
        'coordenacao' : coordenacao,
        'semestre' : Configuracao.objects.all().first().semestre,
    }
    return context

@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context()
    return render(request, 'projetos/calendario.html', context)

@login_required
def calendario_limpo(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context()
    context['limpo'] = True
    return render(request, 'projetos/calendario.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio(request, modelo, formato):
    """Gera relatorios em html e PDF."""
    configuracao = Configuracao.objects.all().first()

    if modelo == "projetos":
        context = {
            'projetos': Projeto.objects.all(),
            'configuracao': configuracao,
        }
        arquivo = "projetos/relatorio_projetos.html"

    elif modelo == "alunos":
        context = {
            'alunos': Aluno.objects.all().filter(user__tipo_de_usuario=1).\
                                          filter(anoPFE=configuracao.ano).\
                                          filter(semestrePFE=configuracao.semestre),
            'configuracao': configuracao,
        }
        arquivo = "projetos/relatorio_alunos.html"

    elif modelo == "feedbacks":
        context = {
            'feedbacks': Feedback.objects.all(),
            'configuracao': configuracao,
        }
        arquivo = "projetos/relatorio_feedbacks.html"

    elif modelo == "calendario":  # Nao funcionando (processamento falha)
        context = get_calendario_context()
        arquivo = "projetos/calendario.html"

    else:
        #return HttpResponse("Chamada irregular : Base de dados desconhecida = "+modelo)
        mensagem = "Chamada irregular : Base de dados desconhecida = " + modelo
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    if(formato == "html" or formato == "HTML"):
        return render(request, arquivo, context)
    if(formato == "pdf" or formato == "PDF"):
        pdf = render_to_pdf(arquivo, context)
        return HttpResponse(pdf.getvalue(), content_type='application/pdf')


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio_backup(request):
    """Gera um relatório de backup de segurança."""
    subject = 'RELATÓRIOS PFE'
    message = "Relatórios PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com', 'lpsoares@gmail.com',]
    mail = EmailMessage(subject, message, email_from, recipient_list)
    configuracao = Configuracao.objects.all().first()
    context = {
        'projetos': Projeto.objects.all(),
        'alunos': Aluno.objects.all().filter(user__tipo_de_usuario=1).\
                                      filter(anoPFE=configuracao.ano).\
                                      filter(semestrePFE=configuracao.semestre),
        'configuracao': configuracao,
    }
    pdf_proj = render_to_pdf('projetos/relatorio_projetos.html', context)
    pdf_alun = render_to_pdf('projetos/relatorio_alunos.html', context)
    mail.attach("projetos.pdf", pdf_proj.getvalue(), 'application/pdf')
    mail.attach("alunos.pdf", pdf_alun.getvalue(), 'application/pdf')
    mail.send()
    #return HttpResponse("E-mail enviado.")
    mensagem = "E-mail enviado."
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, 'generic.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_fechados(request, periodo="todos"):
    """Lista todos os projetos fechados."""
    #configuracao = Configuracao.objects.all().first()
    projetos = []
    alunos_list = []
    prioridade_list = []
    nalunos = 0
    qtd_prioridades = [0, 0, 0, 0, 0, 0]   # para grafico de pizza no final

    for projeto in Projeto.objects.all():
        alunos_pfe = Aluno.objects.filter(alocacao__projeto=projeto)
        if alunos_pfe: #len(alunos_pfe) > 0:
            projetos.append(projeto)
            alunos_list.append(alunos_pfe)
            nalunos += len(alunos_pfe)
            #alunos = []
            prioridades = []
            for aluno in alunos_pfe:
                opcoes = Opcao.objects.filter(projeto=projeto)
                opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
                opcoes1 = opcoes_alunos.filter(aluno__alocacao__projeto=projeto)
                opcoes2 = opcoes1.filter(aluno=aluno)
                if len(opcoes2) == 1:
                    prioridade = opcoes2.first().prioridade
                    prioridades.append(prioridade)
                    qtd_prioridades[prioridade-1] += 1
                else:
                    prioridades.append(0)
            prioridade_list.append(zip(alunos_pfe, prioridades))
    mylist = zip(projetos, prioridade_list)
    context = {
        'mylist': mylist,
        'length': len(projetos),
        'nalunos': nalunos,
        'qtd_prioridades': qtd_prioridades,
        'periodo': periodo,
    }
    return render(request, 'projetos/projetos_fechados.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def tabela_documentos(request):
    """Exibe tabela com todos os documentos armazenados."""
    configuracao = Configuracao.objects.all().first()
    projetos = Projeto.objects.filter(alocacao__isnull=False).distinct().order_by("ano", "semestre")
    documentos = []
    for projeto in projetos:

        contrato = {}

        # Contratos   -   (0, 'contrato com empresa')
        contratos = []
        for doc in Documento.objects.filter(organizacao=projeto.organizacao).\
                                     filter(tipo_de_documento=0):
            contratos.append((doc.documento, doc.anotacao, doc.data))
        contrato["contratos"] = contratos

        # Contrato alunos  -  (1, 'contrato entre empresa e aluno')
        contratos_alunos = []
        alunos = Aluno.objects.filter(alocacao__projeto=projeto)
        for aluno in alunos:
            documento = Documento.objects.filter(usuario=aluno.user).\
                                          filter(tipo_de_documento=1).last()
            if documento:
                contratos_alunos.append((documento.documento,
                                         aluno.user.first_name+" "+aluno.user.last_name))
            else:
                contratos_alunos.append(("", aluno.user.first_name+" "+aluno.user.last_name))
        contrato["contratos_alunos"] = contratos_alunos

        # relatorio_final   -   (3, 'relatório final')
        documento = Documento.objects.filter(projeto=projeto).filter(tipo_de_documento=3).last()
        if documento:
            contrato["relatorio_final"] = documento.documento
        else:
            contrato["relatorio_final"] = ""

        # Autorização de Publicação da Empresa  -   (4, 'autorização de publicação empresa')
        documento = Documento.objects.filter(projeto=projeto).filter(tipo_de_documento=4).last()
        if documento:
            contrato["autorizacao_publicacao_empresa"] = documento.documento
        else:
            contrato["autorizacao_publicacao_empresa"] = ""

        documentos.append(contrato)

        # Autorização de Publicação do Aluno  -   (5, 'autorização de publicação aluno')
        autorizacao_publicacao_aluno = []
        alunos = Aluno.objects.filter(alocacao__projeto=projeto)
        for aluno in alunos:
            documento = Documento.objects.filter(usuario=aluno.user).\
                                          filter(tipo_de_documento=5).last()
            if documento:
                autorizacao_publicacao_aluno.\
                    append((documento.documento, aluno.user.first_name+" "+aluno.user.last_name))
            else:
                autorizacao_publicacao_aluno.\
                    append(("", aluno.user.first_name+" "+aluno.user.last_name))
        contrato["autorizacao_publicacao_aluno"] = autorizacao_publicacao_aluno

        # Outros   -   (14, 'outros')
        outros = []
        for doc in Documento.objects.filter(organizacao=projeto.organizacao).\
                                     filter(tipo_de_documento=14):
            outros.append((doc.documento, doc.anotacao, doc.data))
        contrato["outros"] = outros
    mylist = zip(projetos, documentos)

    # Outros documentos
    seguros = Documento.objects.filter(tipo_de_documento=15)

    context = {
        'configuracao': configuracao,
        'mylist': mylist,
        'seguros': seguros,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/tabela_documentos.html', context)

@login_required
def submissao(request):
    """Para perguntas descritivas ao aluno de onde trabalho, entidades, sociais e familia."""
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 1:
        mensagem = "Você não está cadastrado como aluno!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    configuracao = Configuracao.objects.first()
    aluno = Aluno.objects.get(pk=request.user.pk)
    if request.method == 'POST':
        if timezone.now() > configuracao.prazo:
            mensagem = "Prazo para o preenchimento do formulário vencido!"
            context = {
                "area_principal": True,
                "area_aluno": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        aluno.trabalhou = request.POST.get("trabalhou", "")
        aluno.social = request.POST.get("social", "")
        aluno.entidade = request.POST.get("entidade", "")
        aluno.familia = request.POST.get("familia", "")

        aluno.save()
        return render(request, 'users/atualizado.html',)
    else:
        context = {
            'trabalhou' : aluno.trabalhou,
            'social' : aluno.social,
            'entidade' : aluno.entidade,
            'familia' : aluno.familia,
            'entidades' : Entidade.objects.all(),
        }
        return render(request, 'projetos/submissao.html', context)


def cria_areas(request):
    """Cria um objeto Areas e preenche ele."""
    check_values = request.POST.getlist('selection')

    areas = Areas.create()

    areas.inovacao_social = "inovacao_social" in check_values
    areas.ciencia_dos_dados = "ciencia_dos_dados" in check_values
    areas.modelagem_3D = "modelagem_3D" in check_values
    areas.manufatura = "manufatura" in check_values
    areas.resistencia_dos_materiais = "resistencia_dos_materiais" in check_values
    areas.modelagem_de_sistemas = "modelagem_de_sistemas" in check_values
    areas.controle_e_automacao = "controle_e_automacao" in check_values
    areas.termodinamica = "termodinamica" in check_values
    areas.fluidodinamica = "fluidodinamica" in check_values
    areas.eletronica_digital = "eletronica_digital" in check_values
    areas.programacao = "programacao" in check_values
    areas.inteligencia_artificial = "inteligencia_artificial" in check_values
    areas.banco_de_dados = "banco_de_dados" in check_values
    areas.computacao_em_nuvem = "computacao_em_nuvem" in check_values
    areas.visao_computacional = "visao_computacional" in check_values
    areas.computacao_de_alto_desempenho = "computacao_de_alto_desempenho" in check_values
    areas.robotica = "robotica" in check_values
    areas.realidade_virtual_aumentada = "realidade_virtual_aumentada" in check_values
    areas.protocolos_de_comunicacao = "protocolos_de_comunicacao" in check_values
    areas.eficiencia_energetica = "eficiencia_energetica" in check_values
    areas.administracao_economia_financas = "administracao_economia_financas" in check_values

    areas.outras = request.POST.get("outras", "")

    areas.save()

    return areas

def lista_areas(areas):
    """Lista áreas de um objeto Areas."""

    mensagem = ""

    if areas.inovacao_social:
        mensagem += "&bull; Inovacao Social<br>\n"
    if areas.ciencia_dos_dados:
        mensagem += "&bull; Ciência dos Dados<br>\n"
    if areas.modelagem_3D:
        mensagem += "&bull; Modelagem 3D<br>\n"
    if areas.manufatura:
        mensagem += "&bull; Manufatura<br>\n"
    if areas.resistencia_dos_materiais:
        mensagem += "&bull; Resistência dos Materiais<br>\n"
    if areas.modelagem_de_sistemas:
        mensagem += "&bull; Modelagem de Sistemas<br>\n"
    if areas.controle_e_automacao:
        mensagem += "&bull; Controle e Automação<br>\n"
    if areas.termodinamica:
        mensagem += "&bull; Termodinâmica<br>\n"
    if areas.fluidodinamica:
        mensagem += "&bull; Fluidodinâmica<br>\n"
    if areas.eletronica_digital:
        mensagem += "&bull; Eletrônica Digital<br>\n"
    if areas.programacao:
        mensagem += "&bull; Programacao<br>\n"
    if areas.inteligencia_artificial:
        mensagem += "&bull; Inteligência Artificial<br>\n"
    if areas.banco_de_dados:
        mensagem += "&bull; Banco de Dados<br>\n"
    if areas.computacao_em_nuvem:
        mensagem += "&bull; Computação em Nuvem<br>\n"
    if areas.visao_computacional:
        mensagem += "&bull; Visão Computacional<br>\n"
    if areas.computacao_de_alto_desempenho:
        mensagem += "&bull; Computação de Alto Desempenho<br>\n"
    if areas.robotica:
        mensagem += "&bull; Robótica<br>\n"
    if areas.realidade_virtual_aumentada:
        mensagem += "&bull; Realidade Virtual e Aumentada<br>\n"
    if areas.protocolos_de_comunicacao:
        mensagem += "&bull; Protocolos de Comunicação<br>\n"
    if areas.eficiencia_energetica:
        mensagem += "&bull; Eficiência Energética<br>\n"
    if areas.administracao_economia_financas:
        mensagem += "&bull; Administração, Economia e Finanças<br>\n"

    if areas.outras and areas.outras != "":
        mensagem += "Outras: " + areas.outras + "<br>\n"

    return mensagem

def preenche_proposta(request, proposta):
    """Preenche um proposta a partir de um request."""
    if proposta is None: # proposta nova
        proposta = Proposta.create()

        configuracao = Configuracao.objects.all().first()
        ano = configuracao.ano
        semestre = configuracao.semestre

        # Vai para próximo semestre
        if semestre == 1:
            semestre = 2
        else:
            ano += 1
            semestre = 1

        proposta.ano = ano
        proposta.semestre = semestre

    proposta.nome = request.POST.get("nome", "")
    proposta.email = request.POST.get("email", "")
    proposta.website = request.POST.get("website", "")
    proposta.nome_organizacao = request.POST.get("organizacao", "")
    proposta.endereco = request.POST.get("endereco", "")
    proposta.contatos_tecnicos = request.POST.get("contatos_tecnicos", "")
    proposta.contatos_administrativos = request.POST.get("contatos_adm", "")
    proposta.descricao_organizacao = request.POST.get("descricao_organizacao", "")
    proposta.departamento = request.POST.get("info_departamento", "")
    proposta.titulo = request.POST.get("titulo", "")

    proposta.descricao = request.POST.get("desc_projeto", "")
    proposta.expectativas = request.POST.get("expectativas", "")
    proposta.recursos = request.POST.get("recursos", "")
    proposta.observacoes = request.POST.get("observacoes", "")

    proposta.areas_de_interesse = cria_areas(request)

    proposta.save()

    return proposta

def envia_proposta(proposta):
    """Envia Proposta por email."""

    #Isso tinha que ser feito por template, arrumar qualquer hora.
    message = "<h3>Proposta de Projeto para o PFE {0}.{1}</h3>\n<br>\n".\
                   format(proposta.ano, proposta.semestre)

    message += "Para editar essa proposta acesse:</b><br>\n <a href='{0}'>{0}</a><br>\n<br>\n".\
        format(settings.SERVER+proposta.get_absolute_url())

    message += "<b>Título da Proposta de Projeto:</b> {0}<br>\n<br>\n".format(proposta.titulo)
    message += "<b>Proposta submetida por:</b> {0} <br>\n".format(proposta.nome)
    message += "<b>e-mail:</b> "
    for each in list(map(str.strip, re.split(",|;", proposta.email))):
        message += "&lt;{0}&gt; ".format(each)
    message += "<br>\n<br>\n"

    message += "<b>Nome da Organização:</b> {0}<br>\n".\
        format(proposta.nome_organizacao.replace('\n', '<br>\n'))
    message += "<b>Website:</b> {0}<br>\n".format(proposta.website)
    message += "<b>Endereco:</b> {0}<br>\n".format(proposta.endereco.replace('\n', '<br>\n'))

    message += "<br>\n<br>\n"

    message += "<b>Contatos Técnicos:</b><br>\n {0}<br>\n<br>\n".\
                   format(proposta.contatos_tecnicos.replace('\n', '<br>\n'))

    message += "<b>Contatos Administrativos:</b><br>\n {0}<br>\n<br>\n".\
                   format(proposta.contatos_administrativos.replace('\n', '<br>\n'))

    message += "<b>Informações sobre a instituição/empresa:</b><br>\n {0}<br>\n<br>\n".\
                   format(proposta.descricao_organizacao.replace('\n', '<br>\n'))

    message += "<b>Informações sobre a departamento:</b><br>\n {0}<br>\n<br>\n".\
                   format(proposta.departamento.replace('\n', '<br>\n'))

    message += "<br>\n<br>\n"

    message += "<b>Descrição do Projeto:</b><br>\n {0}<br><br>\n".format(proposta.descricao)
    message += "<b>Expectativas de resultados/entregas:</b><br>\n {0}<br>\n<br>\n".\
                   format(proposta.expectativas.replace('\n', '<br>\n'))

    message += "<br>\n"

    message += "<b>Áreas/Habilidades envolvidas no projeto:</b><br>\n"
    message += lista_areas(proposta.areas_de_interesse)

    message += "<br>\n"
    message += "<b>Recursos a serem disponibilizados aos alunos:</b><br>\n {0}<br><br>\n".\
                   format(proposta.recursos.replace('\n', '<br>\n'))
    message += "<b>Outras observações para os alunos:</b><br>\n {0}<br><br>\n".\
                   format(proposta.observacoes.replace('\n', '<br>\n'))

    message += "<br>\n<br>\n"
    message += "<b>Data da proposta:</b> {0}<br>\n<br>\n<br>\n".\
                   format(proposta.data.strftime("%d/%m/%Y %H:%M"))

    message += "<br>\n<br>\n"
    message += """
    <b>Obs.:</b> Ao submeter o projeto, deve ficar claro que a intenção do Projeto Final de Engenharia é 
    que os alunos tenham um contato próximo com as pessoas responsáveis nas instituições parceiras 
    para o desenvolvimento de uma solução em engenharia. Em geral os alunos se deslocam uma vez 
    por semana para entender melhor o desafio, demonstrar resultados preliminares, fazerem 
    planejamentos em conjunto, dentre de outros pontos que podem variar de projeto para projeto. 
    Também deve ficar claro que embora não exista um custo direto para as instituições parceiras, 
    essas terão de levar em conta que pelo menos um profissional deverá dedicar algumas horas 
    semanalmente para acompanhar os alunos. Além disso se a proposta contemplar gastos, como por 
    exemplo servidores, matéria prima de alguma forma, o Insper não terá condição de bancar tais 
    gastos e isso terá de ficar a cargo da empresa, contudo os alunos terão acesso aos 
    laboratórios do Insper para o desenvolvimento do projeto em horários agendados.<b>\n"""

    subject = 'Proposta PFE : ({0}.{1} - {2}'.format(proposta.ano,
                                                     proposta.semestre,
                                                     proposta.titulo)

    recipient_list = list(map(str.strip, re.split(",|;", proposta.email)))
    recipient_list += ["pfe@insper.edu.br", "lpsoares@insper.edu.br",]
    #recipient_list += ["lpsoares@insper.edu.br",]
    check = email(subject, recipient_list, message)
    if check != 1:
        message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

    return message


#@login_required
def proposta_submissao(request):
    """Formulário de Submissão de Proposta de Projetos."""
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario == 1: # alunos
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    parceiro = None
    professor = None
    administrador = None
    organizacao = ""
    website = "http://"
    endereco = ""
    descricao_organizacao = ""
    if user.tipo_de_usuario == 3: # parceiro
        parceiro = Parceiro.objects.get(pk=request.user.pk)
        organizacao = parceiro.organizacao
        website = parceiro.organizacao.website
        endereco = parceiro.organizacao.endereco
        descricao_organizacao = parceiro.organizacao.informacoes
    elif user.tipo_de_usuario == 2: # professor
        professor = Professor.objects.get(pk=request.user.pk)
    elif user.tipo_de_usuario == 4: # admin
        administrador = Administrador.objects.get(pk=request.user.pk)

    if request.method == 'POST':
        proposta = preenche_proposta(request, None)
        mensagem = envia_proposta(proposta) # Por e-mail

        resposta = "Submissão de proposta de projeto realizada com sucesso.<br>"
        resposta += "Você deve receber um e-mail de confirmação nos próximos instantes.<br>"
        resposta += mensagem
        context = {
            "voltar": True,
            "mensagem": resposta,
        }
        return render(request, 'generic.html', context=context)

    context = {
        'full_name' : user.get_full_name(),
        'email' : user.email,
        'organizacao' : organizacao,
        'website' : website,
        'endereco' : endereco,
        'descricao_organizacao' : descricao_organizacao,
        'parceiro' : parceiro,
        'professor' : professor,
        'administrador' : administrador,
        'contatos_tecnicos' : "",
        'contatos_adm' : "",
        'info_departamento' : "",
        'titulo' : "",
        'desc_projeto' : "",
        'expectativas' : "",
        'areas' : None,
        'recursos' : "",
        'observacoes' : "",
        'edicao' : False,
    }

    return render(request, 'projetos/proposta_submissao.html', context)

#@login_required
def proposta_editar(request, slug):
    """Formulário de Edição de Propostas de Projeto por slug."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        user = None

    parceiro = None
    professor = None
    administrador = None

    if user:
        if user.tipo_de_usuario == 1: # alunos
            mensagem = "Você não está cadastrado como parceiro de uma organização!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        if user.tipo_de_usuario == 3: # parceiro
            parceiro = Parceiro.objects.get(pk=request.user.pk)
        elif user.tipo_de_usuario == 2: # professor
            professor = Professor.objects.get(pk=request.user.pk)
        elif user.tipo_de_usuario == 4: # admin
            administrador = Administrador.objects.get(pk=request.user.pk)

    try:
        proposta = Proposta.objects.get(slug=slug)
    except Proposta.DoesNotExist:
        return HttpResponseNotFound('<h1>Proposta não encontrada!</h1>')

    if request.method == 'POST':
        preenche_proposta(request, proposta)
        mensagem = envia_proposta(proposta) # Por e-mail
        resposta = "Submissão de proposta de projeto atualizada com sucesso.<br>"
        resposta += "Você deve receber um e-mail de confirmação nos próximos instantes.<br>"
        resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"
        resposta += "<br><br><br><hr>"
        resposta += mensagem
        context = {
            "mensagem": resposta,
        }
        return render(request, 'generic.html', context=context)

    context = {
        'full_name' : proposta.nome,
        'email' : proposta.email,
        'organizacao' : proposta.nome_organizacao,
        'website' : proposta.website,
        'endereco' : proposta.endereco,
        'descricao_organizacao' : proposta.descricao_organizacao,
        'parceiro' : parceiro,
        'professor' : professor,
        'administrador' : administrador,
        'contatos_tecnicos' : proposta.contatos_tecnicos,
        'contatos_adm' : proposta.contatos_administrativos,
        'info_departamento' : proposta.departamento,
        'titulo' : proposta.titulo,
        'desc_projeto' : proposta.descricao,
        'expectativas' : proposta.expectativas,
        'areas' : proposta.areas_de_interesse,
        'recursos' : proposta.recursos,
        'observacoes' : proposta.observacoes,
        'edicao' : True,

    }
    return render(request, 'projetos/proposta_submissao.html', context)


@login_required
def index_documentos(request):
    """Lista os documentos armazenados no servidor."""
    regulamento = Documento.objects.filter(tipo_de_documento=6).last() # Regulamento PFE
    plano_de_aprendizagem = Documento.objects.filter(tipo_de_documento=7).last() # Plano de Aprend
    manual_aluno = Documento.objects.filter(tipo_de_documento=8).last() # manual do aluno
    # = Documento.objects.filter(tipo_de_documento=9).last() # manual do orientador
    # = Documento.objects.filter(tipo_de_documento=10).last() # manual da organização parceira
    manual_planejamento = Documento.objects.filter(tipo_de_documento=13).last() # manual de planej
    manual_relatorio = Documento.objects.filter(tipo_de_documento=12).last() # manual de relatórios
    termo_parceria = Documento.objects.filter(tipo_de_documento=14).last() # termo de parceria
    context = {
        'MEDIA_URL' : settings.MEDIA_URL,
        'regulamento': regulamento,
        'plano_de_aprendizagem': plano_de_aprendizagem,
        'manual_aluno': manual_aluno,
        'manual_planejamento' : manual_planejamento,
        'manual_relatorio': manual_relatorio,
        'termo_parceria': termo_parceria,
    }
    return render(request, 'index_documentos.html', context)


####### PARTE DE I/O  #########

# Faz o upload de arquivos
def simple_upload(myfile, path="", prefix=""):
    """Faz uploads para o servidor."""
    file_system_storage = FileSystemStorage()
    filename = file_system_storage.save(path+prefix+text.get_valid_filename(myfile.name), myfile)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def carrega(request, dado):
    """Faz o upload de arquivos CSV para o servidor."""

    if dado == "disciplinas":
        resource = DisciplinasResource()
    if dado == "alunos":
        resource = AlunosResource()
    else:
        raise Http404

    # https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
    if request.method == 'POST':

        dataset = tablib.Dataset()

        new_data = request.FILES['arquivo'].readlines()
        entradas = ""
        for i in new_data:
            texto = i.decode("utf-8")
            entradas += re.sub('[^A-Za-z0-9À-ÿ, \r\n@._]+', '', texto) #Limpa caracteres especiais

        #imported_data = dataset.load(entradas, format='csv')
        dataset.load(entradas, format='csv')
        dataset.insert_col(0, col=lambda row: None, header="id")

        result = resource.import_data(dataset, dry_run=True, raise_errors=True)

        if not result.has_errors():
            resource.import_data(dataset, dry_run=False)  # Actually import now
            string_html = "Importado ({0} registros): <br>".format(len(dataset))
            for row_values in dataset:
                string_html += str(row_values) + "<br>"
            context = {
                "area_principal": True,
                "mensagem": string_html,
            }
            return render(request, 'generic.html', context=context)
        else:
            mensagem = "Erro ao carregar arquivo." + str(result)
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

    context = {
        'campos_permitidos': resource.campos,
    }
    return render(request, 'projetos/import.html', context)

def get_response(file, path):
    """Verifica a extensão do arquivo e retorna o HttpRensponse corespondente."""
    #image/gif, image/tiff, application/zip, audio/mpeg, audio/ogg, text/csv, text/plain
    if path[-3:].lower() == "jpg" or path[-4:].lower() == "jpeg":
        return HttpResponse(file.read(), content_type="image/jpeg")
    elif path[-3:].lower() == "png":
        return HttpResponse(file.read(), content_type="image/png")
    elif path[-3:].lower() == "doc" or path[-4:].lower() == "docx":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    elif path[-3:].lower() == "pdf":
        return HttpResponse(file.read(), content_type="application/pdf")
    else:
        return None

@login_required
#@permission_required('users.altera_professor', login_url='/projetos/')
def arquivos(request, documentos, path):
    """Permite acessar arquivos do servidor."""
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}".format(documentos, path))
    file_path = os.path.abspath(local_path)
    if ".." in file_path:
        raise PermissionDenied
    if "\\" in file_path:
        raise PermissionDenied
    if os.path.exists(file_path):
        doc = Documento.objects.filter(documento=local_path[len(settings.BASE_DIR)+\
                                                            len(settings.MEDIA_URL):]).last()
        if doc:
            if (doc.tipo_de_documento < 6) and (PFEUser.objects.get(pk=request.user.pk).\
                                                                tipo_de_usuario != 2):
                #return HttpResponse("Documento Confidencial")
                mensagem = "Documento Confidencial"
                context = {
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)
        with open(file_path, 'rb') as file:
            response = get_response(file, path)
            if not response:
                #return HttpResponse("Erro ao carregar arquivo (formato não suportado).")
                mensagem = "Erro ao carregar arquivo (formato não suportado)."
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

@login_required
#@permission_required('users.altera_professor', login_url='/projetos/')
def arquivos2(request, organizacao, usuario, path):
    """Permite acessar arquivos do servidor."""
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}".format(organizacao, usuario, path))
    file_path = os.path.abspath(local_path)
    if ".." in file_path:
        raise PermissionDenied
    if "\\" in file_path:
        raise PermissionDenied
    if os.path.exists(file_path):
        doc = Documento.objects.filter(\
            documento=local_path[len(settings.BASE_DIR)+len(settings.MEDIA_URL):]).last()
        if doc:
            if (doc.tipo_de_documento < 6) and\
               (PFEUser.objects.get(pk=request.user.pk).tipo_de_usuario != 2):
                #return HttpResponse("Documento Confidencial")
                mensagem = "Documento Confidencial!"
                context = {
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)
        with open(file_path, 'rb') as file:
            response = get_response(file, path)
            if not response:
                #return HttpResponse("Erro ao carregar arquivo (formato não suportado).")
                mensagem = "Erro ao carregar arquivo (formato não suportado)."
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

####### FIM DA PARTE DE I/O  #########

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_lista(request, periodo):
    """Lista todos os projetos."""
    configuracao = Configuracao.objects.all().first()
    projetos = Projeto.objects.filter(alocacao__isnull=False).distinct() # no futuro remover
    projetos = projetos.order_by("ano", "semestre", "organizacao", "titulo",)
    if periodo == "todos":
        pass
    if periodo == "antigos":
        if configuracao.semestre == 1:
            projetos = projetos.filter(ano__lt=configuracao.ano)
        else:
            projetos = projetos.filter(ano__lte=configuracao.ano).\
                                       exclude(ano=configuracao.ano, semestre=2)
    elif periodo == "atuais":
        projetos = projetos.filter(ano=configuracao.ano, semestre=configuracao.semestre)
    elif periodo == "próximos":
        if configuracao.semestre == 1:
            projetos = projetos.filter(ano__gte=configuracao.ano).\
                                exclude(ano=configuracao.ano, semestre=1)
        else:
            projetos = projetos.filter(ano__gt=configuracao.ano)

    context = {
        'projetos': projetos,
        'periodo' : periodo,
        'configuracao' : configuracao,
    }
    return render(request, 'projetos/projetos_lista.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def propostas_lista(request, periodo):
    """Lista todas as propostas de projetos."""
    configuracao = Configuracao.objects.all().first()
    propostas = Proposta.objects.all().order_by("ano", "semestre", "organizacao", "titulo",)
    if periodo == "todos":
        pass
    if periodo == "antigos":
        if configuracao.semestre == 1:
            propostas = propostas.filter(ano__lt=configuracao.ano)
        else:
            propostas = propostas.filter(ano__lte=configuracao.ano).\
                                       exclude(ano=configuracao.ano, semestre=2)
    elif periodo == "atuais":
        propostas = propostas.filter(ano=configuracao.ano, semestre=configuracao.semestre)
    elif periodo == "disponiveis":
        if configuracao.semestre == 1:
            propostas = propostas.filter(ano__gte=configuracao.ano).\
                                exclude(ano=configuracao.ano, semestre=1)
        else:
            propostas = propostas.filter(ano__gt=configuracao.ano)

    context = {
        'propostas': propostas,
        'periodo' : periodo,
        'configuracao' : configuracao,
    }
    return render(request, 'projetos/propostas_lista.html', context)

@login_required
@permission_required('users.altera_parceiro', login_url='/projetos/')
def parceiro_propostas(request):
    """Lista todas as propostas de projetos."""
    #configuracao = Configuracao.objects.all().first()

    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        #return HttpResponse("Você não está cadastrado como parceiro")
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    propostas = Proposta.objects.filter(organizacao=user.parceiro.organizacao).\
                        order_by("ano", "semestre", "titulo",)
    context = {
        'propostas': propostas,
        #'configuracao' : configuracao,
    }
    return render(request, 'projetos/parceiro_propostas.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def exportar(request):
    """Exporta dados."""
    return render(request, 'projetos/exportar.html')

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def relatorios(request):
    """Página para recuperar alguns relatórios."""
    return render(request, 'projetos/relatorios.html')

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def carregar(request):
    """Para carregar dados para o servidor."""
    return render(request, 'projetos/carregar.html')

@login_required
def meuprojeto(request):
    """Mostra o projeto do próprio aluno, se for aluno."""
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 1 and user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        #return HttpResponse("Você não está cadastrado como aluno ou professor")
        mensagem = "Você não está cadastrado como aluno ou professor!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    if user.tipo_de_usuario == 2:
        professor = Professor.objects.get(user__pk=request.user.pk)
        return redirect('professor_detail', primarykey=professor.pk)
    # vvvv Caso seja um aluno  vvv
    aluno = Aluno.objects.get(pk=request.user.pk)
    context = {
        'aluno': aluno,
        'configuracao' : Configuracao.objects.all().first(),
    }
    return render(request, 'projetos/meuprojeto_aluno.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def organizacoes_tabela(request):
    """Alocação das Organizações por semestre."""
    configuracao = Configuracao.objects.all().first()

    organizacoes_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        organizacoes = []
        grupos = []
        #for professor in Professor.objects.all().order_by("user__first_name", "user__last_name"):
        for organizacao in Organizacao.objects.all():
            #count_projetos = 0
            count_projetos = []
            grupos_pfe = Projeto.objects.filter(organizacao=organizacao).\
                                         filter(ano=ano).\
                                         filter(semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe: #len(alunos_pfe) > 0
                        #count_projetos += 1
                        count_projetos.append(grupo)
                #if count_projetos > 0:
                if count_projetos:
                    organizacoes.append(organizacao)
                    grupos.append(count_projetos)
        organizacoes_pfe.append(zip(organizacoes, grupos))
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    anos = zip(organizacoes_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro
    context = {
        'anos': anos,
    }
    return render(request, 'projetos/organizacoes_tabela.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def professores_tabela(request):
    """Alocação dos Orientadores por semestre."""
    configuracao = Configuracao.objects.all().first()

    professores_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                          Lower("user__last_name")):
            #count_grupos = 0
            count_grupos = []
            grupos_pfe = Projeto.objects.filter(orientador=professor).\
                                        filter(ano=ano).\
                                        filter(semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        #count_grupos += 1
                        count_grupos.append(grupo)
                #if count_grupos > 0:
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)
        professores_pfe.append(zip(professores, grupos))
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    anos = zip(professores_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro
    context = {
        'anos': anos,
    }
    return render(request, 'projetos/professores_tabela.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def coorientadores_tabela(request):
    """Alocação dos Coorientadores por semestre."""
    configuracao = Configuracao.objects.all().first()

    professores_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by(Lower("user__first_name"),
                                                          Lower("user__last_name")):
            count_grupos = []
            grupos_pfe = Projeto.objects.filter(coorientador__usuario__professor=professor).\
                                        filter(ano=ano).\
                                        filter(semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:
                        count_grupos.append(grupo)
                if count_grupos:
                    professores.append(professor)
                    grupos.append(count_grupos)
        professores_pfe.append(zip(professores, grupos))
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    anos = zip(professores_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro
    context = {
        'anos': anos,
    }
    return render(request, 'projetos/coorientadores_tabela.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_tabela(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    configuracao = Configuracao.objects.all().first()

    membros_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        membros = dict()
        bancas = Banca.objects.all().filter(projeto__ano=ano).filter(projeto__semestre=semestre)
        for banca in bancas:
            if banca.projeto.orientador:
                membros.setdefault(banca.projeto.orientador.user, []).append(banca)
            if banca.membro1:
                membros.setdefault(banca.membro1, []).append(banca)
            if banca.membro2:
                membros.setdefault(banca.membro2, []).append(banca)
            if banca.membro3:
                membros.setdefault(banca.membro3, []).append(banca)

        membros_pfe.append(membros)
        periodo.append(str(ano)+"."+str(semestre))

        if ((ano == configuracao.ano) and (semestre == configuracao.semestre)):
            break

        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    anos = zip(membros_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro

    context = {
        'anos' : anos,
    }
    return render(request, 'projetos/bancas_tabela.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_index(request):
    """Menus de bancas e calendario de bancas."""
    bancas = Banca.objects.all()
    context = {
        'bancas': bancas,
    }
    return render(request, 'projetos/bancas_index.html', context)

@login_required
def encontros_marcar(request):
    """Encontros a serem agendados pelos alunos."""
    configuracao = Configuracao.objects.all().first()
    hoje = datetime.date.today()
    encontros = Encontro.objects.filter(startDate__gt=hoje)
    aluno = Aluno.objects.filter(pk=request.user.pk).first()
    projeto = Projeto.objects.filter(alocacao__aluno=aluno).\
                              distinct().\
                              filter(ano=configuracao.ano).\
                              filter(semestre=configuracao.semestre).last()

    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        agendado = None
        for encontro in encontros:
            if str(encontro.id) == check_values[0]:
                if encontro.projeto != projeto:
                    encontro.projeto = projeto
                    encontro.save()
                agendado = str(encontro.startDate)
            else:
                if encontro.projeto == projeto:
                    encontro.projeto = None
                    encontro.save()
        if agendado:
            #return HttpResponse("Agendado: "+agendado)
            mensagem = "Agendado: " + agendado
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)
        else:
            return HttpResponse("Problema! Por favor reportar.")
    else:
        context = {
            'encontros': encontros,
            'projeto': projeto,
        }
        return render(request, 'projetos/encontros.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def dinamicas_root(request):
    """Mostra os horários das próximas dinâmicas."""
    return redirect('dinamicas', "proximas")

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def dinamicas(request, periodo):
    """Mostra os horários de dinâmicas."""
    todos_encontros = Encontro.objects.all().order_by('startDate')
    if periodo == "proximas":
        hoje = datetime.date.today()
        encontros = todos_encontros.filter(startDate__gt=hoje)
    else:
        encontros = todos_encontros
    context = {
        'encontros': encontros,
        'periodo' : periodo,
    }
    return render(request, 'projetos/dinamicas.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def carrega_bancos(request):
    """rotina que carrega arquivo CSV de bancos para base de dados do servidor."""
    with open('projetos/bancos.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                #print("Colunas {} e {}".format(row[0],row[1]))
                pass
            else:
                #print('Nome: {}; Código {}'.format(row[0],row[1]))
                banco = Banco.create(nome=row[0], codigo=row[1])
                banco.save()
            line_count += 1
    mensagem = "Bancos carregados."
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, 'generic.html', context=context)
    #return HttpResponse("Bancos carregados")


@login_required
@transaction.atomic
def reembolso_pedir(request):
    """Página com sistema de pedido de reembolso."""
    configuracao = Configuracao.objects.all().first()
    usuario = PFEUser.objects.get(pk=request.user.pk)
    if usuario.tipo_de_usuario == 1:
        aluno = Aluno.objects.get(pk=request.user.pk)
        projeto = Projeto.objects.filter(alocacao__aluno=aluno).last()
    else:
        projeto = None
    if request.method == 'POST':
        reembolso = Reembolso.create(usuario)
        reembolso.descricao = request.POST['descricao']

        usuario.cpf = int(''.join(i for i in request.POST['cpf'] if i.isdigit()))
        usuario.save()

        reembolso.conta = request.POST['conta']
        reembolso.agencia = request.POST['agencia']
        reembolso.banco = Banco.objects.get(codigo=request.POST['banco'])
        reembolso.valor = request.POST['valor']

        reembolso.save() # Preciso salvar para pegar o PK
        nota_fiscal = simple_upload(request.FILES['arquivo'],
                                    path="reembolsos/",
                                    prefix=str(reembolso.pk)+"_")
        reembolso.nota = nota_fiscal[len(settings.MEDIA_URL):]

        reembolso.save()

        subject = 'Reembolso PFE : '+usuario.username
        recipient_list = configuracao.recipient_reembolso.split(";")
        recipient_list.append('pfeinsper@gmail.com') #sempre mandar para a conta do gmail
        recipient_list.append(usuario.email) #mandar para o usuário que pediu o reembolso
        if projeto:
            if projeto.orientador:
                #mandar para o orientador se houver
                recipient_list.append(projeto.orientador.user.email)
        message = message_reembolso(usuario, projeto, reembolso)
        check = email(subject, recipient_list, message)
        if check != 1:
            message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"
        return HttpResponse(message)
    else:
        bancos = Banco.objects.all().order_by(Lower("nome"), "codigo")
        context = {
            'usuario': usuario,
            'projeto': projeto,
            'bancos': bancos,
            'configuracao' : configuracao,
        }
        return render(request, 'projetos/reembolso_pedir.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def avisos_listar(request):
    """Mostra toda a tabela de avisos da coordenação do PFE."""
    configuracao = Configuracao.objects.all().first()

    qualquer_aviso = list(Aviso.objects.all())

    eventos = Evento.objects.filter(startDate__year=configuracao.ano)
    if configuracao.semestre == 1:
        qualquer_evento = list(eventos.filter(startDate__month__lt=7))
    else:
        qualquer_evento = list(eventos.filter(startDate__month__gt=6))

    avisos = sorted(qualquer_aviso+qualquer_evento, key=lambda t: t.get_data())

    #dias_passados = (datetime.date.today() - configuracao.t0).days
    context = {
        'avisos': avisos,
        'configuracao' : configuracao,
        'hoje' : datetime.date.today(),
        'filtro' : "todos",
    }
    return render(request, 'projetos/avisos_listar.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def emails(request):
    """Gera uma série de lista de emails, com alunos, professores, parceiros, etc."""
    # Deve ter recurso para pegar aluno pelos projetos, opções,
    # pois um aluno que reprova pode aparecer em duas listas.
    configuracao = Configuracao.objects.all().first()
    ano = 2018
    semestre = 2
    semestres = []
    alunos_p_semestre = []
    orientadores_p_semestre = []
    parceiros_p_semestre = []
    projetos_p_semestre = []
    bancas_p_semestre = []
    while True:
        semestres.append(str(ano)+"."+str(semestre))

        projetos_pessoas = {} # Dicionario com as pessoas do projeto

        alunos_semestre = [] # Alunos do semestre
        organizacoes = [] # Controla as organizações participantes por semestre
        orientadores = [] # Orientadores por semestre
        parceiros = [] # Pessoas que trabalham nas organizações parceiras
        membros_bancas = [] # Membros das bancas

        for projeto in Projeto.objects.filter(ano=ano).filter(semestre=semestre):
            if Aluno.objects.filter(alocacao__projeto=projeto): #checa se tem alunos
                alunos_tmp = Aluno.objects.filter(trancado=False).\
                              filter(alocacao__projeto=projeto).\
                              filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
                alunos_semestre += list(alunos_tmp)
                orientador = projeto.orientador
                parceiros = Parceiro.objects.filter(organizacao=projeto.organizacao).\
                              filter(user__is_active=True)

                if projeto.orientador not in orientadores:
                    orientadores.append(orientador) # Junta orientadores do semestre

                if projeto.organizacao not in organizacoes:
                    organizacoes.append(projeto.organizacao) # Junta organizações do semestre

                bancas = Banca.objects.filter(projeto=projeto)
                for banca in bancas:
                    if banca.membro1:
                        membros_bancas.append(banca.membro1)
                    if banca.membro2:
                        membros_bancas.append(banca.membro2)
                    if banca.membro3:
                        membros_bancas.append(banca.membro3)

                projetos_pessoas[projeto] = dict()
                projetos_pessoas[projeto]["estudantes"] = list(alunos_tmp) # Pessoas por projeto
                projetos_pessoas[projeto]["orientador"] = list([orientador]) # Pessoas por projeto
                projetos_pessoas[projeto]["parceiros"] = list(parceiros) # Pessoas por projeto

        # Parceiros de todas as organizações parceiras
        parceiros_semestre = Parceiro.objects.filter(organizacao__in=organizacoes)

        # Cria listas para enviar para templeate html
        alunos_p_semestre.append(Aluno.objects.filter(trancado=False).\
                                filter(anoPFE=ano).\
                                filter(semestrePFE=semestre).\
                                filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0]))

        #alocados_p_semestre.append(alunos_semestre)
        orientadores_p_semestre.append(orientadores)
        parceiros_p_semestre.append(parceiros_semestre)
        bancas_p_semestre.append(membros_bancas)

        projetos_p_semestre.append(projetos_pessoas)

        if ano > configuracao.ano or (ano == configuracao.ano and semestre > configuracao.semestre):
            break

        # Vai para próximo semestre
        if semestre == 1:
            semestre = 2
        else:
            ano += 1
            semestre = 1

    email_todos = zip(semestres,
                      alunos_p_semestre,  #na pratica chamaremos de aluno no template
                      orientadores_p_semestre,
                      parceiros_p_semestre,
                      bancas_p_semestre)

    email_p_semestre = zip(semestres, projetos_p_semestre)

    membros_comite = PFEUser.objects.all().filter(membro_comite=True)

    lista_todos_alunos = Aluno.objects.filter(trancado=False).\
                                 filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

    lista_todos_professores = Professor.objects.all()
    lista_todos_parceiros = Parceiro.objects.all()

    context = {
        'email_todos' : email_todos,
        'email_p_semestre' : email_p_semestre,
        'membros_comite' : membros_comite,
        'todos_alunos' : lista_todos_alunos,
        'todos_professores' : lista_todos_professores,
        'todos_parceiros' : lista_todos_parceiros,
    }
    return render(request, 'projetos/emails.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_lista(request, periodo):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    #configuracao = Configuracao.objects.all().first()
    todas_bancas = Banca.objects.all().order_by("startDate")
    if periodo == "proximas":
        hoje = datetime.date.today()
        bancas = todas_bancas.filter(startDate__gt=hoje)
    else:
        bancas = todas_bancas
    context = {
        'bancas' : bancas,
        'periodo' : periodo,
    }
    return render(request, 'projetos/bancas_lista.html', context)

def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""
    if 'inicio' in request.POST:
        try:
            banca.startDate = dateutil.parser.parse(request.POST['inicio'])
        except (ValueError, OverflowError):
            banca.startDate = None
    if 'fim' in request.POST:
        try:
            banca.endDate = dateutil.parser.parse(request.POST['fim'])
        except (ValueError, OverflowError):
            banca.endDate = None
    if 'tipo' in request.POST and request.POST['tipo'] != "":
        banca.tipo_de_banca = int(request.POST['tipo'])
    if 'local' in request.POST:
        banca.location = request.POST['local']
    if 'link' in request.POST:
        banca.link = request.POST['link']
    if 'membro1' in request.POST:
        banca.membro1 = PFEUser.objects.get(id=int(request.POST['membro1']))
    else:
        banca.membro1 = None
    if 'membro2' in request.POST:
        banca.membro2 = PFEUser.objects.get(id=int(request.POST['membro2']))
    else:
        banca.membro2 = None
    if 'membro3' in request.POST:
        banca.membro3 = PFEUser.objects.get(id=int(request.POST['membro3']))
    else:
        banca.membro3 = None
    banca.save()

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_criar(request):
    """Cria uma banca de avaliação para o projeto."""
    configuracao = Configuracao.objects.all().first()
    if request.method == 'POST':
        if 'projeto' in request.POST:
            projeto = Projeto.objects.get(id=int(request.POST['projeto']))
            banca = Banca.create(projeto)
            editar_banca(banca, request)
            # return HttpResponse( # Isso não esta bom assim, ajustar
            #     "Banca criada.<br>"+\
            #     "<a href='../bancas_index"+\
            #     "'>Voltar</a>")
            mensagem = "Banca criada."
            context = {
                "area_principal": True,
                "bancas_index": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)
        return HttpResponse("Banca não registrada, problema com identificação do projeto.")
    else:
        ano = configuracao.ano
        semestre = configuracao.semestre
        projetos = Projeto.objects.filter(ano=ano).filter(semestre=semestre).\
                                                   filter(disponivel=True).\
                                                   exclude(orientador=None)
        pessoas = PFEUser.objects.all().\
                                  filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0]).\
                                  order_by(Lower("first_name"), Lower("last_name")) # professores

        context = {
            'projetos' : projetos,
            'pessoas' : pessoas,
        }
        return render(request, 'projetos/bancas_criar.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_buscar(request):
    """Busca uma banca de avaliação para posteriormente ser editador."""
    #configuracao = Configuracao.objects.all().first()
    if request.method == 'POST':
        return HttpResponse("Acesso Inadequado.")
    else:
        bancas = Banca.objects.all().order_by("-startDate")
        context = {
            'bancas' : bancas,
        }
        return render(request, 'projetos/bancas_buscar.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_editar(request, primarykey):
    """Edita uma banca de avaliação para o projeto."""
    banca = Banca.objects.get(pk=primarykey)
    if request.method == 'POST':
        editar_banca(banca, request)
        # return HttpResponse(
        #     "Banca editada.<br>"+\
        #     "<a href='../bancas_index"+\
        #     "'>Voltar</a>")
        mensagem = "Banca editada."
        context = {
            "area_principal": True,
            "bancas_index": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    else:
        projetos = Projeto.objects.filter(disponivel=True).exclude(orientador=None).\
                                  order_by("-ano", "-semestre")

        pessoas = PFEUser.objects.all().\
                                  filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0]).\
                                  order_by(Lower("first_name"), Lower("last_name")) # professores
        context = {
            'projetos' : projetos,
            'pessoas' : pessoas,
            'banca' : banca,
        }
        return render(request, 'projetos/bancas_editar.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def todos_parceiros(request):
    """Exibe todas os parceiros (pessoas) de organizações que já submeteram projetos."""
    pareceiros = Parceiro.objects.all()
    context = {
        'pareceiros': pareceiros,
        }
    return render(request, 'projetos/todos_parceiros.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def todos_professores(request):
    """Exibe todas os professores que estão cadastrados no PFE."""
    professores = Professor.objects.all()
    context = {
        'professores': professores,
        }
    return render(request, 'projetos/todos_professores.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def comite(request):
    """Exibe os professores que estão no comitê do PFE."""
    professores = Professor.objects.filter(user__membro_comite=True)
    context = {
        'professores': professores,
        }
    return render(request, 'projetos/todos_professores.html', context)

@login_required
def minhas_bancas(request):
    """Lista as bancas agendadas para um aluno."""
    aluno = Aluno.objects.get(pk=request.user.pk)
    projetos = Projeto.objects.filter(alocacao__aluno=aluno)
    bancas = Banca.objects.filter(projeto__in=projetos).order_by("-startDate")

    context = {
        'bancas' : bancas,
    }
    return render(request, 'projetos/minhas_bancas.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def export_calendar(request, event_id):
    """Gera evento de calendário."""
    banca = Banca.objects.all().get(pk=event_id)

    cal = Calendar()
    site = Site.objects.get_current()

    cal.add('prodid', '-//PFE//Insper//')
    cal.add('version', '2.0')

    site_token = site.domain.split('.')
    site_token.reverse()
    site_token = '.'.join(site_token)

    ical_event = Event()

    ical_event['uid'] = "Banca{0}{1}{2}".format(banca.startDate.strftime("%Y%m%d%H%M%S"),
                                                banca.projeto.pk,
                                                banca.tipo_de_banca)
    ical_event.add('summary', "Banca {0}".format(banca.projeto))
    ical_event.add('dtstart', banca.startDate)
    ical_event.add('dtend', banca.endDate)
    ical_event.add('dtstamp', datetime.datetime.now().date())
    ical_event.add('tzid', "America/Sao_Paulo")
    ical_event.add('location', banca.location)

    ical_event.add('geo', (-25.598749, -46.676368))

    cal_address = vCalAddress('MAILTO:lpsoares@insper.edu.br')
    cal_address.params["CN"] = "Luciano Pereira Soares"
    ical_event.add('organizer', cal_address)

    #REMOVER OS xx DOS EMAILS
    if banca.membro1:
        atnd = vCalAddress("MAILTO:{}".format(banca.membro1.email))
        atnd.params["CN"] = "{0} {1}".format(banca.membro1.first_name, banca.membro1.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    if banca.membro2:
        atnd = vCalAddress("MAILTO:{}".format(banca.membro2.email))
        atnd.params["CN"] = "{0} {1}".format(banca.membro2.first_name, banca.membro2.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    if banca.membro3:
        atnd = vCalAddress("MAILTO:{}".format(banca.membro3.email))
        atnd.params["CN"] = "{0} {1}".format(banca.membro3.first_name, banca.membro3.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    alunos = Aluno.objects.filter(alocacao__projeto=banca.projeto).filter(trancado=False)
    for aluno in alunos:
        atnd = vCalAddress("MAILTO:{}".format(aluno.user.email))
        atnd.params["CN"] = "{0} {1}".format(aluno.user.first_name, aluno.user.last_name)
        atnd.params["ROLE"] = "REQ-PARTICIPANT"
        ical_event.add("attendee", atnd, encode=0)

    description = "Banca do Projeto {0}".format(banca.projeto)
    if banca.link:
        description += "\n\nLink: {0}".format(banca.link)
    description += "\n\nOrientador:\n- {0}".format(banca.projeto.orientador)
    if banca.membro1 or banca.membro2 or banca.membro3:
        description += "\n\nMembros da Banca:"
        if banca.membro1:
            description += "\n- {0} {1}".format(banca.membro1.first_name, banca.membro1.last_name)
        if banca.membro2:
            description += "\n- {0} {1}".format(banca.membro2.first_name, banca.membro2.last_name)
        if banca.membro3:
            description += "\n- {0} {1}".format(banca.membro3.first_name, banca.membro3.last_name)
    description += "\n\nAlunos:"
    for aluno in alunos:
        description += "\n- {0} {1}".format(aluno.user.first_name, aluno.user.last_name)

    ical_event.add('description', description)

    cal.add_component(ical_event)

    response = HttpResponse(cal.to_ical())
    response['Content-Type'] = 'text/calendar'
    response['Content-Disposition'] = 'attachment; filename=Banca{0}.ics'.format(banca.pk)

    return response

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_agendamento(request):
    """Lista todas as bancas agendadas futuras para enviar agendaementos."""
    todas_bancas = Banca.objects.all().order_by("startDate")
    hoje = datetime.date.today()
    bancas = todas_bancas.filter(startDate__gt=hoje)
    context = {
        'bancas' : bancas,
    }
    return render(request, 'projetos/bancas_agendamento.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def mapeamento(request):
    """Chama o mapeamento entre estudantes e projetos do próximo semestre."""
    configuracao = Configuracao.objects.all().first()

    if configuracao.semestre == 1:
        ano = configuracao.ano
        semestre = 2
    else:
        ano = configuracao.ano+1
        semestre = 1

    return redirect('mapeamento_estudante_projeto', anosemestre="{0}.{1}".format(ano, semestre))

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def mapeamento_estudante_projeto(request, anosemestre):
    """Mapeamento entre estudantes e projetos."""
    configuracao = Configuracao.objects.first()

    ano = int(anosemestre.split(".")[0])
    semestre = int(anosemestre.split(".")[1])

    #lista_projetos = list(zip(*ordena_projetos(False, ano, semestre)))
    lista_propostas = list(zip(*ordena_propostas(False, ano, semestre)))
    if lista_propostas:
        propostas = lista_propostas[0]
    else:
        propostas = []

    alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
                               filter(anoPFE=ano).\
                               filter(semestrePFE=semestre).\
                               order_by(Lower("user__first_name"), Lower("user__last_name"))
    opcoes = []
    for aluno in alunos:
        opcoes_aluno = []
        alocacaos = Alocacao.objects.filter(aluno=aluno)
        for proposta in propostas:
            opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
            if opcao:
                opcoes_aluno.append(opcao)
            else:
                try:
                    proj = Projeto.objects.get(proposta=proposta)
                    if alocacaos.filter(projeto=proj):
                        # Cria uma opção temporaria
                        opc = Opcao()
                        opc.prioridade = 0
                        opc.proposta = proposta
                        opc.aluno = aluno
                        opcoes_aluno.append(opc)
                    else:
                        opcoes_aluno.append(None)
                except Projeto.DoesNotExist:
                    opcoes_aluno.append(None)

        opcoes.append(opcoes_aluno)

    estudantes = zip(alunos, opcoes)
    context = {
        'estudantes': estudantes,
        'propostas': propostas,
        'configuracao': configuracao,
        'ano': ano,
        'semestre': semestre,
        'loop_anos': range(2018, configuracao.ano+1),
    }
    return render(request, 'projetos/mapeamento_estudante_projeto.html', context)

def projeto_feedback(request):
    """Para Feedback das Organizações Parceiras."""
    if request.method == 'POST':
        feedback = Feedback.create()
        feedback.nome = request.POST.get("nome", "")
        feedback.email = request.POST.get("email", "")
        feedback.empresa = request.POST.get("empresa", "")
        feedback.tecnico = request.POST.get("tecnico", "")
        feedback.comunicacao = request.POST.get("comunicacao", "")
        feedback.organizacao = request.POST.get("organizacao", "")
        feedback.outros = request.POST.get("outros", "")
        feedback.save()
        mensagem = "Feedback recebido, obrigado!"
        context = {
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
        #return HttpResponse("Feedback recebido, obrigado!")
    else:
        context = {
        }
        return render(request, 'projetos/projeto_feedback.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def lista_feedback(request):
    """Lista todos os feedback das Organizações Parceiras."""

    context = {
        'feedbacks' : Feedback.objects.all().order_by("-data"),
        'SERVER_URL' : settings.SERVER,
    }
    return render(request, 'projetos/lista_feedback.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    context = {
        'feedback' : Feedback.objects.get(id=feedback_id),
    }
    return render(request, 'projetos/mostra_feedback.html', context)

#@login_required
#@permission_required("users.altera_professor", login_url='/projetos/')
def avaliacao(request, primarykey): #acertar isso para pk
    """Cria uma tela para preencher avaliações de bancas."""
    try:
        projeto = Projeto.objects.get(pk=primarykey)

        try:
            banca = Banca.objects.filter(projeto=projeto).order_by("startDate").last()
        except Banca.DoesNotExist:
            return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    except Projeto.DoesNotExist:
        return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')
        #raise Http404("Poll does not exist")

    objetivos = ObjetidosDeAprendizagem.objects.filter(avaliacao_banca=True)

    professores = PFEUser.objects.all().\
                        filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0])

    administradores = PFEUser.objects.all().\
                        filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[3][0])

    pessoas = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    if request.method == 'POST':
        if 'avaliador' in request.POST:
            julgamento = Avaliacao.create(projeto)

            #print(PFEUser.objects.get(pk=int(request.POST['avaliador'])).first_name)
            julgamento.avaliador = PFEUser.objects.get(pk=int(request.POST['avaliador']))
            # julgamento.avaliador = PFEUser.objects.get(pk=request.user.pk)

            #if request.POST['tipo_banca'] == "final":
            #    julgamento.tipo_de_avaliacao = 0
            #else:
            #    julgamento.tipo_de_avaliacao = 1
            julgamento.tipo_de_avaliacao = banca.tipo_de_banca

            if 'objetivo.1' in request.POST:
                pk_objetivo1 = int(request.POST['objetivo.1'].split('.')[0])
                julgamento.objetivo1 = ObjetidosDeAprendizagem.objects.get(pk=pk_objetivo1)
                julgamento.objetivo1_conceito = request.POST['objetivo.1'].split('.')[1]

            if 'objetivo.2' in request.POST:
                pk_objetivo2 = int(request.POST['objetivo.2'].split('.')[0])
                julgamento.objetivo2 = ObjetidosDeAprendizagem.objects.get(pk=pk_objetivo2)
                julgamento.objetivo2_conceito = request.POST['objetivo.2'].split('.')[1]

            if 'objetivo.3' in request.POST:
                pk_objetivo3 = int(request.POST['objetivo.3'].split('.')[0])
                julgamento.objetivo3 = ObjetidosDeAprendizagem.objects.get(pk=pk_objetivo3)
                julgamento.objetivo3_conceito = request.POST['objetivo.3'].split('.')[1]

            if 'objetivo.4' in request.POST:
                pk_objetivo4 = int(request.POST['objetivo.4'].split('.')[0])
                julgamento.objetivo4 = ObjetidosDeAprendizagem.objects.get(pk=pk_objetivo4)
                julgamento.objetivo4_conceito = request.POST['objetivo.4'].split('.')[1]

            if 'objetivo.5' in request.POST:
                pk_objetivo5 = int(request.POST['objetivo.5'].split('.')[0])
                julgamento.objetivo5 = ObjetidosDeAprendizagem.objects.get(pk=pk_objetivo5)
                julgamento.objetivo5_conceito = request.POST['objetivo.5'].split('.')[1]

            if 'observacoes' in request.POST:
                julgamento.observacoes = request.POST['observacoes']

            julgamento.save()

            message = "<h3>Avaliação PFE</h3><br>\n"
            message += "<b>Título do Projeto:</b> {0}<br>\n".format(projeto.get_titulo())
            message += "<b>Organização:</b> {0}<br>\n".format(projeto.organizacao)
            message += "<b>Orientador:</b> {0}<br>\n".format(projeto.orientador)
            message += "<b>Avaliador:</b> {0}<br>\n".format(julgamento.avaliador)
            message += "<b>Data:</b> {0}<br>\n".format(banca.startDate.strftime("%d/%m/%Y %H:%M"))

            if julgamento.tipo_de_avaliacao == 0:
                message += "<b>Banca:</b> final<br>\n"
            else:
                message += "<b>Banca:</b> Intermediária<br>\n"

            message += "<br>\n"
            message += "<b>Conceitos:</b><br>\n"
            message += "<table style='border: 1px solid black; "
            message += "border-collapse:collapse; padding: 0.3em;'>"
            if julgamento.objetivo1:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento.objetivo1)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(julgamento.objetivo1_conceito)
            if julgamento.objetivo2:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento.objetivo2)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(julgamento.objetivo2_conceito)
            if julgamento.objetivo3:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento.objetivo3)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(julgamento.objetivo3_conceito)
            if julgamento.objetivo4:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento.objetivo4)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(julgamento.objetivo4_conceito)
            if julgamento.objetivo5:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento.objetivo5)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(julgamento.objetivo5_conceito)
            message += "</table>"

            message += "<br>\n<br>\n"
            message += "<b>Observações:</b>\n"
            message += "<p style='border:1px; border-style:solid; padding: 0.3em; margin: 0;'>"
            message += julgamento.observacoes.replace('\n', '<br>\n')
            message += "</p>"
            message += "<br>\n<br>\n"

            message += "<br><b>Objetivos de Aprendizagem</b>"
            for objetivo in objetivos:
                message += "<br><b>{0}</b>: {1}".format(objetivo.titulo, objetivo.objetivo)
                message += "<table "
                message += "style='border:1px solid black; border-collapse:collapse; width:100%;'>"
                message += "<tr>"
                message += "<th style='border: 1px solid black; width:18%;'>"
                message += "Insatisfatório (I)</th>"
                message += "<th style='border: 1px solid black; width:18%;'>"
                message += "Em Desenvolvimento (D)</th>"
                message += "<th style='border: 1px solid black; width:18%;'>"
                message += "Essencial (C)</th>"
                message += "<th style='border: 1px solid black; width:18%;'>"
                message += "Proficiente (B)</th>"
                message += "<th style='border: 1px solid black; width:18%;'>"
                message += "Avançado (A)</th>"
                message += "</tr>"
                message += "<tr>"

                message += "<td style='border: 1px solid black;'>"
                message += "{0}".format(objetivo.rubrica_I)
                message += "</td>"

                message += "<td style='border: 1px solid black;'>"
                message += "{0}".format(objetivo.rubrica_D)
                message += "</td>"

                message += "<td style='border: 1px solid black;'>"
                message += "{0}".format(objetivo.rubrica_C)
                message += "</td>"

                message += "<td style='border: 1px solid black;'>"
                message += "{0}".format(objetivo.rubrica_B)
                message += "</td>"

                message += "<td style='border: 1px solid black;'>"
                message += "{0}".format(objetivo.rubrica_A)
                message += "</td>"

                message += "</tr>"
                message += "</table>"

            subject = 'Banca PFE : {0}'.format(projeto)
            recipient_list = [projeto.orientador.user.email, julgamento.avaliador.email,]
            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

            resposta = "Avaliação submetida e enviada para:<br>"
            for recipient in recipient_list:
                resposta += "&bull; {0}<br>".format(recipient)
            resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"
            context = {
                "area_principal": True,
                "mensagem": resposta,
            }
            return render(request, 'generic.html', context=context)
            #return HttpResponse(resposta)

        return HttpResponse("Avaliação não submetida.")
    else:
        # mes = datetime.date.today().month
        # if mes <= 4 or (mes > 7 and mes < 11):
        #     guess_banca = 1 # intermediaria
        # else:
        #     guess_banca = 0 # final

        context = {
            'pessoas' : pessoas,
            'objetivos': objetivos,
            'projeto': projeto,
            'banca' : banca,
            #'guess_banca' : guess_banca,
        }
        return render(request, 'projetos/avaliacao.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def edita_aviso(request, primakey):
    """Edita aviso."""
    aviso = Aviso.objects.get(pk=primakey)
    context = {
        'aviso': aviso,
    }
    return render(request, 'projetos/edita_aviso.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def validate_aviso(request):
    """Ajax para validar avisos."""
    aviso_id = int(request.GET.get('aviso', None))
    checked = request.GET.get('checked', None) == "true"

    if aviso_id == 0:
        avisos = Aviso.objects.all()
        for aviso in avisos:
            aviso.realizado = False
            aviso.save()
    else:
        aviso = Aviso.objects.get(id=aviso_id)
        aviso.realizado = checked
        aviso.save()

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def conceitos_obtidos(request, primarykey): #acertar isso para pk
    """Visualiza os conceitos obtidos pelos alunos no projeto."""
    try:
        projeto = Projeto.objects.get(pk=primarykey)
        # try:
        #     banca = Banca.objects.filter(projeto=projeto).order_by("startDate").last()
        # except Banca.DoesNotExist:
        #     return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    except Projeto.DoesNotExist:
        return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

    objetivos = ObjetidosDeAprendizagem.objects.filter(avaliacao_banca=True)
    banca_inter = Avaliacao.objects.filter(projeto=projeto, tipo_de_avaliacao=1).\
                                    order_by('avaliador', '-momento')
    banca_final = Avaliacao.objects.filter(projeto=projeto, tipo_de_avaliacao=0).\
                                    order_by('avaliador', '-momento')

    # Quando mudar para Postgres isso vai funcionar.
    #.order_by('momento').distinct('avaliador')

    context = {
        'objetivos': objetivos,
        'projeto': projeto,
        'banca_inter' : banca_inter,
        'banca_final' : banca_final,
    }

    return render(request, 'projetos/conceitos_obtidos.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def certificados_submetidos(request):
    """Lista os Certificados Emitidos."""
    certificados = Certificado.objects.all()
    context = {
        'certificados': certificados,
    }
    return render(request, 'projetos/certificados_submetidos.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def cadastrar_organizacao(request):
    """Cadastra Organização na base de dados do PFE."""

    if request.method == 'POST':
        if 'nome' in request.POST and 'sigla' in request.POST:
            organizacao = Organizacao.create()
            organizacao.nome = request.POST['nome']
            organizacao.sigla = request.POST['sigla']

            organizacao.endereco = request.POST['endereco']
            organizacao.website = request.POST['website']
            organizacao.informacoes = request.POST['informacoes']

            cnpj = request.POST['cnpj']
            if cnpj:
                organizacao.cnpj = cnpj[:2]+cnpj[3:6]+cnpj[7:10]+cnpj[11:15]+cnpj[16:18]

            organizacao.inscricao_estadual = request.POST['inscricao_estadual']
            organizacao.razao_social = request.POST['razao_social']
            organizacao.ramo_atividade = request.POST['ramo_atividade']

            if 'logo' in request.FILES:
                logotipo = simple_upload(request.FILES['logo'],
                                         path=get_upload_path(organizacao, ""))
                organizacao.logotipo = logotipo[len(settings.MEDIA_URL):]

            organizacao.save()

            mensagem = "Organização inserida na base de dados."
            context = {
                "voltar": True,
                "cadastrar_organizacao": True,
                "organizacoes_lista": True,
                "area_principal": True,
                "mensagem": mensagem,
            }

        else:
            mensagem = "<h3 style='color:red'>Falha na inserção na base da dados.<h3>"
            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": mensagem,
            }

        return render(request, 'generic.html', context=context)

    context = {
    }
    return render(request, 'projetos/cadastra_organizacao.html', context)



@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def cadastrar_usuario(request):
    """Cadastra usuário na base de dados do PFE."""

    if request.method == 'POST':
        if 'email' in request.POST:
            usuario = PFEUser.create()

            #is_active

            usuario.email = request.POST['email']

            # (1, 'aluno'),
            # (2, 'professor'),
            # (3, 'parceiro'),
            # (4, 'administrador')

            if request.POST['tipo_de_usuario'] == "estudante":
                usuario.tipo_de_usuario = 1
            elif request.POST['tipo_de_usuario'] == "professor":
                usuario.tipo_de_usuario = 2
            elif request.POST['tipo_de_usuario'] == "parceiro":
                usuario.tipo_de_usuario = 3
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            if usuario.tipo_de_usuario == 1 or usuario.tipo_de_usuario == 2:
                usuario.username = request.POST['email'].split("@")[0]
            elif usuario.tipo_de_usuario == 3:
                usuario.username = request.POST['email'].split("@")[0] + "." + \
                    request.POST['email'].split("@")[1].split(".")[0]
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            if 'nome' in request.POST and len(request.POST['nome'].split()) > 1:
                usuario.first_name = request.POST['nome'].split()[0]
                usuario.last_name = " ".join(request.POST['nome'].split()[1:])
            else:
                return HttpResponse("Não foi inserido o nome completo.", status=401)

            if 'genero' in request.POST:
                if request.POST['genero'] == "masculino":
                    usuario.genero = "M"
                elif request.POST['genero'] == "feminino":
                    usuario.genero = "F"
            else:
                usuario.genero = "X"

            cpf = request.POST['cpf']
            if cpf:
                usuario.cpf = cpf[:3]+cpf[4:7]+cpf[8:11]+cpf[12:13]

            if 'linkedin' in request.POST:
                usuario.linkedin = request.POST['linkedin']

            usuario.save()

            if usuario.tipo_de_usuario == 1: #estudante

                estudante = Aluno.objects.get(user=usuario)

                if 'matricula' in request.POST:
                    estudante.matricula = request.POST['matricula']

                # ('C', 'Computação'),
                # ('M', 'Mecânica'),
                # ('X', 'Mecatrônica'),

                if request.POST['curso'] == "computacao":
                    estudante.curso = 'C'
                elif request.POST['curso'] == "mecanica":
                    estudante.curso = 'M'
                elif request.POST['curso'] == "mecatronica":
                    estudante.curso = 'X'
                else:
                    return HttpResponse("Algum erro não identificado.", status=401)

                estudante.anoPFE = int(request.POST['ano'])
                estudante.semestrePFE = int(request.POST['semestre'])

                estudante.save()

            elif usuario.tipo_de_usuario == 2: #professor
                professor = Professor.objects.get(user=usuario)

                # ("TI", "Tempo Integral"),
                # ("TP", 'Tempo Parcial'),

                if request.POST['dedicacao'] == "ti":
                    professor.curso = 'TI'
                elif request.POST['dedicacao'] == "tp":
                    professor.curso = 'TP'
                else:
                    return HttpResponse("Algum erro não identificado.", status=401)

                if 'areas' in request.POST:
                    professor.areas = request.POST['areas']

                if 'website' in request.POST:
                    professor.website = request.POST['website']

                if 'lattes' in request.POST:
                    professor.lattes = request.POST['lattes']

                professor.save()

            elif usuario.tipo_de_usuario == 3: #Parceiro
                parceiro = Parceiro.objects.get(user=usuario)

                if 'cargo' in request.POST:
                    parceiro.cargo = request.POST['cargo']

                if 'telefone' in request.POST:
                    parceiro.telefone = request.POST['telefone']

                if 'celular' in request.POST:
                    parceiro.celular = request.POST['celular']

                if 'skype' in request.POST:
                    parceiro.skype = request.POST['skype']

                if 'observacao' in request.POST:
                    parceiro.observacao = request.POST['observacao']

                parceiro.organizacao = Organizacao.objects.get(pk=int(request.POST['organizacao']))

                if 'principal_contato' in request.POST:
                    parceiro.principal_contato = True

                parceiro.save()

            mensagem = "Usuário inserido na base de dados."
        else:
            mensagem = "<h3 style='color:red'>Falha na inserção na base da dados.<h3>"
        context = {
            "voltar": True,
            "cadastrar_usuario": True,
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    context = {
        "organizacoes" : Organizacao.objects.all(),
    }
    return render(request, 'projetos/cadastra_usuario.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def migracao(request):
    """Migra projetos (temporário)."""

    return HttpResponse("Feito.")

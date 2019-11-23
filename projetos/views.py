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

from io import BytesIO # Para gerar o PDF
import dateutil.parser

import tablib
from tablib import Databook

from xhtml2pdf import pisa # Para gerar o PDF

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.db import transaction
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.template.loader import get_template
from django.utils import timezone

from users.models import PFEUser, Aluno, Professor, Parceiro, Opcao
from .models import Projeto, Empresa, Configuracao, Evento, Anotacao
from .models import Banca, Documento, Encontro, Banco, Reembolso, Aviso, Entidade
#from .models import Disciplina

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

    usuario = PFEUser.objects.get(pk=request.user.pk)
    if usuario.tipo_de_usuario == 1:
        aluno = Aluno.objects.get(pk=request.user.pk)
        projeto = Projeto.objects.filter(alocacao__aluno=aluno).last()
    else:
        projeto = None

    #request.session['num_visits'] = num_visits + 1

    configuracao = Configuracao.objects.first()
    vencido = timezone.now() > configuracao.prazo
    context = {
        'projeto': projeto,
        'configuracao': configuracao,
        'vencido': vencido,
    }
    #'num_visits': num_visits,

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
            return HttpResponse("Prazo para seleção de projetos vencido!")
            #<br>Hora atual:  "+str(timezone.now())+"<br>Hora limite:"+str(configuracao.prazo)
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

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def histograma(request):
    """Exibe um histograma com a procura dos projetos pelos alunos."""
    configuracao = Configuracao.objects.all().first()
    opcoes_list = []
    projetos = Projeto.objects.filter(ano=configuracao.ano).filter(semestre=configuracao.semestre)
    for projeto in projetos:
        opcoes = Opcao.objects.filter(projeto=projeto)
        opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
        opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).\
                                       filter(aluno__semestrePFE=configuracao.semestre)
        count = 0
        for opcao in opcoes_validas:
            if opcao.prioridade <= 5:
                count += 1
        opcoes_list.append(count)
    mylist = zip(projetos, opcoes_list)
    mylist = sorted(mylist, key=lambda x: x[1], reverse=True)
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

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def propor(request):
    """Monta grupos de PFE."""
    ############################################
    ## COLOCAR ESSE VALOR ACESSIVEL NO SISTEMA #
    ############################################
    pref_pri_cr = 0.1  # Ficar longe da prioridade tem um custo de 5% na selecao do projeto

    configuracao = Configuracao.objects.all().first()
    projeto_list = []
    opcoes_list = []
    projetos = Projeto.objects.all()
    if request.method == 'POST':
        min_group = int(request.POST.get('min', 0))
        max_group = int(request.POST.get('max', 5))
        projetos_ajustados = {}
        alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
                               filter(anoPFE=configuracao.ano).\
                               filter(semestrePFE=configuracao.semestre)

        #Checa se o CR de todos os alunos esta coreto
        for aluno in alunos:
            if aluno.cr < 5.0:
                return HttpResponse("Aluno: "+aluno.user.first_name+" "+aluno.user.last_name+\
                                    " ("+aluno.user.username+') com CR = '+str(aluno.cr))

        #Cria Lista para todos os projetos
        for projeto in projetos:
            projetos_ajustados[projeto] = []

        #Posiciona os alunos nas suas primeiras opcoes (supondo projeto permitir)
        for aluno in alunos:
            opcoes = Opcao.objects.filter(aluno=aluno)
            if len(opcoes) >= 5: # checa se aluno preencheu formulario
                #busca nas opcoes do aluno
                opcoes1 = get_opcao(1, opcoes, min_group, max_group, projetos_ajustados)
                projetos_ajustados[opcoes1.projeto].append(opcoes1)

        #Posiciona os alunos nas suas melhores opcoes sem estourar o tamanho do grupo
        balanceado = False
        count = 200
        menor_grupo = 1 # usado para elimnar primeiro grupos de 1, depois de 2, etc
        while (not balanceado) and (count > 0):
            balanceado = True
            balanceado_max = False
            # Removendo alunos de grupos superlotados
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
                            opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno)
                            next_op = get_next_opcao(remove_opcao.prioridade, opcoes)
                            if next_op != 0:
                                #busca nas opcoes do aluno
                                op2 = get_opcao(next_op, opcoes, min_group,
                                                max_group, projetos_ajustados)
                                if op2: #op2 != None
                                    balanceado_max = False
                                    balanceado = False
                                    menor_grupo = 1
                                    projetos_ajustados[projeto].remove(remove_opcao)
                                    projetos_ajustados[op2.projeto].append(op2)
                                    #print("Movendo(a) "+remove_opcao.aluno.user.first_name.lower()\
                                    #+" (DE): "+pr.titulo+" (PARA):"+op2.projeto.titulo)

            # Realocando alunos de grupos muito pequenos (um aluno por vez)
            for projeto, ops in projetos_ajustados.items():
                remove_opcao = None
                remove_projeto = None
                if ops and (len(ops) <= menor_grupo): #(len(ops) > 0)
                    for option in ops:
                        if remove_opcao is None:
                            if option.prioridade < 5:  #Não tirar aluno com prioridade > que 5
                                remove_opcao = option
                                remove_projeto = projeto
                        elif(option.aluno.cr < remove_opcao.aluno.cr) and\
                                (option.prioridade < 5):
                            remove_opcao = option
                            remove_projeto = projeto
                if remove_opcao is not None:
                    opcoes = Opcao.objects.filter(aluno=remove_opcao.aluno)
                    next_op = get_next_opcao(remove_opcao.prioridade, opcoes)
                    if next_op != 0:
                        #busca nas opcoes do aluno
                        op2 = get_opcao(next_op, opcoes, min_group, max_group, projetos_ajustados)
                        if op2: #op2 != None:
                            balanceado = False
                            menor_grupo = 1
                            projetos_ajustados[remove_projeto].remove(remove_opcao)
                            projetos_ajustados[op2.projeto].append(op2)
                            #print("Movendo(b) "+remove_opcao.aluno.user.first_name.lower()+\
                            # " (DE): "+remove_projeto.titulo+" (PARA):"+op2.projeto.titulo)

            if (menor_grupo < min_group) and balanceado: #caso todos grupos com menor_grupo ja foram
                menor_grupo += 1
                balanceado = False

        #Cria lista para enviar para o template html
        for projeto, ops in projetos_ajustados.items():
            if ops: #len(ops) > 0
                projeto_list.append(projeto)
                opcoes_list.append(ops)
        mylist = zip(projeto_list, opcoes_list)
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
def index_professor(request):
    """Mostra página principal do usuário professor."""
    return render(request, 'index_professor.html')

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def completo(request, primakey):
    """Mostra um projeto por completo."""
    projeto = Projeto.objects.filter(pk=primakey).first()  # acho que tem de ser get
    opcoes = Opcao.objects.filter(projeto=projeto)
    configuracao = Configuracao.objects.all().first()
    context = {
        'projeto': projeto,
        'opcoes': opcoes,
        'configuracao': configuracao,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/projeto_completo.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def areas(request):
    """Mostra distribuição por área de interesse dos alunos."""
    configuracao = Configuracao.objects.all().first()
    alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
                           filter(anoPFE=configuracao.ano).\
                           filter(semestrePFE=configuracao.semestre)

    inovacao_social = alunos.filter(inovacao_social=True).count()
    ciencia_dos_dados = alunos.filter(ciencia_dos_dados=True).count()
    modelagem_3d = alunos.filter(modelagem_3D=True).count()
    manufatura = alunos.filter(manufatura=True).count()
    resistencia_dos_materiais = alunos.filter(resistencia_dos_materiais=True).count()
    modelagem_de_sistemas = alunos.filter(modelagem_de_sistemas=True).count()
    controle_e_automacao = alunos.filter(controle_e_automacao=True).count()
    termodinamica = alunos.filter(termodinamica=True).count()
    fluidodinamica = alunos.filter(fluidodinamica=True).count()
    eletronica_digital = alunos.filter(eletronica_digital=True).count()
    programacao = alunos.filter(programacao=True).count()
    inteligencia_artificial = alunos.filter(inteligencia_artificial=True).count()
    banco_de_dados = alunos.filter(banco_de_dados=True).count()
    computacao_em_nuvem = alunos.filter(computacao_em_nuvem=True).count()
    visao_computacional = alunos.filter(visao_computacional=True).count()
    computacao_de_alto_desempenho = alunos.filter(computacao_de_alto_desempenho=True).count()
    robotica = alunos.filter(robotica=True).count()
    realidade_virtual_aumentada = alunos.filter(realidade_virtual_aumentada=True).count()
    protocolos_de_comunicacao = alunos.filter(protocolos_de_comunicacao=True).count()
    eficiencia_energetica = alunos.filter(eficiencia_energetica=True).count()
    administracao_economia_financas = alunos.filter(administracao_economia_financas=True).count()

    context = {
        'inovacao_social':inovacao_social,
        'ciencia_dos_dados':ciencia_dos_dados,
        'modelagem_3D':modelagem_3d,
        'manufatura':manufatura,
        'resistencia_dos_materiais':resistencia_dos_materiais,
        'modelagem_de_sistemas':modelagem_de_sistemas,
        'controle_e_automacao':controle_e_automacao,
        'termodinamica':termodinamica,
        'fluidodinamica': fluidodinamica,
        'eletronica_digital':eletronica_digital,
        'programacao':programacao,
        'inteligencia_artificial':inteligencia_artificial,
        'banco_de_dados':banco_de_dados,
        'computacao_em_nuvem':computacao_em_nuvem,
        'visao_computacional': visao_computacional,
        'computacao_de_alto_desempenho':computacao_de_alto_desempenho,
        'robotica':robotica,
        'realidade_virtual_aumentada':realidade_virtual_aumentada,
        'protocolos_de_comunicacao':protocolos_de_comunicacao,
        'eficiencia_energetica':eficiencia_energetica,
        'administracao_economia_financas':administracao_economia_financas,
    }
    return render(request, 'projetos/areas.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacoes_lista(request):
    """Exibe todas as organizações que já submeteram projetos."""
    organizacoes = Empresa.objects.all()
    fechados = []
    for organizacao in organizacoes:
        fechados.append(Projeto.objects.filter(empresa=organizacao).\
                 filter(alocacao__isnull=False).distinct().count())
    organizacoes_list = zip(organizacoes, fechados)
    total_organizacoes = Empresa.objects.all().count()
    total_submetidos = Projeto.objects.all().count()
    total_fechados = Projeto.objects.filter(alocacao__isnull=False).distinct().count()
    context = {
        'organizacoes_list': organizacoes_list,
        'total_organizacoes': total_organizacoes,
        'total_submetidos': total_submetidos,
        'total_fechados': total_fechados,
        }
    return render(request, 'projetos/organizacoes_lista.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacao_completo(request, org): #acertar isso para pk
    """Exibe detalhes das organizações parceiras."""
    organization = Empresa.objects.get(login=org)  # acho que tem de ser get
    context = {
        'organization': organization,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/organizacao_completo.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def cria_anotacao(request, login): #acertar isso para pk
    """Cria um anotação para uma organização parceira."""
    organization = Empresa.objects.get(login=login)  # acho que tem de ser get
    if request.method == 'POST':
        if 'anotacao' in request.POST:
            anotacao = Anotacao.create(organization)
            anotacao.autor = PFEUser.objects.get(pk=request.user.pk)
            anotacao.texto = request.POST['anotacao']
            anotacao.save()
            return HttpResponse(""""
                Anotação criada.<br><a href='../organizacao/"+login+"'>Volta para organização</a>
            """)
        return HttpResponse("Anotação não criada.")
    else:
        context = {
            'organization': organization,
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
        return HttpResponse("Chamada irregular : Base de dados desconhecida = "+modelo)
    dataset = resource.export()
    if(formato == "xls" or formato == "xlsx"):
        response = HttpResponse(dataset.xlsx, content_type='application/ms-excel')
        formato = "xlsx"
    elif formato == "json":
        response = HttpResponse(dataset.json, content_type='application/json')
    elif formato == "csv":
        response = HttpResponse(dataset.csv, content_type='text/csv')
    else:
        return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)
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
        return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)
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
    return HttpResponse("E-mail enviado.")

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

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio(request, modelo, formato):
    """Gera relatorios."""
    configuracao = Configuracao.objects.all().first()

    if modelo == "projetos":
        context = {
            'projetos': Projeto.objects.all(),
            'configuracao': configuracao,
        }
        if(formato == "html" or formato == "HTML"):
            return render(request, 'projetos/relatorio_projetos.html', context)
        elif(formato == "pdf" or formato == "PDF"):
            pdf = render_to_pdf('projetos/relatorio_projetos.html', context)
            return HttpResponse(pdf.getvalue(), content_type='application/pdf')

    elif modelo == "alunos":
        context = {
            'alunos': Aluno.objects.all().filter(user__tipo_de_usuario=1).\
                                          filter(anoPFE=configuracao.ano).\
                                          filter(semestrePFE=configuracao.semestre),
            'configuracao': configuracao,
        }
        if(formato == "html" or formato == "HTML"):
            return render(request, 'projetos/relatorio_alunos.html', context)
        if(formato == "pdf" or formato == "PDF"):
            pdf = render_to_pdf('projetos/relatorio_alunos.html', context)
            return HttpResponse(pdf.getvalue(), content_type='application/pdf')
    else:
        return HttpResponse("Chamada irregular : Base de dados desconhecida = "+modelo)

    return HttpResponse("Chamada irregular : Formato desconhecido = "+formato)

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
    return HttpResponse("E-mail enviado.")

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_fechados(request):
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
        for doc in Documento.objects.filter(organizacao=projeto.empresa).\
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
        for doc in Documento.objects.filter(organizacao=projeto.empresa).\
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

# ME PARECE QUE ESTA EM REDUNDÂNCIA, REMOVER NO FUTURO #

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def todos(request):
    """Lista todos os projetos Fechados."""
    #configuracao = Configuracao.objects.all().first()
    projetos = []
    alunos_list = []
    prioridade_list = []
    nalunos = 0
    qtd_prioridades = [0, 0, 0, 0, 0, 0]   # para grafico de pizza no final

    for projeto in Projeto.objects.all():
        alunos_pfe = Aluno.objects.filter(alocacao__projeto=projeto)
        if alunos_pfe: # len(alunos_pfe) > 0:
            projetos.append(projeto)
            alunos_list.append(alunos_pfe)
            nalunos += len(alunos_pfe)
            #alunos = []
            prioridades = []
            for aluno in alunos_pfe:
                opcoes = Opcao.objects.filter(projeto=projeto)
                opcoes_alunos = opcoes.filter(aluno__user__tipo_de_usuario=1)
                #opcoes_validas = opcoes_alunos.filter(aluno__anoPFE=configuracao.ano).\
                #                               filter(aluno__semestrePFE=configuracao.semestre)
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
    }
    return render(request, 'projetos/todos.html', context)

@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""
    eventos = Evento.objects.exclude(name="Aula PFE").exclude(name="Laboratório")
    aulas = Evento.objects.filter(name="Aula PFE")
    laboratorios = Evento.objects.filter(name="Laboratório")
    context = {
        'eventos': eventos,
        'aulas': aulas,
        'laboratorios': laboratorios,
    }
    return render(request, 'projetos/calendario.html', context)

@login_required
def submissao(request):
    """Para perguntas descritivas ao aluno de onde trabalho, entidades, sociais e familia."""
    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 1:
        return HttpResponse("Você não está cadastrado como aluno")
    configuracao = Configuracao.objects.first()
    aluno = Aluno.objects.get(pk=request.user.pk)
    if request.method == 'POST':
        if timezone.now() > configuracao.prazo:
            #<br>Hora atual:  "+str(timezone.now())+"<br>Hora limite:"+str(configuracao.prazo)
            return HttpResponse("Prazo para o preenchimento do formulário vencido!")

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
    filename = file_system_storage.save(path+prefix+myfile.name, myfile)
    uploaded_file_url = file_system_storage.url(filename)
    return uploaded_file_url

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def carrega(request, dado):
    """Faz o upload de arquivos CSV para o servidor."""
    # https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
    if request.method == 'POST':

        dataset = tablib.Dataset()

        if dado == "disciplinas":
            resource = DisciplinasResource()
        if dado == "alunos":
            resource = AlunosResource()
        else:
            raise Http404

        new_data = request.FILES['arquivo'].readlines()
        entradas = ""
        for i in new_data:
            string = i.decode("utf-8")
            entradas += re.sub('[^A-Za-z0-9À-ÿ, \r\n@._]+', '', string) #Limpa caracteres especiais

        #imported_data = dataset.load(entradas, format='csv')
        dataset.insert_col(0, col=lambda row: None, header="id")

        result = resource.import_data(dataset, dry_run=True, raise_errors=True)

        if not result.has_errors():
            resource.import_data(dataset, dry_run=False)  # Actually import now
            string_html = "Importado: <br>"
            for row_values in dataset:
                string_html += str(row_values) + "<br>"
            return HttpResponse(string_html)
        else:
            return HttpResponse("Erro ao carregar arquivo."+str(result))

    return render(request, 'projetos/import.html')

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
                return HttpResponse("Documento Confidencial")
        with open(file_path, 'rb') as file:
            response = get_response(file, path)
            if not response:
                return HttpResponse("Erro ao carregar arquivo (formato não suportado).")
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
                return HttpResponse("Documento Confidencial")
        with open(file_path, 'rb') as file:
            response = get_response(file, path)
            if not response:
                return HttpResponse("Erro ao carregar arquivo (formato não suportado).")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

####### FIM DA PARTE DE I/O  #########

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_lista(request, periodo):
    """Lista todos os projetos."""
    configuracao = Configuracao.objects.all().first()
    projetos = Projeto.objects.all().order_by("ano", "semestre")
    if periodo == "antigos":
        if configuracao.semestre == 1:
            projetos = projetos.filter(ano__lt=configuracao.ano)
        else:
            projetos = projetos.filter(ano__lte=configuracao.ano).\
                                       exclude(ano=configuracao.ano, semestre=2)
    elif periodo == "atuais":
        projetos = projetos.filter(ano=configuracao.ano, semestre=configuracao.semestre)
    elif periodo == "disponiveis":
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
    if user.tipo_de_usuario != 1 and user.tipo_de_usuario != 2:
        return HttpResponse("Você não está cadastrado como aluno ou professor")
    elif user.tipo_de_usuario == 2:
        return redirect('professor_detail', pk=request.user.pk)
    # vvvv Caso seja um aluno  vvv
    aluno = Aluno.objects.get(pk=request.user.pk)
    context = {
        'aluno': aluno,
    }
    return render(request, 'projetos/meuprojeto_aluno.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def professores_tabela(request):
    """Professores."""
    configuracao = Configuracao.objects.all().first()

    professores_pfe = []
    periodo = []

    ano = 2018
    semestre = 2
    while True:
        professores = []
        grupos = []
        for professor in Professor.objects.all().order_by("user__first_name", "user__last_name"):
            count_grupos = 0
            grupos_pfe = Projeto.objects.filter(orientador=professor).\
                                        filter(ano=ano).\
                                        filter(semestre=semestre)
            if grupos_pfe: #len(grupos_pfe) > 0
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe: #len(alunos_pfe) > 0
                        count_grupos += 1
                if count_grupos > 0:
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

    anos = zip(professores_pfe, periodo)
    context = {
        'anos': anos,
    }
    return render(request, 'projetos/professores_tabela.html', context)

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
    encontros = Encontro.objects.all()
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
            return HttpResponse("Agendado: "+agendado)
        else:
            return HttpResponse("Problema!")
    else:
        context = {
            'encontros': encontros,
            'projeto': projeto,
        }
        return render(request, 'projetos/encontros.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def dinamicas(request):
    """Mostra os horários de dinâmicas."""
    configuracao = Configuracao.objects.all().first()
    encontros = Encontro.objects.all()

    context = {
        'encontros': encontros,
        'configuracao' : configuracao,
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
    return HttpResponse("Bancos carregados")

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
        bancos = Banco.objects.all().order_by("nome", "codigo")
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
    avisos = Aviso.objects.all().order_by("delta")
    dias_passados = (datetime.date.today() - configuracao.t0).days
    context = {
        'avisos': avisos,
        'configuracao' : configuracao,
        'dias_passados' : dias_passados,
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
    while True:
        semestres.append(str(ano)+"."+str(semestre))

        # Codigo abaixo é impreciso pois so pega pela ultima definição do ano,semestre do aluno
        alunos = Aluno.objects.filter(trancado=False).\
                               filter(anoPFE=ano).\
                               filter(semestrePFE=semestre).\
                               filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0]).\
                               order_by("user__first_name")

        projetos = []
        for projeto in Projeto.objects.filter(ano=ano).filter(semestre=semestre):
            if Aluno.objects.filter(alocacao__projeto=projeto): #checa se tem alunos
                projetos.append(projeto)

        organizacoes = []
        for projeto in projetos:
            if projeto.empresa not in organizacoes:
                organizacoes.append(projeto.empresa)

        orientadores = []
        for projeto in projetos:
            if projeto.orientador not in orientadores:
                orientadores.append(projeto.orientador)

        #parceiros = []
        parceiros = Parceiro.objects.filter(organizacao__in=organizacoes)

        alunos_p_semestre.append(alunos)
        orientadores_p_semestre.append(orientadores)
        parceiros_p_semestre.append(parceiros)

        if ano == configuracao.ano and semestre == configuracao.semestre:
            break
        if semestre == 1:
            semestre = 2
        else:
            ano += 1
            semestre = 1
    mylist = zip(semestres, alunos_p_semestre, orientadores_p_semestre, parceiros_p_semestre)

    membros_comite = PFEUser.objects.all().filter(membro_comite=True)

    todos_alunos = Aluno.objects.filter(trancado=False).\
                                 filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

    todos_professores = Professor.objects.all()
    todos_parceiros = Parceiro.objects.all()

    context = {
        'mylist' : mylist,
        'membros_comite' : membros_comite,
        'todos_alunos' : todos_alunos,
        'todos_professores' : todos_professores,
        'todos_parceiros' : todos_parceiros,
    }
    return render(request, 'projetos/emails.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_lista(request, periodo):
    """Lista todas as bancas agendadas, conforme periodo pedido."""
    #configuracao = Configuracao.objects.all().first()
    todas_bancas = Banca.objects.all().order_by("startDate")
    if periodo == "futuras":
        hoje = datetime.date.today()
        bancas = todas_bancas.filter(startDate__gt=hoje)
    else:
        bancas = todas_bancas
    context = {
        'bancas' : bancas,
    }
    return render(request, 'projetos/bancas_lista.html', context)

def editar_banca(banca, request):
    """Edita os valores de uma banca por um request Http."""
    if 'inicio' in request.POST:
        banca.startDate = dateutil.parser.parse(request.POST['inicio'])
    if 'fim' in request.POST:
        banca.endDate = dateutil.parser.parse(request.POST['fim'])
    if 'local' in request.POST:
        banca.location = request.POST['local']
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
        projeto = Projeto.objects.get(id=int(request.POST['projeto']))
        banca = Banca.create(projeto)
        editar_banca(banca, request)
        return HttpResponse("Banca criada.")
    else:
        if configuracao.semestre == 1:
            ano = configuracao.ano-1
            semestre = 2
        else:
            ano = configuracao.ano
            semestre = 1
        projetos = Projeto.objects.filter(ano=ano).filter(semestre=semestre).\
                                                   filter(disponivel=True).\
                                                   exclude(orientador=None)
        pessoas = PFEUser.objects.all().\
                                  filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0]).\
                                  order_by("first_name", "last_name") # Conta soh professor

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
        bancas = Banca.objects.all().order_by("startDate")
        context = {
            'bancas' : bancas,
        }
        return render(request, 'projetos/bancas_buscar.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_editar(request, primarykey):
    """Edita uma banca de avaliação para o projeto."""
    configuracao = Configuracao.objects.all().first()
    banca = Banca.objects.get(pk=primarykey)
    if request.method == 'POST':
        editar_banca(banca, request)
        return HttpResponse("Banca editada.")
    else:
        if configuracao.semestre == 1:
            ano = configuracao.ano-1
            semestre = 2
        else:
            ano = configuracao.ano
            semestre = 1
        projetos = Projeto.objects.filter(ano=ano).filter(semestre=semestre).\
                                                   filter(disponivel=True).\
                                                   exclude(orientador=None)
        pessoas = PFEUser.objects.all().\
                                  filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0]).\
                                  order_by("first_name", "last_name") # Conta soh professor
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
    professores = Professor.objects.all().filter(user__membro_comite=True)
    context = {
        'professores': professores,
        }
    return render(request, 'projetos/todos_professores.html', context)

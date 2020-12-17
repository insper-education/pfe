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
from urllib.parse import quote, unquote
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
from django.http import Http404, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.utils import html, text

from users.models import PFEUser, Aluno, Professor, Parceiro, Administrador, Opcao, Alocacao

from users.support import configuracao_estudante_vencida, get_edicoes, adianta_semestre

from .models import Projeto, Proposta, Organizacao, Configuracao, Evento, Anotacao, Coorientador
from .models import Feedback, Certificado, Entidade
from .models import Banca, Documento, Encontro, Banco, Reembolso, Aviso, Conexao
from .models import ObjetivosDeAprendizagem, Avaliacao2, Observacao, Area, AreaDeInteresse

from .models import get_upload_path

from .resources import ProjetosResource, OrganizacoesResource, OpcoesResource, UsuariosResource
from .resources import EstudantesResource, ProfessoresResource
from .resources import ParceirosResource, Avaliacoes2Resource
from .resources import ConfiguracaoResource, FeedbacksResource, DisciplinasResource

from .messages import email, message_reembolso

from .support import converte_conceito, converte_letra, cria_area_estudante
from .support import get_areas_estudantes, get_areas_propostas, get_peso

@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if configuracao and configuracao.manutencao:
        return render(request, 'projetos/manutencao.html')
    #num_visits = request.session.get('num_visits', 0) # Numero de visitas a página.
    #request.session['num_visits'] = num_visits + 1

    context = {
        'configuracao': configuracao,
    }

    #'num_visits': num_visits,
    return render(request, 'index.html', context=context)


@login_required
def index_projetos(request):
    """Página principal dos Projetos."""

    ## DEIXANDO TEMPORARIAMENTE POR PROBLEMAS DE CACHE DE BROWSERS

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if configuracao and configuracao.manutencao:
        return render(request, 'projetos/manutencao.html')
    #num_visits = request.session.get('num_visits', 0) # Numero de visitas a página.
    #request.session['num_visits'] = num_visits + 1

    context = {
        'configuracao': configuracao,
    }

    #'num_visits': num_visits,
    return render(request, 'index.html', context=context)


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
def projeto_detalhes(request, primarykey):
    """Exibe uma proposta de projeto com seus detalhes para o estudante aplicar."""

    try:
        projeto = Projeto.objects.get(pk=primarykey)
    except Projeto.DoesNotExist:
        return HttpResponse("Projeto não encontrado.", status=401)

    context = {
        'projeto': projeto,
        'MEDIA_URL' : settings.MEDIA_URL,
    }
    return render(request, 'projetos/projeto_detalhes.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def resultado_avaliacoes(request):
    """Mostra os resultados das avaliações (Bancas)."""

    edicoes, ano, semestre = get_edicoes(Projeto)

    if request.is_ajax():
        if 'edicao' in request.POST:
            ano, semestre = request.POST['edicao'].split('.')
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

    banca_intermediaria = []
    banca_final = []
    banca_falconi = []

    for projeto in projetos:
        aval_banc_final = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=2) #B. Final
        nota_banca_final, peso = Aluno.get_banca(None, aval_banc_final)
        if peso is not None:
            banca_final.append(("{0}".format(converte_letra(nota_banca_final, espaco="&nbsp;")),
                                "{0:5.2f}".format(nota_banca_final)))
        else:
            banca_final.append( ("&nbsp;-&nbsp;",None) )

        aval_banc_interm = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=1) #B. Int.
        nota_banca_intermediaria, peso = Aluno.get_banca(None, aval_banc_interm)
        if peso is not None:
            banca_intermediaria.append(("{0}".format(converte_letra(nota_banca_intermediaria,
                                                                    espaco="&nbsp;")),
                                        "{0:5.2f}".format(nota_banca_intermediaria)))
        else:
            banca_intermediaria.append( ("&nbsp;-&nbsp;",None) )

        aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=99) #Falc.
        nota_banca_falconi, peso = Aluno.get_banca(None, aval_banc_falconi)
        if peso is not None:
            banca_falconi.append(("{0}".format(converte_letra(nota_banca_falconi, espaco="&nbsp;")),
                                  "{0:5.2f}".format(nota_banca_falconi)))
        else:
            banca_falconi.append( ("&nbsp;-&nbsp;", None) )


    tabela = zip(projetos, banca_intermediaria, banca_final, banca_falconi)

    context = {
        'tabela': tabela,
        "edicoes": edicoes,
    }

    return render(request, 'projetos/resultado_avaliacoes.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def propor(request):
    """Monta grupos de PFE."""
    # Deprecated
    return HttpResponseNotFound('<h1>Sistema de propor projetos está obsoleto.</h1>')


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def montar_grupos(request):
    """Montar grupos para projetos."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    ano, semestre = adianta_semestre(ano, semestre)

    propostas = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)

    alunos_se_inscrevendo = Aluno.objects.filter(trancado=False).\
                                      filter(anoPFE=ano, semestrePFE=semestre).\
                                      order_by(Lower("user__first_name"), Lower("user__last_name"))

    # Conta soh alunos
    estudantes = alunos_se_inscrevendo.filter(user__tipo_de_usuario=\
                                          PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

    opcoes = []
    for estudante in estudantes:
        opcao = Opcao.objects.filter(aluno=estudante).\
                              filter(proposta__ano=ano, proposta__semestre=semestre).\
                              order_by("prioridade")
        opcoes.append(opcao)
    estudantes_opcoes = zip(estudantes, opcoes)

    # Checa se usuário é administrador ou professor
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    mensagem = ""

    if request.method == 'POST':

        if user:
            if user.tipo_de_usuario == 4: # admin

                if 'limpar' in request.POST:
                    for estudante in estudantes:
                        estudante.pre_alocacao = None
                        estudante.save()

                if 'fechar' in request.POST:
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
                        if alocados: # pelo menos um estudante no projeto

                            try:
                                projeto = Projeto.objects.get(proposta=proposta, avancado=False)
                            except Projeto.DoesNotExist:
                                projeto = Projeto.create(proposta)

                            if not projeto.titulo:
                                projeto.titulo = proposta.titulo

                            if not projeto.descricao:
                                projeto.descricao = proposta.descricao

                            if not projeto.organizacao:
                                projeto.organizacao = proposta.organizacao

                            projeto.avancado = False

                            projeto.ano = proposta.ano
                            projeto.semestre = proposta.semestre

                            projeto.save()

                            alocacoes = Alocacao.objects.filter(projeto=projeto)
                            for alocacao in alocacoes: # Apaga todas alocacoes que não tiverem nota
                                avals = list(Avaliacao2.objects.filter(alocacao=alocacao))
                                if not avals:
                                    alocacao.delete()
                                else:
                                    mensagem += "- "+str(alocacao.aluno)+"\n"

                            for alocado in alocados: # alocando estudantes no projeto
                                alocacao = Alocacao.create(alocado, projeto)
                                alocacao.save()

                        else:

                            try:
                                projeto = Projeto.objects.get(proposta=proposta, avancado=False)
                            except Projeto.DoesNotExist:
                                continue

                            projeto.delete()

                    if mensagem:
                        request.session['mensagem'] = 'Estudantes possuiam alocações com notas:\n'
                        request.session['mensagem'] += mensagem

                    return redirect('/projetos/selecionar_orientadores/')

    if user:
        if user.tipo_de_usuario != 4: # admin
            mensagem = "Sua conta não é de administrador, "
            mensagem += "você pode mexer na tela, contudo suas modificações não serão salvas."

    context = {
        'mensagem': mensagem,
        'configuracao': configuracao,
        'propostas': propostas,
        'estudantes_opcoes': estudantes_opcoes,
    }
    return render(request, 'projetos/montar_grupos.html', context=context)

@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def selecionar_orientadores(request):
    """Selecionar Orientadores para os Projetos."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    mensagem = ""

    if 'mensagem' in request.session:
        mensagem = request.session['mensagem']

    # Vai para próximo semestre
    ano, semestre = adianta_semestre(ano, semestre)

    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

    professores = PFEUser.objects.\
                        filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0])

    administradores = PFEUser.objects.\
                        filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[3][0])

    orientadores = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    # Checa se usuário é administrador ou professor
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user:
        if user.tipo_de_usuario != 4: # admin
            mensagem = "Sua conta não é de administrador, "
            mensagem += "você pode mexer na tela, contudo suas modificações não serão salvas."

    context = {
        'mensagem': mensagem,
        'projetos': projetos,
        'orientadores': orientadores,
    }
    return render(request, 'projetos/selecionar_orientadores.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def projeto_completo(request, primakey):
    """Mostra um projeto por completo."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    try:
        projeto = Projeto.objects.get(pk=primakey)
    except Projeto.DoesNotExist:
        return HttpResponse("Projeto não encontrado.", status=401)

    opcoes = Opcao.objects.filter(proposta=projeto.proposta)
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
def distribuicao_areas(request):
    """Mostra distribuição por área de interesse dos alunos, propostas e projetos."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano              # Ano atual
        semestre = configuracao.semestre    # Semestre atual
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    todas = False                       # Para mostrar todos os dados de todos os anos e semestres
    tipo = "estudantes"
    curso = "todos"

    if request.is_ajax():

        if 'tipo' in request.POST and 'edicao' in request.POST:

            tipo = request.POST['tipo']

            if request.POST['edicao'] == 'todas':
                todas = True
            else:
                periodo = request.POST['edicao'].split('.')
                ano = int(periodo[0])
                semestre =int(periodo[1])

            if tipo == "estudantes" and 'curso' in request.POST:
                curso = request.POST['curso']

        else:
            return HttpResponse("Algum erro não identificado (POST incompleto).", status=401)

    if tipo == "estudantes":
        alunos = Aluno.objects.filter(user__tipo_de_usuario=1)
        if curso != "todos":
            alunos = alunos.filter(curso=curso)
        if not todas:
            alunos = alunos.filter(anoPFE=ano, semestrePFE=semestre)
        total_preenchido = 0
        for aluno in alunos:
            if AreaDeInteresse.objects.filter(usuario=aluno.user).count() > 0:
                total_preenchido += 1
        context = {
            'total': alunos.count(),
            'total_preenchido': total_preenchido,
            'areaspfe': get_areas_estudantes(alunos),
        }

    elif tipo == "propostas":
        propostas = Proposta.objects.all()
        if not todas:
            propostas = propostas.filter(ano=ano, semestre=semestre)
        context = {
            'total': propostas.count(),
            'areaspfe': get_areas_propostas(propostas),
        }

    elif tipo == "projetos":

        projetos = Projeto.objects.all()
        if not todas:
            projetos = projetos.filter(ano=ano, semestre=semestre)

        # Estudar forma melhor de fazer isso
        propostas = [p.proposta.id for p in projetos]
        propostas_projetos = Proposta.objects.filter(id__in=propostas)

        context = {
            'total': propostas_projetos.count(),
            'areaspfe': get_areas_propostas(propostas_projetos),
        }

    else:
        return HttpResponse("Algum erro não identificado (não encontrado tipo).", status=401)

    context['tipo'] = tipo
    context['periodo'] = str(ano)+"."+str(semestre)
    context['ano'] = ano
    context['semestre'] = semestre
    context['loop_anos'] = range(2018, ano+1)

    return render(request, 'projetos/distribuicao_areas.html', context)


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

            try:
                anotacao.autor = PFEUser.objects.get(pk=request.user.pk)
            except Configuracao.DoesNotExist:
                return HttpResponse("Usuário não encontrado.", status=401)

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
            "organizacoes_prospectadas": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)
    else:
        context = {
            'organizacao': organizacao,
            'TIPO_DE_RETORNO': Anotacao.TIPO_DE_RETORNO,
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
        resource = EstudantesResource()
    elif modelo == "professores":
        resource = ProfessoresResource()
    elif modelo == "parceiros":
        resource = ParceirosResource()
    elif modelo == "configuracao":
        resource = ConfiguracaoResource()
    elif modelo == "feedbacks":
        resource = FeedbacksResource()
    else:
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

    data_alunos = EstudantesResource().export()
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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        configuracao.manutencao = 'manutencao' in check_values
        configuracao.save()
        return redirect('/projetos/administracao/')

    context = {'manutencao': configuracao.manutencao,}

    return render(request, 'projetos/servico.html', context)


def render_to_pdf(template_src, context_dict=None):
    """Renderiza um documento em PDF."""

    template = get_template(template_src)
    html_doc = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_doc.encode("utf-8")), result)
    if not pdf.err:
        return result

    return None

def get_calendario_context(primarykey):
    """Contexto para gerar calendário."""

    try:
        user = PFEUser.objects.get(pk=primarykey)
    except PFEUser.DoesNotExist:
        return None

    eventos = Evento.objects.all()

    # Estudantes e parceiros não conseguem ver o calendário no futuro

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4: # Professor e Admin
        eventos = eventos.filter(startDate__year__lte=configuracao.ano)
        if configuracao.semestre == 1:
            eventos = eventos.filter(startDate__month__lte=7)

    eventos_gerais = eventos.exclude(tipo_de_evento=12).\
                             exclude(tipo_de_evento=40).\
                             exclude(tipo_de_evento=41).\
                             exclude(tipo_de_evento=20).\
                             exclude(tipo_de_evento=30).\
                             exclude(tipo_de_evento__gte=100)
    aulas = eventos.filter(tipo_de_evento=12) #12, 'Aula PFE'
    laboratorios = eventos.filter(tipo_de_evento=40) #40, 'Laboratório'
    provas = eventos.filter(tipo_de_evento=41) #41, 'Semana de Provas'
    quinzenais = eventos.filter(tipo_de_evento=20) #20, 'Relato Quinzenal'
    feedbacks = eventos.filter(tipo_de_evento=30) #30, 'Feedback dos Alunos sobre PFE'
    coordenacao = Evento.objects.filter(tipo_de_evento__gte=100) # Eventos da coordenação

    # ISSO NAO ESTA BOM, FAZER ALGO MELHOR

    # TAMBÉM ESTOU USANDO NO CELERY PARA AVISAR DOS EVENTOS

    context = {
        'eventos': eventos_gerais,
        'aulas': aulas,
        'laboratorios': laboratorios,
        'provas' : provas,
        'quinzenais' : quinzenais,
        'feedbacks' : feedbacks,
        'coordenacao' : coordenacao,
        'semestre' : configuracao.semestre,
    }

    return context


@login_required
def calendario(request):
    """Para exibir um calendário de eventos."""
    context = get_calendario_context(request.user.pk)
    if context:
        return render(request, 'projetos/calendario.html', context)
    else:
        HttpResponse("Problema ao gerar calendário.", status=401)


@login_required
def calendario_limpo(request):
    """Para exibir um calendário de eventos."""

    context = get_calendario_context(request.user.pk)
    if context:
        context['limpo'] = True
        return render(request, 'projetos/calendario.html', context)
    else:
        HttpResponse("Problema ao gerar calendário.", status=401)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio(request, modelo, formato):
    """Gera relatorios em html e PDF."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
        context = get_calendario_context(request.user.pk)
        arquivo = "projetos/calendario.html"

    else:
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

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def relatorio_backup(request):
    """Gera um relatório de backup de segurança."""

    subject = 'RELATÓRIOS PFE'
    message = "Relatórios PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com', 'lpsoares@gmail.com',]
    mail = EmailMessage(subject, message, email_from, recipient_list)

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    mensagem = "E-mail enviado."
    context = {
        "area_principal": True,
        "mensagem": mensagem,
    }
    return render(request, 'generic.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_fechados(request):
    """Lista todos os projetos fechados."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    edicoes = []

    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            if edicao == 'todas':
                projetos_filtrados = Projeto.objects.all()
            else:
                ano, semestre = request.POST['edicao'].split('.')
                projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Projeto)
        projetos_filtrados = Projeto.objects.filter(ano=ano, semestre=semestre)

    projetos_selecionados = []
    prioridade_list = []
    conexoes = []
    numero_estudantes = 0

    for projeto in projetos_filtrados:
        estudantes_pfe = Aluno.objects.filter(alocacao__projeto=projeto)
        if estudantes_pfe: #len(estudantes_pfe) > 0:
            projetos_selecionados.append(projeto)
            numero_estudantes += len(estudantes_pfe)
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
            prioridade_list.append(zip(estudantes_pfe, prioridades))
            conexoes.append(Conexao.objects.filter(projeto=projeto, colaboracao=True))

    projetos = zip(projetos_selecionados, prioridade_list, conexoes)

    context = {
        'projetos': projetos,
        'numero_projetos': len(projetos_selecionados),
        'numero_estudantes': numero_estudantes,
        'edicoes': edicoes,
    }
    return render(request, 'projetos/projetos_fechados.html', context)


@login_required
def submissao(request):
    """Para perguntas descritivas ao aluno de onde trabalho, entidades, sociais e familia."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user.tipo_de_usuario == 3:
        mensagem = "Você não está cadastrado como aluno!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    if user.tipo_de_usuario == 1:

        try:
            estudante = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Estudante não encontrado.", status=401)

        vencido = configuracao_estudante_vencida(estudante)

        if (not vencido) and request.method == 'POST':

            estudante.trabalhou = request.POST.get("trabalhou", None)
            estudante.social = request.POST.get("social", None)
            estudante.entidade = request.POST.get("entidade", None)
            estudante.familia = request.POST.get("familia", None)

            estudante.user.linkedin = request.POST.get("linkedin", None)
            estudante.user.save()

            estudante.save()
            return render(request, 'users/atualizado.html',)

        context = {
            'vencido': vencido,
            'trabalhou' : estudante.trabalhou,
            'social' : estudante.social,
            'entidade' : estudante.entidade,
            'familia' : estudante.familia,
            'linkedin' : estudante.user.linkedin,
            'entidades' : Entidade.objects.all(),
        }
    else: # Supostamente professores
        context = {
            'mensagem': "Você não está cadastrado como estudante.",
            'vencido': True,
            'trabalhou': "",
            'social': "",
            'entidade': "",
            'familia': "",
            'linkedin': user.linkedin,
            'entidades': Entidade.objects.all(),
        }
    return render(request, 'projetos/submissao.html', context)


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
    elif dado == "alunos":
        resource = EstudantesResource()
    elif dado == "avaliacoes":
        resource = Avaliacoes2Resource()
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


def carrega_arquivo(request, local_path, path):
    """Carrega arquivos pela URL."""
    file_path = os.path.abspath(local_path)
    if ".." in file_path:
        raise PermissionDenied
    if "\\" in file_path:
        raise PermissionDenied
    if os.path.exists(file_path):
        doc = Documento.objects.filter(documento=local_path[len(settings.BASE_DIR)+\
                                                            len(settings.MEDIA_URL):]).last()
        if doc:

            try:
                user = PFEUser.objects.get(pk=request.user.pk)
            except PFEUser.DoesNotExist:
                return HttpResponse("Usuário não encontrado.", status=401)

            if (doc.tipo_de_documento < 6) and (user.tipo_de_usuario != 2):
                mensagem = "Documento Confidencial"
                context = {
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)

        with open(file_path, 'rb') as file:
            response = get_response(file, path)
            if not response:
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
def arquivos(request, documentos, path):
    """Permite acessar arquivos do servidor."""

    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}".\
        format(documentos, path))

    return carrega_arquivo(request, local_path, path)


@login_required
def arquivos2(request, organizacao, usuario, path):
    """Permite acessar arquivos do servidor."""

    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}".\
        format(organizacao, usuario, path))

    return carrega_arquivo(request, local_path, path)


@login_required
def arquivos3(request, organizacao, projeto, usuario, path):
    """Permite acessar arquivos do servidor."""

    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}/{3}".\
        format(organizacao, projeto, usuario, path))

    return carrega_arquivo(request, local_path, path)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def projetos_lista(request, periodo):
    """Lista todos os projetos."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user:
        if user.tipo_de_usuario != 4: # não é admin
            mensagem = "Você não tem privilégios de administrador!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

    return render(request, 'projetos/carregar.html')

@login_required
def meuprojeto(request):
    """Mostra o projeto do próprio aluno, se for aluno."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    # Caso não seja Aluno, Professor ou Administrador (ou seja Parceiro)
    if user.tipo_de_usuario != 1 and user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
        mensagem = "Você não está cadastrado como aluno ou professor!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    # Caso seja Professor ou Administrador
    if user.tipo_de_usuario == 2 or user.tipo_de_usuario == 4:

        try:
            professor = Professor.objects.get(pk=request.user.professor.pk)
        except Professor.DoesNotExist:
            return HttpResponse("Professor não encontrado.", status=401)

        return redirect('professor_detail', primarykey=professor.pk)

    # vvvv Caso seja um aluno  vvv
    try:
        aluno = Aluno.objects.get(pk=request.user.aluno.pk)
    except Aluno.DoesNotExist:
        return HttpResponse("Estudante não encontrado.", status=401)

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    context = {
        'aluno': aluno,
        'configuracao' : configuracao,
    }
    return render(request, 'projetos/meuprojeto_aluno.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_tabela(request):
    """Lista todas as bancas agendadas, conforme periodo pedido."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    dias_bancas_interm = Evento.objects.filter(tipo_de_evento=14) # (14, 'Banca intermediária'
    dias_bancas_finais = Evento.objects.filter(tipo_de_evento=15) # (15, 'Bancas finais'
    dias_bancas_falcon = Evento.objects.filter(tipo_de_evento=50) # (50, 'Certificação Falconi'

    dias_bancas = (dias_bancas_interm | dias_bancas_finais | dias_bancas_falcon)

    context = {
        'bancas': bancas,
        'dias_bancas': dias_bancas,
    }
    return render(request, 'projetos/bancas_index.html', context)


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


@login_required
@transaction.atomic
def reembolso_pedir(request):
    """Página com sistema de pedido de reembolso."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    try:
        usuario = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)
    if usuario.tipo_de_usuario == 1:
        try:
            aluno = Aluno.objects.get(pk=request.user.aluno.pk)
        except Aluno.DoesNotExist:
            return HttpResponse("Aluno não encontrado.", status=401)

        if not configuracao.liberados_projetos:
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

        try:
            reembolso.banco = Banco.objects.get(codigo=request.POST['banco'])
        except Banco.DoesNotExist:
            return HttpResponse("Banco não encontrado.", status=401)

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
        message = message_reembolso(usuario, projeto, reembolso, cpf)
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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    qualquer_aviso = list(Aviso.objects.all())

    eventos = Evento.objects.filter(startDate__year=configuracao.ano)
    if configuracao.semestre == 1:
        qualquer_evento = list(eventos.filter(startDate__month__lt=7))
    else:
        qualquer_evento = list(eventos.filter(startDate__month__gt=6))

    avisos = sorted(qualquer_aviso+qualquer_evento, key=lambda t: t.get_data())

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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
        membros_bancas = [] # Membros das bancas

        for projeto in Projeto.objects.filter(ano=ano).filter(semestre=semestre):
            if Aluno.objects.filter(alocacao__projeto=projeto): #checa se tem alunos
                alunos_tmp = Aluno.objects.filter(trancado=False).\
                              filter(alocacao__projeto=projeto).\
                              filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
                alunos_semestre += list(alunos_tmp)
                orientador = projeto.orientador
                conexoes = Conexao.objects.filter(projeto=projeto)

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
                projetos_pessoas[projeto]["conexoes"] = list(conexoes) # Todos conectados ao projeto

        # Parceiros de todas as organizações parceiras
        parceiros_semestre = Parceiro.objects.filter(organizacao__in=organizacoes,
                                                     user__is_active=True)

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

        if ano > configuracao.ano and semestre == configuracao.semestre:
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

    membros_comite = PFEUser.objects.filter(membro_comite=True)

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
def bancas_lista(request, periodo_projeto):
    """Lista as bancas agendadas, conforme periodo ou projeto pedido."""

    projeto = None

    if periodo_projeto == "proximas":
        hoje = datetime.date.today()
        bancas = Banca.objects.filter(startDate__gt=hoje).order_by("startDate")
    elif periodo_projeto == "todas":
        bancas = Banca.objects.all().order_by("startDate")
    else:
        try:
            projeto = Projeto.objects.get(id=periodo_projeto)
        except Projeto.DoesNotExist:
            return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')
        bancas = Banca.objects.filter(projeto=projeto).order_by("startDate")

    context = {
        'bancas' : bancas,
        'periodo' : periodo_projeto,
        "projeto" : projeto,
    }
    return render(request, 'projetos/bancas_lista.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def banca_ver(request, primarykey):
    """Retorna banca pedida."""

    try:
        banca = Banca.objects.get(id=primarykey)
    except Banca.DoesNotExist:
        return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    context = {
        'banca' : banca,
    }
    return render(request, 'projetos/banca_ver.html', context)


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

    try:
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
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    banca.save()

def professores_membros_bancas():
    """Retorna potenciais usuários que podem ser membros de uma banca do PFE."""
    professores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[1][0])

    administradores = PFEUser.objects.filter(tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[3][0])

    pessoas = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    return pessoas


def falconi_membros_banca():
    """Coleta registros de possiveis membros de banca para Falconi."""

    try:
        organizacao = Organizacao.objects.get(sigla="Falconi")
    except Organizacao.DoesNotExist:
        return HttpResponse("Organização não encontrada.", status=401)

    falconis = PFEUser.objects.filter(parceiro__organizacao=organizacao)
    return falconis


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_criar(request):
    """Cria uma banca de avaliação para o projeto."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':
        if 'projeto' in request.POST:

            try:
                projeto = Projeto.objects.get(id=int(request.POST['projeto']))
            except Projeto.DoesNotExist:
                return HttpResponse("Projeto não encontrado.", status=401)

            banca = Banca.create(projeto)
            editar_banca(banca, request)
            mensagem = "Banca criada."
            context = {
                "area_principal": True,
                "bancas_index": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Banca não registrada, problema com identificação do projeto.")

    ano = configuracao.ano
    semestre = configuracao.semestre
    projetos = Projeto.objects.filter(ano=ano, semestre=semestre).\
                                        exclude(orientador=None)

    professores = professores_membros_bancas()
    falconis = falconi_membros_banca()

    context = {
        'projetos' : projetos,
        'professores' : professores,
        "TIPO_DE_BANCA": Banca.TIPO_DE_BANCA,
        "falconis": falconis,
    }
    return render(request, 'projetos/bancas_editar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def bancas_editar(request, primarykey):
    """Edita uma banca de avaliação para o projeto."""

    try:
        banca = Banca.objects.get(pk=primarykey)
    except Banca.DoesNotExist:
        return HttpResponse("Banca não encontrada.", status=401)

    if request.method == 'POST':
        editar_banca(banca, request)
        mensagem = "Banca editada."
        context = {
            "area_principal": True,
            "bancas_index": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    projetos = Projeto.objects.exclude(orientador=None).order_by("-ano", "-semestre")

    professores = professores_membros_bancas()
    falconis = falconi_membros_banca()

    context = {
        'projetos' : projetos,
        'professores' : professores,
        'banca' : banca,
        "TIPO_DE_BANCA": Banca.TIPO_DE_BANCA,
        "falconis": falconis,
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

    return render(request, 'projetos/comite_pfe.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def export_calendar(request, event_id):
    """Gera evento de calendário."""

    try:
        banca = Banca.objects.all().get(pk=event_id)
    except Banca.DoesNotExist:
        return HttpResponse("Banca não encontrada.", status=401)

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


#@login_required
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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
        'feedbacks' : feedbacks,
        'SERVER_URL' : settings.SERVER,
        'loop_anos': edicoes,
        'num_projetos': num_projetos,
        'num_feedbacks': num_feedbacks,
    }
    return render(request, 'projetos/lista_feedback.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""

    try:
        feedback = Feedback.objects.get(id=feedback_id)
    except Feedback.DoesNotExist:
        return HttpResponse("Feedback não encontrado.", status=401)

    context = {
        'feedback' : feedback,
    }

    return render(request, 'projetos/mostra_feedback.html', context)


#@login_required
#@permission_required("users.altera_professor", login_url='/projetos/')
def banca_avaliar(request, slug):
    """Cria uma tela para preencher avaliações de bancas."""

    try:
        banca = Banca.objects.get(slug=slug)

        if banca.endDate.date() + datetime.timedelta(days=5) < datetime.date.today():
            mensagem = "Prazo para submissão da Avaliação de Banca vencido.<br>"
            mensagem += "Entre em contato com a coordenação do PFE para enviar sua avaliação.<br>"
            mensagem += "Luciano Pereira Soares <a href='mailto:lpsoares@insper.edu.br'>lpsoares@insper.edu.br</a>.<br>"
            return HttpResponse(mensagem)

        if not banca.projeto:
            return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

    except Banca.DoesNotExist:
        return HttpResponseNotFound('<h1>Banca não encontrada!</h1>')

    if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1: # Intermediária e Final
        objetivos = ObjetivosDeAprendizagem.objects.filter(avaliacao_banca=True).order_by("id")
    elif banca.tipo_de_banca == 2: # Falconi
        objetivos = ObjetivosDeAprendizagem.objects.filter(avaliacao_falconi=True).order_by("id")
    else:
        return HttpResponseNotFound('<h1>Tipo de Banca não indentificado!</h1>')

    if request.method == 'POST':
        if 'avaliador' in request.POST:

            try:
                avaliador = PFEUser.objects.get(pk=int(request.POST['avaliador']))
            except PFEUser.DoesNotExist:
                return HttpResponse("Usuário não encontrado.", status=401)

            if banca.tipo_de_banca == 1: #(1, 'intermediaria'),
                tipo_de_avaliacao = 1 #( 1, 'Banca Intermediária'),
            elif banca.tipo_de_banca == 0: # (0, 'final'),
                tipo_de_avaliacao = 2 #( 2, 'Banca Final'),
            elif banca.tipo_de_banca == 2: # (2, 'falconi'),
                tipo_de_avaliacao = 99 # (99, 'Falconi'),

            # Identifica que uma avaliação já foi realizada anteriormente
            realizada = Avaliacao2.objects.filter(projeto=banca.projeto,
                                                  avaliador=avaliador,
                                                  tipo_de_avaliacao=tipo_de_avaliacao).\
                                           exists()

            objetivos_possiveis = 5
            julgamento = [None]*objetivos_possiveis
            for i in range(objetivos_possiveis):
                if 'objetivo.{0}'.format(i+1) in request.POST:
                    obj_nota = request.POST['objetivo.{0}'.format(i+1)]
                    conceito = obj_nota.split('.')[1]
                    julgamento[i] = Avaliacao2.create(projeto=banca.projeto)
                    julgamento[i].avaliador = avaliador

                    try:
                        pk_objetivo = int(obj_nota.split('.')[0])
                        julgamento[i].objetivo = ObjetivosDeAprendizagem.objects.get(pk=pk_objetivo)
                    except ObjetivosDeAprendizagem.DoesNotExist:
                        return HttpResponse("Objetivo de Aprendizagem não encontrados.", status=401)

                    julgamento[i].tipo_de_avaliacao = tipo_de_avaliacao
                    if conceito == "NA":
                        julgamento[i].na = True
                    else:
                        julgamento[i].nota = converte_conceito(conceito)
                        julgamento[i].peso = get_peso(tipo_de_avaliacao, julgamento[i].objetivo)
                        julgamento[i].na = False
                    julgamento[i].save()

            julgamento_observacoes = None
            if 'observacoes' in request.POST and request.POST['observacoes'] != "":
                julgamento_observacoes = Observacao.create(projeto=banca.projeto)
                julgamento_observacoes.avaliador = avaliador
                julgamento_observacoes.observacoes = request.POST['observacoes']
                julgamento_observacoes.tipo_de_avaliacao = tipo_de_avaliacao
                julgamento_observacoes.save()

            message = "<h3>Avaliação PFE</h3><br>\n"

            if realizada:
                message += "<h3 style='color:red;text-align:center;'>"
                message += "Essa é uma atualização de uma avaliação já enviada anteriormente!"
                message += "</h3><br><br>"

            message += "<b>Título do Projeto:</b> {0}<br>\n".format(banca.projeto.get_titulo())
            message += "<b>Organização:</b> {0}<br>\n".format(banca.projeto.organizacao)
            message += "<b>Orientador:</b> {0}<br>\n".format(banca.projeto.orientador)
            message += "<b>Avaliador:</b> {0}<br>\n".format(avaliador.get_full_name())
            message += "<b>Data:</b> {0}<br>\n".format(banca.startDate.strftime("%d/%m/%Y %H:%M"))

            message += "<b>Banca:</b> "
            tipos = dict(Banca.TIPO_DE_BANCA)
            if banca.tipo_de_banca in tipos:
                message += tipos[banca.tipo_de_banca]
            else:
                message += "Tipo de banca não definido"

            message += "<br>\n<br>\n"
            message += "<b>Conceitos:</b><br>\n"
            message += "<table style='border: 1px solid black; "
            message += "border-collapse:collapse; padding: 0.3em;'>"
            if julgamento[0] and not julgamento[0].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[0].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[0].nota))
            if julgamento[1] and not julgamento[1].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[1].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[1].nota))
            if julgamento[2] and not julgamento[2].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[2].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[2].nota))
            if julgamento[3] and not julgamento[3].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[3].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[3].nota))
            if julgamento[4] and not julgamento[4].na:
                message += "<tr><td style='border: 1px solid black;'>{0}</td>".\
                    format(julgamento[4].objetivo)
                message += "<td style='border: 1px solid black; text-align:center'>"
                message += "&nbsp;{0}&nbsp;</td>\n".\
                    format(converte_letra(julgamento[4].nota))
            message += "</table>"

            message += "<br>\n<br>\n"

            if julgamento_observacoes:
                message += "<b>Observações:</b>\n"
                message += "<p style='border:1px; border-style:solid; padding: 0.3em; margin: 0;'>"
                message += html.escape(julgamento_observacoes.observacoes).replace('\n', '<br>\n')
                message += "</p>"
                message += "<br>\n<br>\n"


            # Criar link para reeditar
            message += "<a href='" + settings.SERVER + "/projetos/banca_avaliar/" + str(banca.slug)

            message += "?avaliador=" + str(avaliador.id)
            for count, julg in enumerate(julgamento):
                if julg and not julg.na:
                    message += "&objetivo" + str(count) + "=" + str(julg.objetivo.id)
                    message += "&conceito" + str(count) + "=" + converte_letra(julg.nota, mais="X")
            if julgamento_observacoes:
                message += "&observacoes=" + quote(julgamento_observacoes.observacoes)
            message += "'>"
            message += "Caso deseje reenviar sua avaliação, clique aqui."
            message += "</a><br>\n"
            message += "<br>\n"

            # Relistar os Objetivos de Aprendizagem
            message += "<br><b>Objetivos de Aprendizagem</b>"

            for julg in julgamento:

                if julg:

                    message += "<br><b>{0}</b>: {1}".format(julg.objetivo.titulo, julg.objetivo.objetivo)
                    message += "<table "
                    message += "style='border:1px solid black; border-collapse:collapse; width:100%;'>"
                    message += "<tr>"

                    if (not julg.na) and converte_letra(julg.nota) == "I":
                        message += "<td style='border: 2px solid black; width:18%;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black; width:18%;'>"
                    message += "Insatisfatório (I)</th>"

                    if (not julg.na) and converte_letra(julg.nota) == "D":
                        message += "<td style='border: 2px solid black; width:18%;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black; width:18%;'>"
                    message += "Em Desenvolvimento (D)</th>"

                    if (not julg.na) and ( converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+" ):
                        message += "<td style='border: 2px solid black; width:18%;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black; width:18%;'>"
                    message += "Essencial (C/C+)</th>"

                    if (not julg.na) and ( converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+" ):
                        message += "<td style='border: 2px solid black; width:18%;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black; width:18%;'>"
                    message += "Proficiente (B/B+)</th>"

                    if (not julg.na) and ( converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+" ):
                        message += "<td style='border: 2px solid black; width:18%;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black; width:18%;'>"
                    message += "Avançado (A/A+)</th>"

                    message += "</tr>"
                    message += "<tr>"

                    if (not julg.na) and converte_letra(julg.nota) == "I":
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_I)
                    message += "</td>"

                    if (not julg.na) and converte_letra(julg.nota) == "D":
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_D)
                    message += "</td>"

                    if (not julg.na) and ( converte_letra(julg.nota) == "C" or converte_letra(julg.nota) == "C+" ):
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_C)
                    message += "</td>"

                    if (not julg.na) and ( converte_letra(julg.nota) == "B" or converte_letra(julg.nota) == "B+" ):
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_B)
                    message += "</td>"

                    if (not julg.na) and ( converte_letra(julg.nota) == "A" or converte_letra(julg.nota) == "A+" ):
                        message += "<td style='border: 2px solid black;"
                        message += " background-color: #F4F4F4;'>"
                    else:
                        message += "<td style='border: 1px solid black;'>"
                    message += "{0}".format(julg.objetivo.rubrica_A)
                    message += "</td>"

                    message += "</tr>"
                    message += "</table>"

            subject = 'Banca PFE : {0}'.format(banca.projeto)

            recipient_list = [avaliador.email,]
            if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1: # Intermediária e Final
                recipient_list += [banca.projeto.orientador.user.email,]
            elif banca.tipo_de_banca == 2: # Falconi
                recipient_list += ["lpsoares@insper.edu.br",]

            check = email(subject, recipient_list, message)
            if check != 1:
                message = "Algum problema de conexão, contacte: lpsoares@insper.edu.br"

            resposta = "Avaliação submetida e enviada para:<br>"
            for recipient in recipient_list:
                resposta += "&bull; {0}<br>".format(recipient)
            if realizada:
                resposta += "<br><br><h2>Essa é uma atualização de uma avaliação já enviada anteriormente!</h2><br><br>"
            resposta += "<br><a href='javascript:history.back(1)'>Voltar</a>"
            context = {
                "area_principal": True,
                "mensagem": resposta,
            }
            return render(request, 'generic.html', context=context)

        return HttpResponse("Avaliação não submetida.")
    else:

        orientacoes = ""

        if banca.tipo_de_banca == 0 or banca.tipo_de_banca == 1: # Intermediária e Final
            pessoas = professores_membros_bancas()
            orientacoes += "O professor(a) orientador(a) é responsável por conduzir a banca. Os membros do grupo terão <b>40 minutos para a apresentação</b>. Os membros da banca terão depois <b>50 minutos para arguição</b> (que serão divididos pelos membros convidados), podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja muitas interferências da banca durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto. Um membro da banca pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar."
            orientacoes += "<br><br>"
            orientacoes += "Como ordem recomendada para a arguição da banca, se deve convidar: professores convidados, professores coorientadores, professor(a) orientador(a) do projeto e por fim demais pessoas assistindo à apresentação. A banca poderá perguntar tanto sobre a apresentação, como o relatório entregue, se espera coletar informações tanto da apresentação, como do relatório, permitindo uma clara ponderação nas rubricas dos objetivos de aprendizado do Projeto Final de Engenharia."
            orientacoes += "<br><br>"
            orientacoes += "As bancas do Projeto Final de Engenharia servem como mais um evidência de aprendizado, assim, além da percepção dos membros da banca em relação ao nível alcançado nos objetivos de aprendizado pelos membros do grupo, serve também como registro da evolução do projeto. Dessa forma, ao final, a banca terá mais <b>15 minutos para ponderar</b>, nesse momento se recomenda dispensar os estudantes e demais convidados externos. Recomendamos 5 minutos para os membros da banca relerem os objetivos de aprendizagem e rubricas, fazerem qualquer anotação e depois 10 minutos para uma discussão final. Cada membro da banca poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. O professor(a) orientador(a) irá publicar (no Blackboard), ao final, a média dos conceitos anotados."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper, se tem os professores automaticamente responsáveis por garantir o sigilo das informações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"

        elif banca.tipo_de_banca == 2: # Falconi
            pessoas = falconi_membros_banca()
            orientacoes += "Os membros do grupo terão <b>15 minutos para a apresentação</b>. Os consultores da Falconi terão depois outros <b>15 minutos para arguição e observações</b>, podendo tirar qualquer dúvida a respeito do projeto e fazerem seus comentários. Caso haja interferências durante a apresentação do grupo, poderá se estender o tempo de apresentação. A dinâmica de apresentação é livre, contudo, <b>todos os membros do grupo devem estar prontos para responder qualquer tipo de pergunta</b> sobre o projeto. Um consultor da Falconi pode fazer uma pergunta direcionada para um estudante específico do grupo se desejar."
            orientacoes += "<br><br>"
            orientacoes += "As apresentações para a comissão de consultores da Falconi serão usadas para avaliar os melhores projetos. Cada consultor da Falconi poderá colocar seu veredito sobre grupo, usando as rubricas a seguir. Ao final a coordenação do PFE irá fazer a média das avaliações e os projetos que atingirem os níveis de excelência pré-estabelecidos irão receber o certificado de destaque."
            orientacoes += "<br><br>"
            orientacoes += "No Projeto Final de Engenharia, a maioria dos projetos está sob sigilo, através de contratos realizados (quando pedido ou necessário) entre a Organização Parceira e o Insper. A Falconi assinou um documento de responsabilidade em manter o sigilo das informações divulgadas nas apresentações. Assim <b>pessoas externas só podem participar das bancas com prévia autorização</b>, isso inclui outros estudantes que não sejam do grupo, familiares ou amigos."
            orientacoes += "<br>"


        # Carregando dados REST

        avaliador = request.GET.get('avaliador','0')
        try:
            avaliador = int(avaliador)
        except ValueError:
            return HttpResponseNotFound('<h1>Usuário não encontrado!</h1>')

        conceitos = [None]*5
        for i in range(5):
            try:
                tmp1 = int(request.GET.get('objetivo'+str(i),'0'))
            except ValueError:
                return HttpResponseNotFound('<h1>Erro em objetivo!</h1>')
            tmp2 = request.GET.get('conceito'+str(i),'')
            conceitos[i] = (tmp1, tmp2)

        observacoes = unquote(request.GET.get('observacoes',''))

        context = {
            'pessoas' : pessoas,
            'objetivos': objetivos,
            'banca' : banca,
            "orientacoes": orientacoes,
            "avaliador": avaliador,
            "conceitos": conceitos,
            "observacoes": observacoes,
        }
        return render(request, 'projetos/avaliacao.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def edita_aviso(request, primakey):
    """Edita aviso."""

    try:
        aviso = Aviso.objects.get(pk=primakey)
    except Aviso.DoesNotExist:
        return HttpResponse("Aviso não encontrado.", status=401)

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
        try:
            aviso = Aviso.objects.get(id=aviso_id)
        except Aviso.DoesNotExist:
            return HttpResponseNotFound('<h1>Aviso não encontrado!</h1>')
        aviso.realizado = checked
        aviso.save()

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def validate_alunos(request):
    """Ajax para validar vaga de estudantes em propostas."""

    proposta_id = int(request.GET.get('proposta', None))
    vaga = request.GET.get('vaga', "  ")
    checked = request.GET.get('checked', None) == "true"

    try:
        proposta = Proposta.objects.get(id=proposta_id)

        if vaga[0] == 'C':
            if vaga[1] == '1':
                proposta.perfil_aluno1_computacao = checked
            elif vaga[1] == '2':
                proposta.perfil_aluno2_computacao = checked
            elif vaga[1] == '3':
                proposta.perfil_aluno3_computacao = checked
            elif vaga[1] == '4':
                proposta.perfil_aluno4_computacao = checked

        if vaga[0] == 'M':
            if vaga[1] == '1':
                proposta.perfil_aluno1_mecanica = checked
            elif vaga[1] == '2':
                proposta.perfil_aluno2_mecanica = checked
            elif vaga[1] == '3':
                proposta.perfil_aluno3_mecanica = checked
            elif vaga[1] == '4':
                proposta.perfil_aluno4_mecanica = checked

        if vaga[0] == 'X':
            if vaga[1] == '1':
                proposta.perfil_aluno1_mecatronica = checked
            elif vaga[1] == '2':
                proposta.perfil_aluno2_mecatronica = checked
            elif vaga[1] == '3':
                proposta.perfil_aluno3_mecatronica = checked
            elif vaga[1] == '4':
                proposta.perfil_aluno4_mecatronica = checked

        proposta.save()
    except Proposta.DoesNotExist:
        return HttpResponseNotFound('<h1>Proposta não encontrada!</h1>')

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def definir_orientador(request):
    """Ajax para definir orientadores de projetos."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user:

        if user.tipo_de_usuario == 4: # admin

            # Código a se usuário é administrador

            orientador_get = request.GET.get('orientador', None)
            orientador_id = None
            if orientador_get:
                orientador_id = int(orientador_get[len("orientador"):])

            projeto_get = request.GET.get('projeto', None)
            projeto_id = None
            if projeto_get:
                projeto_id = int(projeto_get[len("projeto"):])

            if orientador_id:
                try:
                    orientador = Professor.objects.get(user_id=orientador_id)
                except Professor.DoesNotExist:
                    return HttpResponseNotFound('<h1>Orientador não encontrado!</h1>')
            else:
                orientador = None

            try:
                projeto = Projeto.objects.get(id=projeto_id)
                projeto.orientador = orientador
                projeto.save()
            except Projeto.DoesNotExist:
                return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

            data = {
                'atualizado': True,
            }

        elif user.tipo_de_usuario == 2: # professor

            # atualizações não serão salvas

            data = {
                'atualizado': False,
            }

        else:
            return HttpResponseNotFound('<h1>Usuário sem privilérios!</h1>')

    return JsonResponse(data)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def conceitos_obtidos(request, primarykey): #acertar isso para pk
    """Visualiza os conceitos obtidos pelos alunos no projeto."""

    try:
        projeto = Projeto.objects.get(pk=primarykey)
    except Projeto.DoesNotExist:
        return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

    objetivos = ObjetivosDeAprendizagem.objects.all()

    avaliadores_inter = {}
    avaliadores_final = {}
    avaliadores_falconi = {}

    for objetivo in objetivos:

        # Bancas Intermediárias
        bancas_inter = Avaliacao2.objects.filter(projeto=projeto,
                                                 objetivo=objetivo,
                                                 tipo_de_avaliacao=1).\
                                          order_by('avaliador', '-momento')
        for banca in bancas_inter:
            if banca.avaliador not in avaliadores_inter:
                avaliadores_inter[banca.avaliador] = {}
            if objetivo not in avaliadores_inter[banca.avaliador]:
                avaliadores_inter[banca.avaliador][objetivo] = banca
                avaliadores_inter[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Finais
        bancas_final = Avaliacao2.objects.filter(projeto=projeto,
                                                 objetivo=objetivo,
                                                 tipo_de_avaliacao=2).\
                                          order_by('avaliador', '-momento')
        for banca in bancas_final:
            if banca.avaliador not in avaliadores_final:
                avaliadores_final[banca.avaliador] = {}
            if objetivo not in avaliadores_final[banca.avaliador]:
                avaliadores_final[banca.avaliador][objetivo] = banca
                avaliadores_final[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

        # Bancas Falconi
        bancas_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                   objetivo=objetivo,
                                                   tipo_de_avaliacao=99).\
                                            order_by('avaliador', '-momento')
        for banca in bancas_falconi:
            if banca.avaliador not in avaliadores_falconi:
                avaliadores_falconi[banca.avaliador] = {}
            if objetivo not in avaliadores_falconi[banca.avaliador]:
                avaliadores_falconi[banca.avaliador][objetivo] = banca
                avaliadores_falconi[banca.avaliador]["momento"] = banca.momento
            # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Intermediárias
    observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=1).\
                                            order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_inter:
            avaliadores_inter[observacao.avaliador] = {} # Não devia acontecer isso
        if "observacoes" not in avaliadores_inter[observacao.avaliador]:
            avaliadores_inter[observacao.avaliador]["observacoes"] = observacao.observacoes
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Finais
    observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=2).\
                                            order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_final:
            avaliadores_final[observacao.avaliador] = {} # Não devia acontecer isso
        if "observacoes" not in avaliadores_final[observacao.avaliador]:
            avaliadores_final[observacao.avaliador]["observacoes"] = observacao.observacoes
        # Senão é só uma avaliação de objetivo mais antiga

    # Bancas Falconi
    observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=99).\
                                            order_by('avaliador', '-momento')
    for observacao in observacoes:
        if observacao.avaliador not in avaliadores_falconi:
            avaliadores_falconi[observacao.avaliador] = {} # Não devia acontecer isso
        if "observacoes" not in avaliadores_falconi[observacao.avaliador]:
            avaliadores_falconi[observacao.avaliador]["observacoes"] = observacao.observacoes
        # Senão é só uma avaliação de objetivo mais antiga

    context = {
        'objetivos': objetivos,
        'projeto': projeto,
        'avaliadores_inter' : avaliadores_inter,
        'avaliadores_final' : avaliadores_final,
        "avaliadores_falconi": avaliadores_falconi,
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
                username = request.POST['email'].split("@")[0]
            elif usuario.tipo_de_usuario == 3:
                username = request.POST['email'].split("@")[0] + "." + \
                    request.POST['email'].split("@")[1].split(".")[0]
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            if PFEUser.objects.exclude(pk=usuario.pk).filter(username=username).exists():
                return HttpResponse('Username "%s" já está sendo usado.' % username, status=401)

            usuario.username = username

            if 'nome' in request.POST and len(request.POST['nome'].split()) > 1:
                usuario.first_name = request.POST['nome'].split()[0]
                usuario.last_name = " ".join(request.POST['nome'].split()[1:])
            else:
                return HttpResponse("Erro: Não inserido nome completo no formulário.", status=401)

            if 'genero' in request.POST:
                if request.POST['genero'] == "masculino":
                    usuario.genero = "M"
                elif request.POST['genero'] == "feminino":
                    usuario.genero = "F"
            else:
                usuario.genero = "X"

            if 'linkedin' in request.POST:
                usuario.linkedin = request.POST['linkedin']

            if 'lingua' in request.POST:
                usuario.tipo_lingua = request.POST['lingua']

            usuario.save()

            if usuario.tipo_de_usuario == 1: #estudante

                estudante = Aluno.create(usuario)

                if 'matricula' in request.POST:
                    estudante.matricula = request.POST['matricula']

                if request.POST['curso'] == "computacao":
                    estudante.curso = 'C'   # ('C', 'Computação'),
                elif request.POST['curso'] == "mecanica":
                    estudante.curso = 'M'   # ('M', 'Mecânica'),
                elif request.POST['curso'] == "mecatronica":
                    estudante.curso = 'X'   # ('X', 'Mecatrônica'),
                else:
                    return HttpResponse("Algum erro não identificado.", status=401)

                estudante.anoPFE = int(request.POST['ano'])
                estudante.semestrePFE = int(request.POST['semestre'])

                estudante.save()

            elif usuario.tipo_de_usuario == 2: #professor

                professor = Professor.create(usuario)

                # ("TI", "Tempo Integral"),
                # ("TP", 'Tempo Parcial'),

                if request.POST['dedicacao'] == "ti":
                    professor.dedicacao = 'TI'
                elif request.POST['dedicacao'] == "tp":
                    professor.dedicacao = 'TP'
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

                parceiro = Parceiro.create(usuario)

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

                try:
                    parceiro.organizacao = Organizacao.objects.get(pk=int(request.POST['organizacao']))
                except Organizacao.DoesNotExist:
                    return HttpResponse("Organização não encontrada.", status=401)

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

    tipo = request.GET.get('tipo', None)
    if tipo:
        if tipo=="parceiro":
            organizacao_str = request.GET.get('organizacao', None)
            if organizacao_str:
                try:
                    organizacao_id = int(organizacao_str)
                    organizacao_selecionada = Organizacao.objects.get(id=organizacao_id)
                except (ValueError, Organizacao.DoesNotExist):
                    return HttpResponseNotFound('<h1>Organização não encontrado!</h1>')
                context["organizacao_selecionada"] = organizacao_selecionada
        else:
            return HttpResponseNotFound('<h1>Tipo não reconhecido!</h1>')
        context["tipo"] = tipo

    return render(request, 'projetos/cadastra_usuario.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def definir_datas(request):
    """Definir datas do PFE."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)


    if request.method == 'POST':
        if 'limite_propostas' in request.POST:
            try:
                configuracao.prazo = dateutil.parser.parse(request.POST['limite_propostas'])
                configuracao.save()
                mensagem = "Datas atualizadas."
                context = {
                    "area_principal": True,
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)
            except (ValueError, OverflowError):
                return HttpResponse("Algum erro não identificado.", status=401)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    context = {
        'configuracao': configuracao,
    }
    return render(request, 'projetos/definir_datas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def graficos(request):
    """Mostra graficos das evoluções do PFE."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    periodo = ""
    estudantes = Aluno.objects.filter(user__tipo_de_usuario=1)

    edicoes = range(2018, configuracao.ano+1)

    # PROPOSTAS
    num_propostas = []
    for ano_projeto in edicoes:

        projetos = Proposta.objects.filter(ano=ano_projeto).\
                                    filter(semestre=2).\
                                    count()
        num_propostas.append(projetos)

        projetos = Proposta.objects.filter(ano=ano_projeto+1).\
                                    filter(semestre=1).\
                                    count()
        num_propostas.append(projetos)

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

    if request.is_ajax():
        if 'topicId' in request.POST:
            if request.POST['topicId'] != 'todas':
                periodo = request.POST['topicId'].split('.')
                estudantes = estudantes.filter(anoPFE=int(periodo[0])).\
                                filter(semestrePFE=int(periodo[1]))
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    # Número de estudantes e gêneros
    num_alunos = estudantes.count()
    num_alunos_masculino = estudantes.filter(user__genero='M').count() # Estudantes masculino
    num_alunos_feminino = estudantes.filter(user__genero='F').count() # Estudantes feminino

    context = {
        "num_propostas": num_propostas,
        "num_projetos": num_projetos,
        "num_alunos": num_alunos,
        "num_alunos_feminino": num_alunos_feminino,
        "num_alunos_masculino": num_alunos_masculino,
        'periodo': periodo,
        'ano': configuracao.ano,
        'semestre': configuracao.semestre,
        'loop_anos': edicoes,
    }

    return render(request, 'projetos/graficos.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def migracao(request):
    """temporário"""
    message = "Nada Feito"
    return HttpResponse(message)

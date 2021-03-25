#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import os
import datetime
import csv

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Lower
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render, redirect

from users.models import PFEUser, Aluno, Professor, Opcao, Alocacao

from users.support import get_edicoes

from .models import Projeto, Proposta, Configuracao, Coorientador, Avaliacao2, ObjetivosDeAprendizagem
# from .models import Evento

from .models import Feedback, AreaDeInteresse
from .models import Documento, Encontro, Banco, Reembolso, Aviso, Conexao

from .messages import email, message_reembolso

from .support import get_areas_estudantes, get_areas_propostas, simple_upload


@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if configuracao and configuracao.manutencao:
        return render(request, 'projetos/manutencao.html')
    # num_visits = request.session.get('num_visits', 0) # Visitas a página.
    # request.session['num_visits'] = num_visits + 1

    context = {
        'configuracao': configuracao,
    }

    # 'num_visits': num_visits,
    return render(request, 'index.html', context=context)


@login_required
def index_projetos(request):
    """Página principal dos Projetos."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if configuracao and configuracao.manutencao:
        return render(request, 'projetos/manutencao.html')

    context = {
        'configuracao': configuracao,
    }

    # 'num_visits': num_visits,
    return render(request, 'index_projetos.html', context=context)


@login_required
def projeto_detalhes(request, primarykey):
    """Exibe proposta de projeto com seus detalhes para estudantes."""
    try:
        projeto = Projeto.objects.get(pk=primarykey)
    except Projeto.DoesNotExist:
        return HttpResponse("Projeto não encontrado.", status=401)

    context = {
        'projeto': projeto,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_detalhes.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
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
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_completo.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def distribuicao_areas(request):
    """Distribuição por área de interesse dos alunos/propostas/projetos."""
    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano              # Ano atual
        semestre = configuracao.semestre    # Semestre atual
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    todas = False  # Para mostrar todos os dados de todos os anos e semestres
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
                semestre = int(periodo[1])

            if tipo == "estudantes" and 'curso' in request.POST:
                curso = request.POST['curso']

        else:
            return HttpResponse("Erro não identificado (POST incompleto).",
                                status=401)

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
        return HttpResponse("Erro não identificado (não encontrado tipo).",
                            status=401)

    context['tipo'] = tipo
    context['periodo'] = str(ano)+"."+str(semestre)
    context['ano'] = ano
    context['semestre'] = semestre
    context['loop_anos'] = range(2018, ano+1)

    return render(request, 'projetos/distribuicao_areas.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def projetos_fechados(request):
    """Lista todos os projetos fechados."""
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

            projetos_selecionados = []
            prioridade_list = []
            cooperacoes = []
            conexoes = []
            numero_estudantes = 0

            for projeto in projetos_filtrados:
                estudantes_pfe = Aluno.objects.filter(alocacao__projeto=projeto)
                if estudantes_pfe:  # len(estudantes_pfe) > 0:
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
                    cooperacoes.append(Conexao.objects.filter(projeto=projeto,
                                                        colaboracao=True))
                    conexoes.append(Conexao.objects.filter(projeto=projeto,
                                                        colaboracao=False))

            projetos = zip(projetos_selecionados, prioridade_list, cooperacoes, conexoes)

            context = {
                'projetos': projetos,
                'numero_projetos': len(projetos_selecionados),
                'numero_estudantes': numero_estudantes,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Projeto)
        context = {
            'edicoes': edicoes,
        }

    return render(request, 'projetos/projetos_fechados.html', context)


def get_response(file, path):
    """Checa extensão do arquivo e retorna HttpRensponse corespondente."""
    # Exemplos:
    # image/gif, image/tiff, application/zip,
    # audio/mpeg, audio/ogg, text/csv, text/plain
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
        doc = Documento.objects.filter(documento=local_path[len(settings.BASE_DIR) +\
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
            response['Content-Disposition'] = 'inline; filename=' +\
                os.path.basename(file_path)
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


# @login_required
def arquivos3(request, organizacao, projeto, usuario, path):
    """Permite acessar arquivos do servidor."""
    local_path = os.path.join(settings.MEDIA_ROOT, "{0}/{1}/{2}/{3}".\
        format(organizacao, projeto, usuario, path))

    return carrega_arquivo(request, local_path, path)


@login_required
@permission_required('users.altera_professor', login_url='/')
# def projetos_lista(request, periodo):
def projetos_lista(request):
    """Lista todos os projetos."""
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
        context = {
            'edicoes': edicoes,
        }

    return render(request, 'projetos/projetos_lista.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def relatorios(request):
    """Página para recuperar alguns relatórios."""
    return render(request, 'projetos/relatorios.html')


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
        'configuracao': configuracao,
    }

    return render(request, 'projetos/meuprojeto_aluno.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def carrega_bancos(request):
    """Rotina que carrega arquivo CSV de bancos para base de dados do servidor."""
    with open('projetos/bancos.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                # print("Colunas {} e {}".format(row[0],row[1]))
                pass
            else:
                # print('Nome: {}; Código {}'.format(row[0],row[1]))
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
    else:
        bancos = Banco.objects.all().order_by(Lower("nome"), "codigo")
        context = {
            'usuario': usuario,
            'projeto': projeto,
            'bancos': bancos,
            'configuracao': configuracao,
        }
        return render(request, 'projetos/reembolso_pedir.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def comite(request):
    """Exibe os professores que estão no comitê do PFE."""
    professores = Professor.objects.filter(user__membro_comite=True)

    context = {
        'professores': professores,
        }

    return render(request, 'projetos/comite_pfe.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
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
        'feedbacks': feedbacks,
        'SERVER_URL': settings.SERVER,
        'loop_anos': edicoes,
        'num_projetos': num_projetos,
        'num_feedbacks': num_feedbacks,
    }
    return render(request, 'projetos/lista_feedback.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    try:
        feedback = Feedback.objects.get(id=feedback_id)
    except Feedback.DoesNotExist:
        return HttpResponse("Feedback não encontrado.", status=401)

    context = {
        'feedback': feedback,
    }

    return render(request, 'projetos/mostra_feedback.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
def projetos_vs_propostas(request):
    """Mostra graficos das evoluções do PFE."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    context = {
        "num_propostas": num_propostas,
        "num_projetos": num_projetos,
        'loop_anos': edicoes,
    }

    return render(request, 'projetos/projetos_vs_propostas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def analise_notas(request):
    """Mostra graficos das evoluções do PFE."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    periodo = ""
    estudantes = Aluno.objects.filter(user__tipo_de_usuario=1)

    edicoes, ano, semestre = get_edicoes(Avaliacao2)
    
    medias_semestre = Alocacao.objects.all()

    if request.is_ajax():
        if 'edicao' in request.POST:
            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
                medias_semestre = medias_semestre.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                medias_semestre = medias_semestre.filter(aluno__curso=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else: 
        medias_semestre = medias_semestre.filter(projeto__ano=2020, projeto__semestre=2)

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
            if nota[0] == "RIG":
                if nota[1] >= valor["ideal"]:
                    notas["rig"]["ideal"] += 1
                elif nota[1] >= valor["regular"]:
                    notas["rig"]["regular"] += 1
                else:
                    notas["rig"]["inferior"] += 1
            if nota[0] == "BI":
                if nota[1] >= valor["ideal"]:
                    notas["bi"]["ideal"] += 1
                elif nota[1] >= valor["regular"]:
                    notas["bi"]["regular"] += 1
                else:
                    notas["bi"]["inferior"] += 1
            if nota[0] == "RFI":
                if nota[1] >= valor["ideal"]:
                    notas["rfi"]["ideal"] += 1
                elif nota[1] >= valor["regular"]:
                    notas["rfi"]["regular"] += 1
                else:
                    notas["rfi"]["inferior"] += 1
            if nota[0] == "RFG":
                if nota[1] >= valor["ideal"]:
                    notas["rfg"]["ideal"] += 1
                elif nota[1] >= valor["regular"]:
                    notas["rfg"]["regular"] += 1
                else:
                    notas["rfg"]["inferior"] += 1
            if nota[0] == "BF":
                if nota[1] >= valor["ideal"]:
                    notas["bf"]["ideal"] += 1
                elif nota[1] >= valor["regular"]:
                    notas["bf"]["regular"] += 1
                else:
                    notas["bf"]["inferior"] += 1

    medias_lista = [x.get_media for x in medias_semestre]
    
    medias_validas = list(filter(lambda d: d['pesos'] == 1.0, medias_lista))

    medias = {}
    medias["ideal"] = len(list(filter(lambda d: d['media'] >= valor["ideal"], medias_validas)))
    medias["regular"] = len(list(filter(lambda d: valor["ideal"] > d['media'] >= valor["regular"], medias_validas)))
    medias["inferior"] = len(list(filter(lambda d: d['media'] < valor["regular"], medias_validas)))

    context = {
        'periodo': periodo,
        'ano': configuracao.ano,
        'semestre': configuracao.semestre,
        'loop_anos': edicoes,
        'medias': medias,
        "notas": notas,
        "edicoes": edicoes,
    }

    return render(request, 'projetos/analise_notas.html', context)

def media(notas_lista):
    soma = 0
    total = 0
    for i in notas_lista:
        if i:
            soma += i
            total += 1
    if total == 0:
        return None
    return soma / total


@login_required
@permission_required("users.altera_professor", login_url='/')
def analise_objetivos(request):
    """Mostra graficos das evoluções do PFE."""
    edicoes, ano, semestre = get_edicoes(Avaliacao2)

    alocacoes = Alocacao.objects.all()

    if request.is_ajax():
        if 'edicao' in request.POST:
            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
                alocacoes = alocacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                alocacoes = alocacoes.filter(aluno__curso=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    else: 
        alocacoes = alocacoes.filter(projeto__ano=2020, projeto__semestre=2)

    objetivos = ObjetivosDeAprendizagem.objects.all()

    cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9","#7cfa9f","#e8c3b9","#c45890"]
    count = 0
    cores_obj = {}
    for objetivo in objetivos:
        cores_obj[objetivo] = cores[count]
        count += 1

    valor = {}
    valor["ideal"] = 7.0
    valor["regular"] = 5.0

    notas = {
        "rii": {},
        "rig": {},
        "bi":  {},
        "rfi": {},
        "rfg": {},
        "bf":  {},
    }

    pesos = {
        "rii": {},
        "rig": {},
        "bi":  {},
        "rfi": {},
        "rfg": {},
        "bf":  {},
    }

    
    for nota in notas:
        for objetivo in objetivos:
            notas[nota][objetivo] = 0
            pesos[nota][objetivo] = 0

    notas_lista = [x.get_edicoes for x in alocacoes]

    for nota2 in notas_lista:
        for nota in nota2:
            if nota[0] == "RII":
                for k,v in nota[1].items():
                    notas["rii"][k] += v[0] * v[1]
                    pesos["rii"][k] += v[1]
            if nota[0] == "RIG":
                for k,v in nota[1].items():
                    notas["rig"][k] += v[0] * v[1]
                    pesos["rig"][k] += v[1]
            if nota[0] == "BI":
                for k,v in nota[1].items():
                    notas["bi"][k] += v[0] * v[1]
                    pesos["bi"][k] += v[1]
            if nota[0] == "RFI":
                for k,v in nota[1].items():
                    notas["rfi"][k] += v[0] * v[1]
                    pesos["rfi"][k] += v[1]
            if nota[0] == "RFG":
                for k,v in nota[1].items():
                    notas["rfg"][k] += v[0] * v[1]
                    pesos["rfg"][k] += v[1]
            if nota[0] == "BF":
                for k,v in nota[1].items():
                    notas["bf"][k] += v[0] * v[1]
                    pesos["bf"][k] += v[1]


    medias_geral = {}
    for objetivo in objetivos:
        medias_geral[objetivo] = {}
        medias_geral[objetivo]["cor"] = cores_obj[objetivo]
        medias_geral[objetivo]["soma"] = 0
        medias_geral[objetivo]["peso"] = 0

    medias_rii = {}
    for objetivo in objetivos:
        medias_rii[objetivo] = {}
        medias_rii[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rii"][objetivo]>0:
            medias_rii[objetivo]["media"] = notas["rii"][objetivo] / pesos["rii"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rii"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rii"][objetivo]
        else:
            medias_rii[objetivo]["media"] = 0

    medias_rig = {}
    for objetivo in objetivos:
        medias_rig[objetivo] = {}
        medias_rig[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rig"][objetivo]>0:
            medias_rig[objetivo]["media"] = notas["rig"][objetivo] / pesos["rig"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rig"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rig"][objetivo]
        else:
            medias_rig[objetivo]["media"] = 0


    medias_bi = {}
    for objetivo in objetivos:
        medias_bi[objetivo] = {}
        medias_bi[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["bi"][objetivo]>0:
            medias_bi[objetivo]["media"] = notas["bi"][objetivo] / pesos["bi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["bi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["bi"][objetivo]
        else:
            medias_bi[objetivo]["media"] = 0


    medias_rfi = {}
    for objetivo in objetivos:
        medias_rfi[objetivo] = {}
        medias_rfi[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rfi"][objetivo]>0:
            medias_rfi[objetivo]["media"] = notas["rfi"][objetivo] / pesos["rfi"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rfi"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rfi"][objetivo]
        else:
            medias_rfi[objetivo]["media"] = 0


    medias_rfg = {}
    for objetivo in objetivos:
        medias_rfg[objetivo] = {}
        medias_rfg[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["rfg"][objetivo]>0:
            medias_rfg[objetivo]["media"] = notas["rfg"][objetivo] / pesos["rfg"][objetivo]
            medias_geral[objetivo]["soma"] += notas["rfg"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["rfg"][objetivo]
        else:
            medias_rfg[objetivo]["media"] = 0


    medias_bf = {}
    for objetivo in objetivos:
        medias_bf[objetivo] = {}
        medias_bf[objetivo]["cor"] = cores_obj[objetivo]
        if pesos["bf"][objetivo]>0:
            medias_bf[objetivo]["media"] = notas["bf"][objetivo] / pesos["bf"][objetivo]
            medias_geral[objetivo]["soma"] += notas["bf"][objetivo]
            medias_geral[objetivo]["peso"] += pesos["bf"][objetivo]
        else:
            medias_bf[objetivo]["media"] = 0

    for objetivo in objetivos:
        if medias_geral[objetivo]["peso"] > 0:
            medias_geral[objetivo]["media"] = medias_geral[objetivo]["soma"] / medias_geral[objetivo]["peso"]
        else:
            medias_geral[objetivo]["media"] = 0

    context = {
        "medias_rii": medias_rii,
        "medias_rig": medias_rig,
        "medias_bi": medias_bi,
        "medias_rfi": medias_rfi,
        "medias_rfg": medias_rfg,
        "medias_bf": medias_bf,
        'medias_geral': medias_geral,
        "edicoes": edicoes,
    }

    return render(request, 'projetos/analise_objetivos.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def graficos(request):
    """Mostra graficos das evoluções do PFE."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    periodo = ""
    estudantes = Aluno.objects.filter(user__tipo_de_usuario=1)

    edicoes, _, _ = get_edicoes(Avaliacao2)

    avaliacoes = Avaliacao2.objects.all()

    cores = ["#00af00", "#d40000", "#cccc00", "#000000", ]

    notas_total = {}
    for edicao in edicoes:
        notas_total[edicao] = []

    medias = []
    count = 0
    for curso in Aluno.TIPOS_CURSO:
        notas = []
        for edicao in edicoes:
            periodo = edicao.split('.')
            semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
            notas_lista = [x.nota for x in semestre if (x.alocacao != None and x.alocacao.aluno.curso == curso[0])]
            notas_total[edicao] += notas_lista
            notas.append(media(notas_lista))
        medias.append({"curso": curso[1], "media": notas, "cor": cores[count]})
        count += 1
    
    notas = []
    for edicao in edicoes:
        notas.append(media(notas_total[edicao]))
    medias.append({"curso": "Engenharia", "media": notas, "cor": cores[count]})

    context = {
        "medias": medias,
        'periodo': periodo,
        'ano': configuracao.ano,
        'semestre': configuracao.semestre,
        'edicoes': edicoes,
    }

    return render(request, 'projetos/graficos.html', context)



@login_required
@permission_required("users.altera_professor", login_url='/')
def evolucao_notas(request):
    """Mostra graficos das evoluções do PFE."""
    edicoes, _, _ = get_edicoes(Avaliacao2)

    cores = ["#00af00", "#d40000", "#cccc00", "#000000", ]

    # Para armazenar todas as notas de todos os programas de engenharia
    notas_total = {}
    for edicao in edicoes:
        notas_total[edicao] = []

    # médias gerais individuais
    # (21, 'Relatório Intermediário Individual'),
    # (22, 'Relatório Final Individual'),
    avaliacoes = Avaliacao2.objects.filter(tipo_de_avaliacao=21) | Avaliacao2.objects.filter(tipo_de_avaliacao=22)

    medias_individuais = []
    count = 0
    for curso in Aluno.TIPOS_CURSO:
        notas = []
        for edicao in edicoes:
            periodo = edicao.split('.')
            semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
            notas_lista = [x.nota for x in semestre if (x.alocacao != None and x.alocacao.aluno.curso == curso[0])]
            notas_total[edicao] += notas_lista
            notas.append(media(notas_lista))
        medias_individuais.append({"curso": curso[1], "media": notas, "cor": cores[count]})
        count += 1
    
    notas = []
    for edicao in edicoes:
        notas.append(media(notas_total[edicao]))
    medias_individuais.append({"curso": "engenharia", "media": notas, "cor": cores[count]})


    ################################


    # Para armazenar todas as notas de todos os programas de engenharia
    notas_total = {}
    for edicao in edicoes:
        notas_total[edicao] = []

    # médias gerais totais
    medias_gerais = []
    count = 0
    for curso in Aluno.TIPOS_CURSO:
        notas = []
        for edicao in edicoes:
            periodo = edicao.split('.')
            alocacoes = Alocacao.objects.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1], aluno__curso=curso[0])
            notas_lista = []
            for x in alocacoes:
                media_loc = x.get_media
                if media_loc["pesos"] == 1:
                    notas_lista.append(media_loc["media"])

            notas_total[edicao] += notas_lista
            notas.append(media(notas_lista))
        medias_gerais.append({"curso": curso[1], "media": notas, "cor": cores[count]})
        count += 1
    
    notas = []
    for edicao in edicoes:
        notas.append(media(notas_total[edicao]))
    medias_gerais.append({"curso": "engenharia", "media": notas, "cor": cores[count]})

    context = {
        "medias_individuais": medias_individuais,
        "medias_gerais": medias_gerais,
        'edicoes': edicoes,
    }

    return render(request, 'projetos/evolucao_notas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def evolucao_objetivos(request):
    """Mostra graficos das evoluções do PFE."""
    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    periodo = ""
    estudantes = Aluno.objects.filter(user__tipo_de_usuario=1)

    edicoes, ano, semestre = get_edicoes(Avaliacao2)

    avaliacoes = Avaliacao2.objects.all()

    if request.is_ajax():
        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                avaliacoes = avaliacoes.filter(alocacao__aluno__curso=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9","#7cfa9f","#e8c3b9","#c45890"]

    medias = []
    objetivos = ObjetivosDeAprendizagem.objects.all()
    count = 0
    for objetivo in objetivos:
        notas = []
        for edicao in edicoes:
            periodo = edicao.split('.')
            semestre = avaliacoes.filter(projeto__ano=periodo[0], projeto__semestre=periodo[1])
            notas_lista = [x.nota for x in semestre if x.objetivo == objetivo]
            notas.append(media(notas_lista))
        medias.append({"objetivo": objetivo.titulo, "media": notas, "cor": cores[count]})
        count += 1

    context = {
        "medias": medias,
        'periodo': periodo,
        'ano': configuracao.ano,
        'semestre': configuracao.semestre,
        'edicoes': edicoes,
    }

    return render(request, 'projetos/evolucao_objetivos.html', context)


def cap_name(name):
    """Capitaliza palavras."""
    preposicoes = ['da', 'de', 'di', 'do', 'du', 'das', 'dos']
    items = []
    for item in name.split():
        if item.lower() in preposicoes:
            items.append(item.lower())
        else:
            items.append(item.capitalize())
    return ' '.join(items)


@login_required
@permission_required('users.altera_professor', login_url='/')
def nomes(request):
    """Acerta maiúsculas de nomes."""
    alunos = Aluno.objects.all()

    message = ""
    for aluno in alunos:

        first_name = cap_name(aluno.user.first_name)
        last_name = cap_name(aluno.user.last_name)

        if (first_name != aluno.user.first_name) or (last_name != aluno.user.last_name):

            message += aluno.user.first_name + " "
            message += aluno.user.last_name + "\t\t"

            message += cap_name(aluno.user.first_name) + " "
            message += cap_name(aluno.user.last_name) + "<br>"

            aluno.user.first_name = first_name
            aluno.user.last_name = last_name

            aluno.user.save()

    return HttpResponse(message)


@login_required
@permission_required('users.altera_professor', login_url='/')
def migracao(request):
    """temporário"""
    message = "Nada Feito"
    return HttpResponse(message)

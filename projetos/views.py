#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import os
import datetime
import dateutil.parser
import csv

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.functions import Lower
from django.http import Http404, HttpResponse, HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from users.models import PFEUser, Aluno, Professor, Opcao, Alocacao
from users.models import Parceiro

from users.support import get_edicoes

from .models import Projeto, Proposta, Configuracao, Coorientador, Avaliacao2, ObjetivosDeAprendizagem
# from .models import Evento

from .models import Feedback, AreaDeInteresse, Acompanhamento
from .models import Documento, Encontro, Banco, Reembolso, Aviso, Conexao

from .messages import email, message_reembolso

from .support import get_areas_estudantes, get_areas_propostas, simple_upload, calcula_objetivos


@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
    projeto = get_object_or_404(Projeto, pk=primarykey)
    # try:
    #     projeto = Projeto.objects.get(pk=primarykey)
    # except Projeto.DoesNotExist:
    #     return HttpResponse("Projeto não encontrado.", status=401)

    context = {
        'projeto': projeto,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_detalhes.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def projeto_completo(request, primakey):
    """Mostra um projeto por completo."""
    configuracao = get_object_or_404(Configuracao)

    projeto = get_object_or_404(Projeto, pk=primakey)

    opcoes = Opcao.objects.filter(proposta=projeto.proposta)
    conexoes = Conexao.objects.filter(projeto=projeto)
    coorientadores = Coorientador.objects.filter(projeto=projeto)

    # TIPO_DE_DOCUMENTO = ( # não mudar a ordem dos números
    # (3, 'Relatório Final'),
    # (18, 'Vídeo do Projeto'),
    # (19, 'Slides da Apresentação Final'),
    # (20, 'Banner'),
    # )

    documentos = Documento.objects.filter(projeto=projeto,
        tipo_de_documento__in=(3, 18, 19, 20))

    context = {
        'configuracao': configuracao,
        'projeto': projeto,
        'opcoes': opcoes,
        'conexoes': conexoes,
        'coorientadores': coorientadores,
        'documentos': documentos,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_completo.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def distribuicao_areas(request):
    """Distribuição por área de interesse dos alunos/propostas/projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano              # Ano atual
    semestre = configuracao.semestre    # Semestre atual
    # try:
    #     configuracao = Configuracao.objects.get()
    #     ano = configuracao.ano              # Ano atual
    #     semestre = configuracao.semestre    # Semestre atual
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
            user = get_object_or_404(PFEUser, pk=request.user.pk)

            if (doc.confidencial) and \
                not ( (user.tipo_de_usuario == 2) or (user.tipo_de_usuario == 4) ):
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
    user = get_object_or_404(PFEUser, pk=request.user.pk)
    # try:
    #     user = PFEUser.objects.get(pk=request.user.pk)
    # except PFEUser.DoesNotExist:
    #     return HttpResponse("Usuário não encontrado.", status=401)

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
        professor = get_object_or_404(Professor, pk=request.user.professor.pk)
        # try:
        #     professor = Professor.objects.get(pk=request.user.professor.pk)
        # except Professor.DoesNotExist:
        #     return HttpResponse("Professor não encontrado.", status=401)

        return redirect('professor_detail', primarykey=professor.pk)

    # vvvv Caso seja um aluno  vvv
    aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)
    # try:
    #     aluno = Aluno.objects.get(pk=request.user.aluno.pk)
    # except Aluno.DoesNotExist:
    #     return HttpResponse("Estudante não encontrado.", status=401)

    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

    context = {
        'aluno': aluno,
        'configuracao': configuracao,
    }

    return render(request, 'projetos/meuprojeto_aluno.html', context=context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
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
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

    usuario = get_object_or_404(PFEUser, pk=request.user.pk)
    # try:
    #     usuario = PFEUser.objects.get(pk=request.user.pk)
    # except PFEUser.DoesNotExist:
    #     return HttpResponse("Usuário não encontrado.", status=401)
    if usuario.tipo_de_usuario == 1:
        aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)
        # try:
        #     aluno = Aluno.objects.get(pk=request.user.aluno.pk)
        # except Aluno.DoesNotExist:
        #     return HttpResponse("Aluno não encontrado.", status=401)

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

        reembolso.banco = get_object_or_404(Banco, codigo=request.POST['banco'])
        # try:
        #     reembolso.banco = Banco.objects.get(codigo=request.POST['banco'])
        # except Banco.DoesNotExist:
        #     return HttpResponse("Banco não encontrado.", status=401)

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
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
def lista_acompanhamento(request):
    """Lista todos os acompanhamentos das Organizações Parceiras."""

    acompanhamentos = Acompanhamento.objects.all().order_by("-data")

    context = {
        'acompanhamentos': acompanhamentos,
    }
    return render(request, 'projetos/lista_acompanhamento.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def mostra_feedback(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    feedback = get_object_or_404(Feedback, id=feedback_id)
    # try:
    #     feedback = Feedback.objects.get(id=feedback_id)
    # except Feedback.DoesNotExist:
    #     return HttpResponse("Feedback não encontrado.", status=401)

    context = {
        'feedback': feedback,
    }

    return render(request, 'projetos/mostra_feedback.html', context)


@login_required
@transaction.atomic
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
        aviso = get_object_or_404(Aviso, id=aviso_id)
        # try:
        #     aviso = Aviso.objects.get(id=aviso_id)
        # except Aviso.DoesNotExist:
        #     return HttpResponseNotFound('<h1>Aviso não encontrado!</h1>')
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
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
    
    # Somente apresenta as médias que esteja completas (pesso = 100%)
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


@login_required
@permission_required("users.altera_professor", login_url='/')
def certificacao_falconi(request):
    """Mostra graficos das certificacões Falconi."""
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

    periodo = ""
    
    edicoes, ano, semestre = get_edicoes(Avaliacao2)
    edicoes = ["2020.2"]
    

    if request.is_ajax():
        if 'edicao' in request.POST:
            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
                projetos = Projeto.objects.filter(ano=periodo[0], semestre=periodo[1])
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        # if 'curso' in request.POST:
        #     curso = request.POST['curso']
        #     if curso != 'T':
        #         medias_semestre = medias_semestre.filter(aluno__curso=curso)
        # else:
        #     return HttpResponse("Algum erro não identificado.", status=401)

    else: 
        projetos = Projeto.objects.filter(ano=2020, semestre=2)

    # conceitos = I, D, C, C+, B, B+, A, A+
    conceitos = [0, 0, 0, 0, 0, 0, 0, 0]
    total = len(projetos)
    selecionados = 0
    for projeto in projetos:
        aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto, tipo_de_avaliacao=99)  # Falc.
        nota_banca_falconi, peso = Aluno.get_banca(None, aval_banc_falconi)
        if peso is not None:
            selecionados += 1
            if nota_banca_falconi >= 9.5:
                conceitos[7] += 1
            elif nota_banca_falconi >= 9.0:
                conceitos[6] += 1
            elif nota_banca_falconi >= 8.0:
                conceitos[5] += 1
            elif nota_banca_falconi >= 7.0:
                conceitos[4] += 1
            elif nota_banca_falconi >= 6.0:
                conceitos[3] += 1
            elif nota_banca_falconi >= 5.0:
                conceitos[2] += 1
            elif nota_banca_falconi >= 4.0:
                conceitos[1] += 1
            else:
                conceitos[0] += 1

    for i in range(8):
        conceitos[i] *= 100/selecionados

    context = {
        'ano': configuracao.ano,
        'semestre': configuracao.semestre,
        "edicoes": edicoes,
        "selecionados": selecionados,
        "nao_selecionados": total - selecionados,
        "conceitos": conceitos,
    }

    return render(request, 'projetos/certificacao_falconi.html', context)


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


    context = calcula_objetivos(alocacoes)

    context["edicoes"] = edicoes

    return render(request, 'projetos/analise_objetivos.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def graficos(request):
    """Mostra graficos das evoluções do PFE."""
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

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
@transaction.atomic
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
@transaction.atomic
@permission_required("users.altera_professor", login_url='/')
def acompanhamento_view(request):
    """Cria um anotação para uma organização parceira."""
    
    acompanhamentos = Acompanhamento.objects.all().order_by("-data")
    
    if request.is_ajax() and 'texto' in request.POST:
        acompanhamento = Acompanhamento.create()
        
        parceiro_id = int(request.POST['parceiro'])
        parceiro = get_object_or_404(Parceiro, id=parceiro_id)
        acompanhamento.autor = parceiro.user
        # try:
        #     parceiro_id = int(request.POST['parceiro'])
        #     parceiro = Parceiro.objects.get(id=parceiro_id)
        #     acompanhamento.autor = parceiro.user
        # except Parceiro.DoesNotExist:
        #     return HttpResponse("Usuário não encontrado.", status=401)

        acompanhamento.texto = request.POST['texto']

        if 'data_hora' in request.POST:
            try:
                acompanhamento.data = dateutil.parser\
                    .parse(request.POST['data_hora'])
            except (ValueError, OverflowError):
                acompanhamento.data = datetime.datetime.now()

        acompanhamento.save()

        data = {
            'data': acompanhamento.data.strftime("%Y.%m.%d"),
            'autor': str(acompanhamento.autor.get_full_name()),
            'org': str(parceiro.organizacao),
            'atualizado': True,
        }

        return JsonResponse(data)

    parceiros = Parceiro.objects.all()

    context = {
            'parceiros': parceiros,
            'data_hora': datetime.datetime.now(),
        }

    return render(request,
                    'projetos/acompanhamento_view.html',
                    context=context)

from django.contrib.admin.models import LogEntry

@login_required
@permission_required('users.altera_professor', login_url='/')
def migracao(request):
    """temporário"""
    #message = "Nada Feito"
    message = ""
    logs = LogEntry.objects.all()
    for log in logs:
        message += str(log)+"<br>\n"

    return HttpResponse(message)

#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 15 de Maio de 2019
"""

import os
import re
import datetime
import csv
import mimetypes

from wsgiref.util import FileWrapper
import dateutil.parser

from django.http.response import StreamingHttpResponse

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.functions import Lower
from django.http import Http404, HttpResponse
# from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from users.models import PFEUser, Aluno, Professor, Opcao, Alocacao
from users.models import Parceiro
from users.support import adianta_semestre
from users.support import get_edicoes

from .models import Projeto, Proposta, Configuracao, Observacao
from .models import Coorientador, Avaliacao2, ObjetivosDeAprendizagem
# from .models import Evento

from .models import Feedback, AreaDeInteresse, Acompanhamento, Anotacao, Organizacao
from .models import Documento, FeedbackEstudante
# from .models import Encontro
from .models import Banco, Reembolso, Aviso, Conexao

from .messages import email, message_reembolso

from .support import get_areas_estudantes, get_areas_propostas, simple_upload, calcula_objetivos


@login_required
def index(request):
    """Página principal do sistema do Projeto Final de Engenharia."""
    configuracao = get_object_or_404(Configuracao)
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

    context = {
        'projeto': projeto,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_detalhes.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def projeto_completo(request, primarykey):
    """Mostra um projeto por completo."""
    configuracao = get_object_or_404(Configuracao)

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

    # TIPO_DE_DOCUMENTO = ( # não mudar a ordem dos números
    # (3, 'Relatório Final'),
    # (18, 'Vídeo do Projeto'),
    # (19, 'Slides da Apresentação Final'),
    # (20, 'Banner'),
    # (25, 'Relatório Publicado'),
    # (27, 'Apresentação da Banca Final'),
    # )

    documentos = Documento.objects.filter(projeto=projeto,
                                          tipo_de_documento__in=(3, 18, 19, 20, 25, 27))

    projetos_avancados = Projeto.objects.filter(avancado=projeto)

    cooperacoes = Conexao.objects.filter(projeto=projeto, colaboracao=True)

    context = {
        "configuracao": configuracao,
        "projeto": projeto,
        "alocacoes": alocacoes,
        "medias_oo": medias_oo,
        "opcoes": opcoes,
        "conexoes": conexoes,
        "coorientadores": coorientadores,
        "documentos": documentos,
        "projetos_avancados": projetos_avancados,
        "cooperacoes": cooperacoes,
        "MEDIA_URL": settings.MEDIA_URL,
    }

    return render(request, 'projetos/projeto_completo.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def distribuicao_areas(request):
    """Distribuição por área de interesse dos alunos/propostas/projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano              # Ano atual
    semestre = configuracao.semestre    # Semestre atual

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

            if 'curso' in request.POST:
                curso = request.POST['curso']

            if 'curso' in request.POST:
                curso = request.POST['curso']    
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            projetos_filtrados = projetos_filtrados.order_by("-avancado", "organizacao")

            projetos_selecionados = []
            prioridade_list = []
            cooperacoes = []
            conexoes = []

            numero_estudantes = 0
            numero_estudantes_avancado = 0

            numero_projetos = 0
            numero_projetos_avancado = 0

            for projeto in projetos_filtrados:

                estudantes_pfe = Aluno.objects.filter(alocacao__projeto=projeto)
                if curso != 'T':
                    estudantes_pfe = estudantes_pfe.filter(alocacao__aluno__curso=curso)

                if estudantes_pfe:  # len(estudantes_pfe) > 0:
                    projetos_selecionados.append(projeto)
                    if projeto.avancado:
                        numero_estudantes_avancado += len(estudantes_pfe)
                        numero_projetos_avancado += 1
                    else:
                        numero_estudantes += len(estudantes_pfe)
                        numero_projetos += 1

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
                'numero_projetos': numero_projetos,
                'numero_projetos_avancado': numero_projetos_avancado,
                'numero_estudantes': numero_estudantes,
                'numero_estudantes_avancado': numero_estudantes_avancado,
            }

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
    else:
        edicoes, ano, semestre = get_edicoes(Projeto)
        context = {
            'edicoes': edicoes,
        }

    return render(request, 'projetos/projetos_fechados.html', context)


# FONTE: https://stackoverflow.com/questions/33208849/
# ... python-django-streaming-video-mp4-file-using-httpresponse/41289535#41289535
class RangeFileWrapper:
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()

        if self.remaining <= 0:
            raise StopIteration()
        data = self.filelike.read(min(self.remaining, self.blksize))
        if not data:
            raise StopIteration()
        self.remaining -= len(data)
        return data


def stream_video(request, path):
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    # content_type, encoding = mimetypes.guess_type(path)
    content_type, _ = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    resp = None
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'), offset=first_byte, length=length),
                                     status=206, content_type=content_type)
        #resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
        #resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
    return resp


def get_response(file, path, request):
    """Checa extensão do arquivo e retorna HttpRensponse corespondente."""
    # Exemplos:
    # image/gif, image/tiff, application/zip,
    # audio/mpeg, audio/ogg, text/csv, text/plain
    if path[-3:].lower() == "jpg" or path[-4:].lower() == "jpeg":
        return HttpResponse(file.read(), content_type="image/jpeg")
    elif path[-3:].lower() == "png":
        return HttpResponse(file.read(), content_type="image/png")
    elif path[-3:].lower() == "doc":
        return HttpResponse(file.read(), content_type=\
            'application/msword')
    elif path[-4:].lower() == "docx":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    elif path[-3:].lower() == "ppt":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.ms-powerpoint')
    elif path[-4:].lower() == "pptx":
        return HttpResponse(file.read(), content_type=\
            'application/vnd.openxmlformats-officedocument.presentationml.presentation')
    elif path[-3:].lower() == "pdf":
        return HttpResponse(file.read(), content_type="application/pdf")
    elif path[-3:].lower() == "mp4":
        return stream_video(request, file.name)
    elif path[-3:].lower() == "mkv":
        return HttpResponse(file.read(), content_type="video/webm")
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
        documento = local_path[len(settings.BASE_DIR) + len(settings.MEDIA_URL):]

        doc = Documento.objects.filter(documento=documento).last()
        if doc:
            user = get_object_or_404(PFEUser, pk=request.user.pk)

            if (doc.confidencial) and \
                not ((user.tipo_de_usuario == 2) or (user.tipo_de_usuario == 4)):
                mensagem = "Documento Confidencial"
                context = {
                    "mensagem": mensagem,
                }
                return render(request, 'generic.html', context=context)

        if documento[:3] == "tmp":
            mensagem = "Documento não acessível"
            context = {
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        with open(file_path, 'rb') as file:
            response = get_response(file, path, request)
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
# Para pegar certificados não pode ter o login required
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
        return redirect('professor_detail', primarykey=professor.pk)

    # vvvv Caso seja um aluno  vvv
    aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)

    configuracao = get_object_or_404(Configuracao)

    context = {
        'aluno': aluno,
        'configuracao': configuracao,
    }

    return render(request, 'projetos/meuprojeto_aluno.html', context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
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
    usuario = get_object_or_404(PFEUser, pk=request.user.pk)

    if usuario.tipo_de_usuario == 1:
        aluno = get_object_or_404(Aluno, pk=request.user.aluno.pk)

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
def lista_feedback_estudantes(request):
    """Lista todos os feedback das Organizações Parceiras."""
    configuracao = get_object_or_404(Configuracao)

    edicoes = range(2018, configuracao.ano+1)

    todos_feedbacks = FeedbackEstudante.objects.all().order_by("-momento")

    num_feedbacks = []
    num_estudantes = []

    for ano in edicoes:

        estudantes = Aluno.objects.filter(anoPFE=ano).\
            filter(semestrePFE=2).\
            count()
        num_estudantes.append(estudantes)

        estudantes = Aluno.objects.filter(anoPFE=ano+1).\
            filter(semestrePFE=1).\
            count()
        num_estudantes.append(estudantes)

        numb_feedb = todos_feedbacks.filter(projeto__ano=ano).\
            filter(projeto__semestre=2).\
            values('estudante').distinct().\
            count()
        num_feedbacks.append(numb_feedb)

        numb_feedb = todos_feedbacks.filter(projeto__ano=ano+1).\
            filter(projeto__semestre=1).\
            values('estudante').distinct().\
            count()
        num_feedbacks.append(numb_feedb)

    ano = 2021
    semestre = 2
    estudantes = Aluno.objects.filter(trancado=False, anoPFE=ano, semestrePFE=semestre)

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

    context = {
        "SERVER_URL": settings.SERVER,
        "loop_anos": edicoes,
        "num_estudantes": num_estudantes,
        "num_feedbacks": num_feedbacks,
        "alocacoes": alocacoes,
    }
    return render(request, 'projetos/lista_feedback_estudantes.html', context)



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

    context = {
        'feedback': feedback,
    }

    return render(request, 'projetos/mostra_feedback.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def mostra_feedback_estudante(request, feedback_id):
    """Detalha os feedbacks das Organizações Parceiras."""
    feedback = get_object_or_404(FeedbackEstudante, id=feedback_id)

    usuario = feedback.estudante.user
    projeto = feedback.projeto

    context = {
        "usuario": usuario,
        "projeto": projeto,
        "feedback": feedback,
    }

    return render(request, 'estudantes/estudante_feedback.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
def validate_aviso(request):
    """Ajax para validar avisos."""
    aviso_id = int(request.GET.get('aviso', None)[len("aviso"):])
    checked = request.GET.get('checked', None) == "true"
    value = request.GET.get('value', None)

    aviso = get_object_or_404(Aviso, id=aviso_id)
    aviso.realizado = checked

    if checked:
        # Marca a data do aviso como ultima marcação
        aviso.data_realizado = dateutil.parser.parse(value)
    else:
        # Marca a data do aviso como dia anterior
        aviso.data_realizado = dateutil.parser.parse(value) - datetime.timedelta(days=1)

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

    edicoes = range(2018, configuracao.ano+1)

    edicoes2, _, _ = get_edicoes(Projeto)

    total_org_propostas = {}
    total_org_projetos = {}

    # PROPOSTAS e ORGANIZACOES COM PROPOSTAS
    num_propostas = []
    org_propostas = []
    for ano_projeto in edicoes:

        # Segundo Semeste
        propostas = Proposta.objects.filter(ano=ano_projeto).\
            filter(semestre=2)
        num_propostas.append(propostas.count())
        tmp_org = {}
        for projeto in propostas:
            if projeto.organizacao:
                tmp_org[projeto.organizacao.id] = "True"
                total_org_propostas[projeto.organizacao.id] = "True"
        org_propostas.append(len(tmp_org))

        # Primeiro Semestre
        propostas = Proposta.objects.filter(ano=ano_projeto+1).\
            filter(semestre=1)
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
    for ano_projeto in edicoes:

        # Segundo Semeste
        projetos = Projeto.objects.filter(ano=ano_projeto).\
                                   filter(semestre=2)
        num_projetos.append(projetos.count())
        tmp_org = {}
        for projeto in projetos:
            if projeto.organizacao:
                tmp_org[projeto.organizacao.id] = "True"
                total_org_projetos[projeto.organizacao.id] = "True"
        org_projetos.append(len(tmp_org))

        # Primeiro Semestre
        projetos = Projeto.objects.filter(ano=ano_projeto+1).\
            filter(semestre=1)
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
        "num_projetos": num_projetos,
        "total_propostas": sum(num_propostas),
        "total_projetos": sum(num_projetos),
        "org_prospectadas": org_prospectadas,
        "org_propostas": org_propostas,
        "org_projetos": org_projetos,
        "total_org_propostas": len(total_org_propostas),
        "total_org_projetos": len(total_org_projetos),
        'loop_anos': edicoes,
        'edicoes': edicoes2,
    }

    return render(request, 'projetos/projetos_vs_propostas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def analise_notas(request):
    """Mostra graficos das evoluções do PFE."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, _ = get_edicoes(Avaliacao2)

    if request.is_ajax():

        periodo = ""
        # estudantes = Aluno.objects.filter(user__tipo_de_usuario=1)
        medias_semestre = Alocacao.objects.all()

        if 'edicao' in request.POST:
            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
                medias_semestre = medias_semestre.filter(projeto__ano=periodo[0],
                                                         projeto__semestre=periodo[1])
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                medias_semestre = medias_semestre.filter(aluno__curso=curso)
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
        }

    else:
        context = {
            "edicoes": edicoes,
        }


    return render(request, 'projetos/analise_notas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def certificacao_falconi(request):
    """Mostra graficos das certificacões Falconi."""
    configuracao = get_object_or_404(Configuracao)

    edicoes, _, _ = get_edicoes(Avaliacao2)
    edicoes = ["2020.2", "2021.1"]

    if request.is_ajax():

        periodo = ""

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

        # conceitos = I, D, C, C+, B, B+, A, A+
        conceitos = [0, 0, 0, 0, 0, 0, 0, 0]
        total = len(projetos)
        selecionados = 0
        projetos_selecionados = []
        for projeto in projetos:
            aval_banc_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                          tipo_de_avaliacao=99)  # Falc.

            if aval_banc_falconi:
                projetos_selecionados.append(projeto)

            nota_banca_falconi, peso, avaliadores = Aluno.get_banca(None, aval_banc_falconi)
            if peso is not None:
                selecionados += 1
                if nota_banca_falconi >= 9.5:  # conceito A+
                    conceitos[7] += 1
                elif nota_banca_falconi >= 8.5:  # conceito A
                    conceitos[6] += 1
                elif nota_banca_falconi >= 7.5:  # conceito B+
                    conceitos[5] += 1
                elif nota_banca_falconi >= 6.5:  # conceito B
                    conceitos[4] += 1
                elif nota_banca_falconi >= 5.5:  # conceito C+
                    conceitos[3] += 1
                elif nota_banca_falconi >= 4.5:  # conceito C
                    conceitos[2] += 1
                elif nota_banca_falconi >= 1.5:  # Qualquer D
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
                bancas_falconi = Avaliacao2.objects.filter(projeto=projeto,
                                                        objetivo=objetivo,
                                                        tipo_de_avaliacao=99)\
                    .order_by('avaliador', '-momento')

                for banca in bancas_falconi:
                    if banca.avaliador not in avaliadores_falconi:
                        avaliadores_falconi[banca.avaliador] = {}
                    if objetivo not in avaliadores_falconi[banca.avaliador]:
                        avaliadores_falconi[banca.avaliador][objetivo] = banca
                        avaliadores_falconi[banca.avaliador]["momento"] = banca.momento
                    # Senão é só uma avaliação de objetivo mais antiga

            # Bancas Falconi
            observacoes = Observacao.objects.filter(projeto=projeto, tipo_de_avaliacao=99).\
                order_by('avaliador', '-momento')
            for observacao in observacoes:
                if observacao.avaliador not in avaliadores_falconi:
                    avaliadores_falconi[observacao.avaliador] = {}  # Não devia acontecer isso
                if "observacoes" not in avaliadores_falconi[observacao.avaliador]:
                    avaliadores_falconi[observacao.avaliador]["observacoes"] = observacao.observacoes
                # Senão é só uma avaliação de objetivo mais antiga

            avaliadores.append(avaliadores_falconi)

        bancas = zip(projetos_selecionados, avaliadores)

        context = {
            'ano': configuracao.ano,
            'semestre': configuracao.semestre,
            "edicoes": edicoes,
            "selecionados": selecionados,
            "nao_selecionados": total - selecionados,
            "conceitos": conceitos,
            "projetos_selecionados": projetos_selecionados,
            'objetivos': objetivos,
            "bancas": bancas,
        }

    else:
        context = {
            "edicoes": edicoes,
        }

    return render(request, 'projetos/certificacao_falconi.html', context)


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


@login_required
@permission_required("users.altera_professor", login_url='/')
def analise_objetivos(request):
    """Mostra graficos das evoluções do PFE."""
    edicoes, _, _ = get_edicoes(Avaliacao2)

    if request.is_ajax():

        alocacoes = Alocacao.objects.all()

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

        context = calcula_objetivos(alocacoes)
        context["edicoes"] = edicoes
        context["total_geral"] = len(alocacoes)

    else:
        context = {
            "edicoes": edicoes,
        }

    return render(request, 'projetos/analise_objetivos.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def evolucao_notas(request):
    """Mostra graficos das evoluções do PFE."""
    edicoes, _, _ = get_edicoes(Avaliacao2)

    if request.is_ajax():

        avaliacoes = Avaliacao2.objects.all()
        alocacoes = Alocacao.objects.all()

        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                avaliacoes = avaliacoes.filter(alocacao__aluno__curso=curso)
                alocacoes = alocacoes.filter(aluno__curso=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        cores = ["#00af00", "#d40000", "#cccc00", "#000000", ]

        # Para armazenar todas as notas de todos os programas de engenharia
        notas_total = {}
        for edicao in edicoes:
            notas_total[edicao] = []

        # médias gerais individuais
        # (21, 'Relatório Intermediário Individual'),
        # (22, 'Relatório Final Individual'),
        avaliacoes = avaliacoes.filter(tipo_de_avaliacao=21) | avaliacoes.filter(tipo_de_avaliacao=22)

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
            if notas != [None] * len(notas):  # não está vazio
                medias_individuais.append({"curso": curso[1], "media": notas, "cor": cores[count]})
            count += 1

        if len(medias_individuais) > 1:
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
                alocacoes_tmp = alocacoes.filter(projeto__ano=periodo[0],
                                                 projeto__semestre=periodo[1],
                                                 aluno__curso=curso[0])
                notas_lista = []
                for alocacao in alocacoes_tmp:
                    media_loc = alocacao.get_media
                    if media_loc["pesos"] == 1:
                        notas_lista.append(media_loc["media"])

                notas_total[edicao] += notas_lista
                notas.append(media(notas_lista))
            if notas != [None] * len(notas):  # não está vazio
                medias_gerais.append({"curso": curso[1], "media": notas, "cor": cores[count]})
            count += 1

        if len(medias_gerais) > 1:
            notas = []
            for edicao in edicoes:
                notas.append(media(notas_total[edicao]))
            medias_gerais.append({"curso": "engenharia", "media": notas, "cor": cores[count]})

        context = {
            "medias_individuais": medias_individuais,
            "medias_gerais": medias_gerais,
            "edicoes": edicoes,
        }

    else:
        context = {
            "edicoes": edicoes,
        }

    return render(request, 'projetos/evolucao_notas.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def evolucao_objetivos(request):
    """Mostra graficos das evoluções do PFE."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    if request.is_ajax():

        periodo = ""
        # estudantes = Aluno.objects.filter(user__tipo_de_usuario=1)

        avaliacoes = Avaliacao2.objects.all()

        if 'curso' in request.POST:
            curso = request.POST['curso']
            if curso != 'T':
                avaliacoes = avaliacoes.filter(alocacao__aluno__curso=curso)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

        cores = ["#c3cf95", "#d49fbf", "#ceb5ed", "#9efef9", "#7cfa9f", "#e8c3b9", "#c45890", "#375330", "#a48577"]

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

    else:

        context = {
            "edicoes": edicoes,
        }

    return render(request, 'projetos/evolucao_objetivos.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def correlacao_medias_cr(request):
    """Mostra graficos da correlação entre notas e o CR dos estudantes."""
    configuracao = get_object_or_404(Configuracao)
    edicoes, _, semestre = get_edicoes(Avaliacao2)

    if request.is_ajax():
        periodo = ""
        alocacoes = None
        estudantes_computacao = None
        estudantes_mecanica = None
        estudantes_mecatronica = None

        if 'edicao' in request.POST:

            curso = request.POST['curso']

            if request.POST['edicao'] != 'todas':
                periodo = request.POST['edicao'].split('.')
                alocacoes_tmp = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                        projeto__semestre=periodo[1])

                if curso == 'C':
                    estudantes_computacao = alocacoes_tmp.filter(aluno__curso="C")
                elif curso == 'M':
                    estudantes_mecanica = alocacoes_tmp.filter(aluno__curso="M")
                elif curso == 'X':
                    estudantes_mecatronica = alocacoes_tmp.filter(aluno__curso="X")
                else:
                    estudantes_computacao = alocacoes_tmp.filter(aluno__curso="C")
                    estudantes_mecanica = alocacoes_tmp.filter(aluno__curso="M")
                    estudantes_mecatronica = alocacoes_tmp.filter(aluno__curso="X")

            else:
                alocacoes = {}
                for edicao in edicoes:
                    periodo = edicao.split('.')
                    semestre = Alocacao.objects.filter(projeto__ano=periodo[0],
                                                       projeto__semestre=periodo[1])
                    if curso == 'T':
                        alocacoes[periodo[0]+"_"+periodo[1]] = semestre
                    else:
                        semestre = semestre.filter(aluno__curso=curso)
                        alocacoes[periodo[0]+"_"+periodo[1]] = semestre

        else:
            return HttpResponse("Algum erro não identificado.", status=401)
        # else:
        #     alocacoes_tmp = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre)
        #     estudantes_computacao = alocacoes_tmp.filter(aluno__curso="C")
        #     estudantes_mecanica = alocacoes_tmp.filter(aluno__curso="M")
        #     estudantes_mecatronica = alocacoes_tm`p.filter(aluno__curso="X")

        context = {
            "alocacoes": alocacoes,
            "estudantes_computacao": estudantes_computacao,
            "estudantes_mecanica": estudantes_mecanica,
            "estudantes_mecatronica": estudantes_mecatronica,
            'periodo': periodo,
            'ano': configuracao.ano,
            'semestre': configuracao.semestre,
            'edicoes': edicoes,
        }

    else:
        context = {
            'edicoes': edicoes,
        }

    return render(request, 'projetos/correlacao_medias_cr.html', context)

@login_required
@permission_required("users.altera_professor", login_url='/')
def editar_projeto(request, primarykey):
    """Editar Projeto."""

    projeto = Projeto.objects.get(id=primarykey)

    if request.method == 'POST':

        titulo = request.POST.get('titulo', None)
        if titulo and ( projeto.titulo_final or projeto.titulo != titulo):
            projeto.titulo_final = titulo

        descricao = request.POST.get('descricao', None)
        if descricao and ( projeto.descricao or projeto.proposta.descricao != descricao):
            projeto.descricao = descricao

        orientador_id = request.POST.get('orientador', None)
        if orientador_id:
            orientador = get_object_or_404(Professor, pk=orientador_id)
            projeto.orientador = orientador

        coorientador_id = request.POST.get('coorientador', None)
        if coorientador_id:
            coorientador = get_object_or_404(PFEUser, pk=coorientador_id)
            (reg, _created) = Coorientador.objects.get_or_create(projeto=projeto)
            reg.usuario = coorientador
            reg.save()

        alocacoes = Alocacao.objects.filter(projeto=projeto).delete()

        estudante_id = request.POST.get('estudante1', None)
        if estudante_id:
            estudante = get_object_or_404(Aluno, pk=estudante_id)
            alocacao = Alocacao.create(estudante, projeto)
            alocacao.save()

        estudante_id = request.POST.get('estudante2', None)
        if estudante_id:
            estudante = get_object_or_404(Aluno, pk=estudante_id)
            alocacao = Alocacao.create(estudante, projeto)
            alocacao.save()

        estudante_id = request.POST.get('estudante3', None)
        if estudante_id:
            estudante = get_object_or_404(Aluno, pk=estudante_id)
            alocacao = Alocacao.create(estudante, projeto)
            alocacao.save()

        estudante_id = request.POST.get('estudante4', None)
        if estudante_id:
            estudante = get_object_or_404(Aluno, pk=estudante_id)
            alocacao = Alocacao.create(estudante, projeto)
            alocacao.save()


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


def cap_name(name):
    """Capitaliza palavras."""
    excecoes = ['e', 'da', 'de', 'di', 'do', 'du', 'das', 'dos']
    items = []
    for item in name.split():
        if item.lower() in excecoes:
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
    # acompanhamentos = Acompanhamento.objects.all().order_by("-data")
    if request.is_ajax() and 'texto' in request.POST:
        acompanhamento = Acompanhamento.create()

        parceiro_id = int(request.POST['parceiro'])
        parceiro = get_object_or_404(Parceiro, id=parceiro_id)
        acompanhamento.autor = parceiro.user

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


@login_required
@permission_required('users.altera_professor', login_url='/')
def logs(request):
    """Alguns logs de Admin."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    # Caso não seja Administrador
    if user.tipo_de_usuario != 4:
        mensagem = "Você não está cadastrado como administador"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    message = ""
    mensagens = LogEntry.objects.all()
    for log in mensagens:
        message += str(log)+"<br>\n"
    return HttpResponse(message)


@login_required
@permission_required('users.altera_professor', login_url='/')
def conexoes_estabelecidas(request):
    """Mostra usuários conectados."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)
    if user.tipo_de_usuario == 4:
        message = "<h3>Usuários Conectados</h3><br>"
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            user_id = data.get('_auth_user_id', None)
            try:
                user = PFEUser.objects.get(id=user_id)
                message += "- " + str(user)
                message += "; autenticado: " + str(user.is_authenticated)
                message += "; conectado desde: " + str(user.last_login)
                message += "; permissões: " + str(user.get_all_permissions())[:120]
                message += "<br>"
            except PFEUser.DoesNotExist:
                message += "PROBLEMA COM USER ID = " + str(user_id)
                message += "; Data = " + str(data)
                message += "<br>"
        return HttpResponse(message)
    return HttpResponse("Você não tem privilégios")


@login_required
@permission_required('users.altera_professor', login_url='/')
def migracao(request):
    """temporário."""
    message = "Nada Feito"

    recipient_list = ['pfeinsper@gmail.com', ]

    configuracao = get_object_or_404(Configuracao)
    comite = PFEUser.objects.filter(membro_comite=True)
    
    lista_comite = [obj.email for obj in comite]

    recipient_list += lista_comite

    print(recipient_list)

    return HttpResponse(message)

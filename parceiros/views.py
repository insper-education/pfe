"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime

from django.conf import settings

from django.shortcuts import render

from django.contrib.auth.decorators import login_required, permission_required

#from django.http import Http404, HttpResponse, , JsonResponse
from django.http import HttpResponse, HttpResponseNotFound


#from users.models import Aluno, Opcao, Alocacao
from users.models import PFEUser, Administrador, Parceiro, Professor, Aluno

#from projetos.models import ObjetivosDeAprendizagem, Avaliacao2, Observacao, Area, AreaDeInteresse
from projetos.models import Area, Proposta, Organizacao, Projeto, Configuracao

#from projetos.models import Projeto, Evento, Coorientador
from projetos.models import Anotacao

from propostas.support import envia_proposta, preenche_proposta


@login_required
@permission_required("users.altera_valores", login_url='/projetos/')
def index_parceiros(request):
    """Mostra página principal do usuário que é um parceiro de uma organização."""

    return render(request, 'parceiros/index_parceiros.html')


@login_required
@permission_required('users.altera_parceiro', login_url='/projetos/')
def parceiro_propostas(request):
    """Lista todas as propostas de projetos."""

    user = PFEUser.objects.get(pk=request.user.pk)
    if user.tipo_de_usuario != 2 and user.tipo_de_usuario != 4:
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
    }
    return render(request, 'parceiros/parceiro_propostas.html', context)


#@login_required
def proposta_submissao(request):
    """Formulário de Submissão de Proposta de Projetos."""
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        user = None

    parceiro = None
    professor = None
    administrador = None
    organizacao = ""
    website = "http://"
    endereco = ""
    descricao_organizacao = ""
    full_name = ""
    email_sub = ""

    if user:

        if user.tipo_de_usuario == 1: # alunos
            mensagem = "Você não está cadastrado como parceiro de uma organização!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        full_name = user.get_full_name()
        email_sub = user.email

        if user.tipo_de_usuario == 3: # parceiro
            try:
                parceiro = Parceiro.objects.get(pk=request.user.parceiro.pk)
            except Parceiro.DoesNotExist:
                return HttpResponse("Parceiro não encontrado.", status=401)
            organizacao = parceiro.organizacao
            website = parceiro.organizacao.website
            endereco = parceiro.organizacao.endereco
            descricao_organizacao = parceiro.organizacao.informacoes
        elif user.tipo_de_usuario == 2: # professor
            try:
                professor = Professor.objects.get(pk=request.user.professor.pk)
            except Professor.DoesNotExist:
                return HttpResponse("Professor não encontrado.", status=401)
        elif user.tipo_de_usuario == 4: # admin
            try:
                administrador = Administrador.objects.get(pk=request.user.administrador.pk)
            except Administrador.DoesNotExist:
                return HttpResponse("Administrador não encontrado.", status=401)

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

    areas = Area.objects.filter(ativa=True)

    organizacao_str = request.GET.get('organizacao', None)
    if organizacao_str:
        try:
            organizacao_id = int(organizacao_str)
            organizacao = Organizacao.objects.get(id=organizacao_id)
        except (ValueError, Organizacao.DoesNotExist):
            return HttpResponseNotFound('<h1>Organização não encontrado!</h1>')

    context = {
        'full_name' : full_name,
        'email' : email_sub,
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
        'areast' : areas,
        'recursos' : "",
        'observacoes' : "",
        'edicao' : False,
        'interesses' : Proposta.TIPO_INTERESSE,
        'tipo_de_interesse' : 0 # Não existe na verdade
    }
    return render(request, 'parceiros/proposta_submissao.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/projetos/')
def organizacoes_lista(request):
    """Exibe todas as organizações que já submeteram propostas de projetos."""

    organizacoes = Organizacao.objects.all()
    fechados = []
    desde = []
    contato = []
    for organizacao in organizacoes:
        propostas = Proposta.objects.filter(organizacao=organizacao).order_by("ano", "semestre")
        if propostas.first():
            desde.append(str(propostas.first().ano)+"."+str(propostas.first().semestre))
        else:
            desde.append("---------")

        anot = Anotacao.objects.filter(organizacao=organizacao).order_by("momento").last()
        if anot:
            contato.append(anot)
        else:
            contato.append("---------")

        projetos = Projeto.objects.filter(organizacao=organizacao)
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

    return render(request, 'parceiros/organizacoes_lista.html', context)


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

    return render(request, 'parceiros/organizacao_completo.html', context=context)

@login_required
@permission_required('users.altera_professor', login_url='/projetos/')
def organizacoes_tabela(request):
    """Alocação das Organizações por semestre."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    organizacoes_pfe = []
    periodo = []

    ano = 2018    # Ano de início do PFE
    semestre = 2  # Semestre de início do PFE
    while True:
        organizacoes = []
        grupos = []
        for organizacao in Organizacao.objects.all():
            count_projetos = []
            grupos_pfe = Projeto.objects.filter(organizacao=organizacao).\
                                         filter(ano=ano).\
                                         filter(semestre=semestre)
            if grupos_pfe:
                for grupo in grupos_pfe: # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe: #len(alunos_pfe) > 0
                        count_projetos.append(grupo)
                if count_projetos:
                    organizacoes.append(organizacao)
                    grupos.append(count_projetos)
        if organizacoes: # Se não houver nenhum organização não cria entrada na lista
            organizacoes_pfe.append(zip(organizacoes, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if ((semestre == configuracao.semestre + 1) and (ano == configuracao.ano)) or \
           (ano > configuracao.ano):
            break

        # Avança um semestre
        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    anos = zip(organizacoes_pfe[::-1], periodo[::-1]) #inverti lista deixando os mais novos primeiro

    context = {
        'anos': anos,
    }

    return render(request, 'parceiros/organizacoes_tabela.html', context)

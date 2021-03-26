"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime
import dateutil.parser

from django.conf import settings

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from users.support import adianta_semestre
from users.models import PFEUser, Administrador, Parceiro, Professor, Aluno

from projetos.models import Area, Proposta, Organizacao
from projetos.models import Projeto, Configuracao, Feedback
from projetos.models import Anotacao, Conexao
from propostas.support import envia_proposta, preenche_proposta


@login_required
@permission_required("users.altera_valores", login_url='/')
def index_organizacoes(request):
    """Mostra página principal do parceiro de uma organização."""
    return render(request, 'organizacoes/index_organizacoes.html')


@login_required
@permission_required("users.altera_professor", login_url='/')
def anotacao(request, organizacao_id, anotacao_id=None):  # acertar isso para pk
    """Cria um anotação para uma organização parceira."""
    try:
        organizacao = Organizacao.objects.get(id=organizacao_id)
    except Proposta.DoesNotExist:
        return HttpResponseNotFound('<h1>Organização não encontrada!</h1>')

    if request.is_ajax() and 'texto' in request.POST:

        if anotacao_id:
            try:
                anotacao = Anotacao.objects.get(id=anotacao_id)
            except Anotacao.DoesNotExist:
                return HttpResponseNotFound('<h1>Anotação não encontrada!</h1>')
        else:
            anotacao = Anotacao.create(organizacao)

        try:
            anotacao.autor = PFEUser.objects.get(pk=request.user.pk)
        except Configuracao.DoesNotExist:
            return HttpResponse("Usuário não encontrado.", status=401)

        anotacao.texto = request.POST['texto']
        anotacao.tipo_de_retorno = int(request.POST['tipo_de_retorno'])
        anotacao.save()
        if 'data_hora' in request.POST:
            try:
                anotacao.momento = dateutil.parser\
                    .parse(request.POST['data_hora'])
            except (ValueError, OverflowError):
                anotacao.momento = datetime.datetime.now()
        anotacao.save()

        data = {
            'autor': str(anotacao.autor.get_full_name()),
            'anotacao_id': anotacao.id,
            'atualizado': True,
        }

        return JsonResponse(data)

    else:

        anotacao = None

        if anotacao_id:
            anotacao = get_object_or_404(Anotacao, id=anotacao_id)

        context = {
            'organizacao': organizacao,
            'TIPO_DE_RETORNO': Anotacao.TIPO_DE_RETORNO,
            'data_hora': datetime.datetime.now(),
            'anotacao': anotacao,
        }

        return render(request,
                      'organizacoes/anotacao_view.html',
                      context=context)


@login_required
@permission_required('users.altera_parceiro', login_url='/')
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

    propostas = Proposta.objects\
        .filter(organizacao=user.parceiro.organizacao)\
        .order_by("ano", "semestre", "titulo", )
    context = {
        'propostas': propostas,
    }
    return render(request, 'organizacoes/parceiro_propostas.html', context)


# @login_required
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

        if user.tipo_de_usuario == 1:  # alunos
            mensagem = "Você não está cadastrado como parceiro!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

        full_name = user.get_full_name()
        email_sub = user.email

        if user.tipo_de_usuario == 3:  # parceiro
            try:
                parceiro = Parceiro.objects.get(pk=request.user.parceiro.pk)
            except Parceiro.DoesNotExist:
                return HttpResponse("Parceiro não encontrado.", status=401)
            organizacao = parceiro.organizacao
            website = parceiro.organizacao.website
            endereco = parceiro.organizacao.endereco
            descricao_organizacao = parceiro.organizacao.informacoes
        elif user.tipo_de_usuario == 2:  # professor
            try:
                professor = Professor.objects.get(pk=request.user.professor.pk)
            except Professor.DoesNotExist:
                return HttpResponse("Professor não encontrado.", status=401)
        elif user.tipo_de_usuario == 4:  # admin
            try:
                administrador = Administrador.objects\
                    .get(pk=request.user.administrador.pk)
            except Administrador.DoesNotExist:
                return HttpResponse("Administrador não encontrado.",
                                    status=401)

    if request.method == 'POST':
        proposta = preenche_proposta(request, None)
        enviar = "mensagem" in request.POST  # Por e-mail se enviar
        mensagem = envia_proposta(proposta, enviar)

        resposta = "Submissão de proposta de projeto realizada"
        resposta = "com sucesso.<br>"

        if enviar:
            resposta += "Você deve receber um e-mail de confirmação"
            resposta += "nos próximos instantes.<br>"

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
        'full_name': full_name,
        'email': email_sub,
        'organizacao': organizacao,
        'website': website,
        'endereco': endereco,
        'descricao_organizacao': descricao_organizacao,
        'parceiro': parceiro,
        'professor': professor,
        'administrador': administrador,
        'contatos_tecnicos': "",
        'contatos_adm': "",
        'info_departamento': "",
        'titulo': "",
        'desc_projeto': "",
        'expectativas': "",
        'areast': areas,
        'recursos': "",
        'observacoes': "",
        'edicao': False,
        'interesses': Proposta.TIPO_INTERESSE,
        'tipo_de_interesse': 0  # Não existe na verdade
    }
    return render(request, 'organizacoes/proposta_submissao.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def organizacoes_prospect(request):
    """Exibe as organizações prospectadas e a última comunicação."""
    todas_organizacoes = Organizacao.objects.all()

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano              # Ano atual
        semestre = configuracao.semestre    # Semestre atual
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    # Vai para próximo semestre
    ano, semestre = adianta_semestre(ano, semestre)

    disponiveis = []
    submetidas = []
    contato = []
    organizacoes = []

    periodo = 60
    if request.is_ajax() and 'periodo' in request.POST:
        periodo = int(request.POST['periodo'])*30  # periodo vem em meses

    for organizacao in todas_organizacoes:
        propostas = Proposta.objects.filter(organizacao=organizacao)\
            .order_by("ano", "semestre")
        ant = Anotacao.objects.filter(organizacao=organizacao)\
            .order_by("momento").last()

        if (periodo > 366) or \
           (ant and (datetime.date.today() - ant.momento.date() <
                    datetime.timedelta(days=periodo))):

            organizacoes.append(organizacao)
            contato.append(ant)

            if configuracao.semestre == 1:
                propostas_submetidas = propostas\
                    .filter(ano__gte=configuracao.ano)\
                    .exclude(ano=configuracao.ano, semestre=1).distinct()
            else:
                propostas_submetidas = propostas\
                    .filter(ano__gt=configuracao.ano).distinct()

            submetidas.append(propostas_submetidas.count())
            disponiveis.append(propostas_submetidas.filter(disponivel=True)
                                                   .count())

    organizacoes_list = zip(organizacoes, disponiveis, submetidas, contato)
    total_organizacoes = len(organizacoes)
    total_disponiveis = sum(disponiveis)
    total_submetidas = sum(submetidas)

    context = {
        'organizacoes_list': organizacoes_list,
        'total_organizacoes': total_organizacoes,
        'total_disponiveis': total_disponiveis,
        'total_submetidas': total_submetidas,
        'ano': ano,
        'semestre': semestre,
        'filtro': "todas",
        }
    return render(request,
                  'organizacoes/organizacoes_prospectadas.html',
                  context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def organizacoes_lista(request):
    """Exibe todas as organizações que já submeteram propostas de projetos."""
    organizacoes = Organizacao.objects.all()
    fechados = []
    desde = []
    contato = []
    for organizacao in organizacoes:
        propostas = Proposta.objects.filter(organizacao=organizacao)\
            .order_by("ano", "semestre")
        if propostas.first():
            desde.append(str(propostas.first().ano) + "." +
                         str(propostas.first().semestre))
        else:
            desde.append("---------")

        anot = Anotacao.objects.filter(organizacao=organizacao)\
            .order_by("momento").last()
        if anot:
            contato.append(anot)
        else:
            contato.append("---------")

        projetos = Projeto.objects.filter(organizacao=organizacao)
        fechados.append(projetos.filter(alocacao__isnull=False)
                                .distinct().count())

    organizacoes_list = zip(organizacoes, fechados, desde, contato)
    total_organizacoes = Organizacao.objects.all().count()
    total_submetidos = Projeto.objects.all().count()
    total_fechados = Projeto.objects.filter(alocacao__isnull=False)\
        .distinct().count()

    context = {
        'organizacoes_list': organizacoes_list,
        'total_organizacoes': total_organizacoes,
        'total_submetidos': total_submetidos,
        'total_fechados': total_fechados,
        'meses3': datetime.date.today() - datetime.timedelta(days=100),
        'filtro': "todas",
        }

    return render(request, 'organizacoes/organizacoes_lista.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def organizacao_completo(request, org):  # acertar isso para pk
    """Exibe detalhes das organizações parceiras."""
    try:
        organizacao = Organizacao.objects.get(id=org)
    except Organizacao.DoesNotExist:
        return HttpResponseNotFound('<h1>Organização não encontrada!</h1>')

    context = {
        'organizacao': organizacao,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request,
                  'organizacoes/organizacao_completo.html',
                  context=context)


@login_required
@permission_required('users.altera_professor', login_url='/')
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
                for grupo in grupos_pfe:  # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:  # len(alunos_pfe) > 0
                        count_projetos.append(grupo)
                if count_projetos:
                    organizacoes.append(organizacao)
                    grupos.append(count_projetos)

        # Se não houver nenhum organização não cria entrada na lista
        if organizacoes:
            organizacoes_pfe.append(zip(organizacoes, grupos))
            periodo.append(str(ano)+"."+str(semestre))

        # Para de buscar depois do semestre atual
        if (((semestre == configuracao.semestre + 1) and
                (ano == configuracao.ano)) or
                (ano > configuracao.ano)):
            break

        # Avança um semestre
        if semestre == 2:
            semestre = 1
            ano += 1
        else:
            semestre = 2

    # inverti lista deixando os mais novos primeiro
    anos = zip(organizacoes_pfe[::-1], periodo[::-1])

    context = {
        'anos': anos,
    }

    return render(request, 'organizacoes/organizacoes_tabela.html', context)


# @login_required
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
    else:
        context = {
        }
        return render(request, 'organizacoes/projeto_feedback.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def todos_parceiros(request):
    """Exibe todas os parceiros de organizações que já submeteram projetos."""
    pareceiros = Parceiro.objects.all()

    context = {
        'pareceiros': pareceiros,
        }

    return render(request, 'organizacoes/todos_parceiros.html', context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def seleciona_conexoes(request):
    """Exibe todas os parceiros de uma organização específica."""

    # Passado o id do projeto
    projeto_id = request.GET.get('projeto', None)

    try:
        projeto = Projeto.objects.get(id=projeto_id)
    except Projeto.DoesNotExist:
        return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

    if projeto.organizacao:
        parceiros = Parceiro.objects.filter(organizacao=projeto.organizacao)
    else:
        return HttpResponseNotFound('<h1>Projeto não tem organização definida!</h1>')

    if request.method == 'POST':

        gestor_responsavel = request.POST.getlist("gestor_responsavel")
        mentor_tecnico = request.POST.getlist("mentor_tecnico")
        recursos_humanos = request.POST.getlist("recursos_humanos")

        for parceiro in parceiros:

            if str(parceiro.id) in gestor_responsavel or\
               str(parceiro.id) in mentor_tecnico or\
               str(parceiro.id) in recursos_humanos:
                (conexao, _created) = Conexao.objects.get_or_create(parceiro=parceiro,
                                                                    projeto=projeto)

                conexao.gestor_responsavel = str(parceiro.id) in gestor_responsavel
                conexao.mentor_tecnico = str(parceiro.id) in mentor_tecnico
                conexao.recursos_humanos = str(parceiro.id) in recursos_humanos
                conexao.save()

            else:
                if Conexao.objects.filter(parceiro=parceiro, projeto=projeto):
                    Conexao.objects.get(parceiro=parceiro, projeto=projeto).delete()

        return redirect('projeto_completo', projeto_id)

    context = {
        'projeto': projeto,
        'parceiros': parceiros,
        }

    return render(request, 'organizacoes/seleciona_conexoes.html', context)

@login_required
@permission_required('users.altera_professor', login_url='/')
def estrelas(request):
    """Ajax para validar avisos."""
    organizacao_id = int(request.GET.get('organizacao', None))
    estrelas = int(request.GET.get('estrelas', 0))

    try:
        organizacao = Organizacao.objects.get(id=organizacao_id)
    except Organizacao.DoesNotExist:
        return HttpResponseNotFound('<h1>Organizacao não encontrada!</h1>')
    organizacao.estrelas = estrelas
    organizacao.save()

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)
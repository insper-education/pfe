"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

from collections import OrderedDict

import datetime
import dateutil.parser

from PyPDF2 import PdfFileReader

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404

from users.support import adianta_semestre, get_edicoes
from users.models import PFEUser, Administrador, Parceiro, Professor, Aluno

from projetos.models import Area, Proposta, Organizacao
from projetos.models import Projeto, Configuracao, Feedback
from projetos.models import Anotacao, Conexao, Documento
from projetos.models import get_upload_path
from projetos.support import simple_upload

from propostas.support import envia_proposta, preenche_proposta, preenche_proposta_pdf


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def index_organizacoes(request):
    """Mostra página principal do parceiro de uma organização."""
    return render(request, 'organizacoes/index_organizacoes.html')


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def anotacao(request, organizacao_id, anotacao_id=None):  # acertar isso para pk
    """Cria um anotação para uma organização parceira."""
    organizacao = get_object_or_404(Organizacao, id=organizacao_id)

    if request.is_ajax() and 'texto' in request.POST:

        if anotacao_id:
            anotacao_obj = get_object_or_404(Anotacao, id=anotacao_id)
        else:
            anotacao_obj = Anotacao.create(organizacao)

        anotacao_obj.autor = get_object_or_404(PFEUser, pk=request.user.pk)

        anotacao_obj.texto = request.POST['texto']
        anotacao_obj.tipo_de_retorno = int(request.POST['tipo_de_retorno'])
        anotacao_obj.save()
        if 'data_hora' in request.POST:
            try:
                anotacao_obj.momento = dateutil.parser\
                    .parse(request.POST['data_hora'])
            except (ValueError, OverflowError):
                anotacao_obj.momento = datetime.datetime.now()
        anotacao_obj.save()

        data = {
            'data': anotacao_obj.momento.strftime("%d/%m/%Y"),
            'autor': str(anotacao_obj.autor.get_full_name()),
            'anotacao_id': anotacao_obj.id,
            'atualizado': True,
        }

        return JsonResponse(data)


    anotacao_obj = None

    if anotacao_id:
        anotacao_obj = get_object_or_404(Anotacao, id=anotacao_id)
        data_hora = anotacao_obj.momento
    else:
        data_hora = datetime.datetime.now()

    context = {
        'organizacao': organizacao,
        'TIPO_DE_RETORNO': Anotacao.TIPO_DE_RETORNO,
        'data_hora': data_hora,
        'anotacao': anotacao_obj,
    }

    return render(request,
                  'organizacoes/anotacao_view.html',
                  context=context)


# Adiciona um novo documento na base de dados
def cria_documento(request, organizacao):

    projeto = None
    projeto_id = request.POST.get("projeto", "")
    if projeto_id:
        projeto = Projeto.objects.get(id=projeto_id)

    data = datetime.date.today()
    if 'data' in request.POST:
        try:
            data = dateutil.parser\
                .parse(request.POST['data'])
        except (ValueError, OverflowError):
            pass

    tipo_de_documento = 255
    try:
        tipo_de_documento = request.POST.get("tipo_de_documento", "")
    except (ValueError, OverflowError):
        pass

    link = request.POST.get("link", None)
    if link:
        if link[:4] != "http":
            link = "http://" + link

        max_length = Documento._meta.get_field('link').max_length
        if len(link) > max_length - 1:
            return "<h1>Erro: Nome do link maior que " + str(max_length) + " caracteres.</h1>"

    max_length = Documento._meta.get_field('documento').max_length
    if 'arquivo' in request.FILES and len(request.FILES['arquivo'].name) > max_length - 1:
            return "<h1>Erro: Nome do arquivo maior que " + str(max_length) + " caracteres.</h1>"

    # (0, 'Português'),
    # (1, 'Inglês'),
    lingua_do_documento = 0 # Valor default
    lingua = request.POST.get("lingua_do_documento", "portugues")
    if lingua == "ingles":
        lingua_do_documento = 1

    confidencial = "confidencial" in request.POST and request.POST["confidencial"] == "true"

    # Criando documento na base de dados
    documento = Documento.create()

    documento.organizacao = organizacao
    documento.projeto = projeto
    documento.tipo_de_documento = tipo_de_documento
    documento.data = data
    documento.link = link
    documento.lingua_do_documento = lingua_do_documento
    documento.confidencial = confidencial

    # if tipo_de_documento == 25:  #(25, 'Relatório Publicado'),
    #     documento.confidencial = False
    # else:
    #     documento.confidencial = True

    if 'arquivo' in request.FILES:
        arquivo = simple_upload(request.FILES['arquivo'],
                                path=get_upload_path(documento, ""))

        documento.documento = arquivo[len(settings.MEDIA_URL):]

    documento.save()

    return None

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_documento_org(request, organizacao_id):
    """Cria um anotação para uma organização parceira."""
    organizacao = get_object_or_404(Organizacao, id=organizacao_id)

    if request.method == 'POST':
        erro = cria_documento(request, organizacao)
        if erro:
            return HttpResponseBadRequest(erro)
        return redirect('organizacao_completo', org=organizacao.id)

    documento = None
    projetos = Projeto.objects.filter(organizacao=organizacao)

    context = {
        'organizacao': organizacao,
        'TIPO_DE_DOCUMENTO': Documento.TIPO_DE_DOCUMENTO,
        'data': datetime.date.today(),
        'documento': documento,
        "projetos": projetos,
    }

    return render(request,
                  'organizacoes/documento_view.html',
                  context=context)

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_documento_proj(request, projeto_id):
    """Cria um anotação para um projeto."""
    projeto = get_object_or_404(Projeto, id=projeto_id)
    organizacao = projeto.organizacao

    if request.method == 'POST':
        erro = cria_documento(request, organizacao)
        if erro:
            return HttpResponseBadRequest(erro)
        return redirect('projeto_completo', projeto_id)

    documento = None
    projetos = Projeto.objects.filter(organizacao=organizacao)

    context = {
        "organizacao": organizacao,
        "TIPO_DE_DOCUMENTO": Documento.TIPO_DE_DOCUMENTO,
        "data": datetime.date.today(),
        "documento": documento,
        "projetos": projetos,
        "projeto": projeto,
    }

    return render(request,
                  'organizacoes/documento_view.html',
                  context=context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
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

    if hasattr(user, 'parceiro'):
        propostas = Proposta.objects\
            .filter(organizacao=user.parceiro.organizacao)\
            .order_by("ano", "semestre", "titulo", )
    else:
        propostas = None

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

    configuracao = get_object_or_404(Configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

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
            parceiro = get_object_or_404(Parceiro, pk=request.user.parceiro.pk)
            organizacao = parceiro.organizacao
            website = parceiro.organizacao.website
            endereco = parceiro.organizacao.endereco
            descricao_organizacao = parceiro.organizacao.informacoes
        elif user.tipo_de_usuario == 2:  # professor
            professor = get_object_or_404(Professor, pk=request.user.professor.pk)
        elif user.tipo_de_usuario == 4:  # admin
            administrador = get_object_or_404(Administrador, pk=request.user.administrador.pk)

    if request.method == 'POST':
        proposta = preenche_proposta(request, None)
        enviar = "mensagem" in request.POST  # Por e-mail se enviar
        mensagem = envia_proposta(proposta, enviar)

        resposta = "Submissão de proposta de projeto realizada "
        resposta += "com sucesso.<br>"

        if enviar:
            resposta += "Você deve receber um e-mail de confirmação "
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

    interesses = [
        ["aprimorar", Proposta.TIPO_INTERESSE[0][1], False],
        ["realizar", Proposta.TIPO_INTERESSE[1][1], False],
        ["iniciar", Proposta.TIPO_INTERESSE[2][1], False],
        ["identificar", Proposta.TIPO_INTERESSE[3][1], False],
        ["mentorar", Proposta.TIPO_INTERESSE[4][1], False],
    ]

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
        'interesses': interesses,
        'ano_semestre': str(ano)+"."+str(semestre),
    }
    return render(request, 'organizacoes/proposta_submissao.html', context)


def _getFields(obj, tree=None, retval=None, fileobj=None):
    """
    Extracts field data if this PDF contains interactive form fields.

    The *tree* and *retval* parameters are for recursive use.

    :param fileobj: A file object (usually a text file) to write
        a report to on all interactive form fields found.
    :return: A dictionary where each key is a field name, and each
        value is a :class:`Field<PyPDF2.generic.Field>` object. By
        default, the mapping name is used for keys.
    :rtype: dict, or ``None`` if form data could not be located.
    """
    fieldAttributes = {'/FT': 'Field Type', '/Parent': 'Parent', '/T': 'Field Name', '/TU': 'Alternate Field Name',
                       '/TM': 'Mapping Name', '/Ff': 'Field Flags', '/V': 'Value', '/DV': 'Default Value'}
    if retval is None:
        retval = OrderedDict()
        catalog = obj.trailer["/Root"]
        # get the AcroForm tree
        if "/AcroForm" in catalog:
            tree = catalog["/AcroForm"]
        else:
            return None
    if tree is None:
        return retval

    obj._checkKids(tree, retval, fileobj)
    for attr in fieldAttributes:
        if attr in tree:
            # Tree is a field
            obj._buildField(tree, retval, fileobj, fieldAttributes)
            break

    if "/Fields" in tree:
        fields = tree["/Fields"]
        for f in fields:
            field = f.getObject()
            obj._buildField(field, retval, fileobj, fieldAttributes)

    return retval


def get_form_fields(infile):
    infile = PdfFileReader(open(infile, 'rb'))
    fields = _getFields(infile)
    return fields


# @login_required
def carrega_proposta(request):
    """Página para carregar Proposta de Projetos em PDF."""
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        user = None

    configuracao = get_object_or_404(Configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    full_name = ""
    email_sub = ""
    parceiro = False

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

        parceiro = user.tipo_de_usuario == 3  # parceiro

    if request.method == 'POST':

        resposta = ""

        if 'arquivo' in request.FILES:
            arquivo = simple_upload(request.FILES['arquivo'],
                                    path=get_upload_path(None, ""))

            fields = get_form_fields(arquivo[1:])

            fields["nome"] = request.POST.get("nome", "").strip()
            fields["email"] = request.POST.get("email", "").strip()

            proposta, erros = preenche_proposta_pdf(fields, None)

            enviar = "mensagem" in request.POST  # Por e-mail se enviar
            mensagem = envia_proposta(proposta, enviar)

            if erros:
                resposta += "ERROS:<br><b style='color:red;font-size:40px'>"
                resposta += erros + "<br><br>"
                resposta += "</b>"

            resposta += "Submissão de proposta de projeto realizada "
            resposta += "com sucesso.<br>"

            if enviar:
                resposta += "Você deve receber um e-mail de confirmação "
                resposta += "nos próximos instantes.<br><br>"

        else:
            mensagem = "Arquivo não identificado"

        resposta += mensagem
        context = {
            "voltar": True,
            "mensagem": resposta,
        }
        return render(request, 'generic.html', context=context)

    context = {
        'full_name': full_name,
        'email': email_sub,
        "parceiro": parceiro,
        'ano_semestre': str(ano)+"."+str(semestre),
    }
    return render(request, 'organizacoes/carrega_proposta.html', context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_prospect(request):
    """Exibe as organizações prospectadas e a última comunicação."""
    todas_organizacoes = Organizacao.objects.all()
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano              # Ano atual
    semestre = configuracao.semestre    # Semestre atual

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
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_lista(request):
    """Exibe todas as organizações que já submeteram propostas de projetos."""
    organizacoes = Organizacao.objects.all()
    fechados = []
    desde = []
    contato = []
    grupos = []
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

        projetos = Projeto.objects.filter(organizacao=organizacao).filter(alocacao__isnull=False).distinct()
        fechados.append(projetos.count())

        tipo_estudantes = ""
        for projeto in projetos:
            estudantes = Aluno.objects.filter(alocacao__projeto=projeto)
            tipos = ""
            for estudante in estudantes:
                tipos += estudante.curso2.sigla_curta
            tipo_estudantes += "["+tipos+"]"
        grupos.append(tipo_estudantes)


    organizacoes_list = zip(organizacoes, fechados, desde, contato, grupos)
    total_organizacoes = Organizacao.objects.all().count()
    total_submetidos = Proposta.objects.all().count()
    total_fechados = Projeto.objects.filter(alocacao__isnull=False)\
        .distinct().count()

    #cabecalhos = ["Organização", "Último <br>Contato", "Parceira <br>Desde", "Propostas <br>Enviadas", "Projetos <br>Fechados", "Grupos de <br>Estudantes", ]
    cabecalhos = ["Company", "Last <br>Contact", "Partner <br>Since", "Submitted <br>Proposals", "Closed <br>Projects", "Group of <br>Students", ]

    #titulo = "Organizações Parceiras"
    titulo = "Partnership Companies"

    context = {
        'organizacoes_list': organizacoes_list,
        'total_organizacoes': total_organizacoes,
        'total_submetidos': total_submetidos,
        'total_fechados': total_fechados,
        'meses3': datetime.date.today() - datetime.timedelta(days=100),
        'filtro': "todas",
        "grupos": grupos,
        "cabecalhos": cabecalhos,
        "titulo": titulo,
    }

    return render(request, 'organizacoes/organizacoes_lista.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacao_completo(request, org):  # acertar isso para pk
    """Exibe detalhes das organizações parceiras."""
    organizacao = get_object_or_404(Organizacao, id=org)

    context = {
        'organizacao': organizacao,
        'MEDIA_URL': settings.MEDIA_URL,
    }

    return render(request,
                  'organizacoes/organizacao_completo.html',
                  context=context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def organizacoes_tabela(request):
    """Alocação das Organizações por semestre."""
    configuracao = get_object_or_404(Configuracao)

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
@transaction.atomic
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

        try:
            nps = int(request.POST.get("nps", "-1"))
            if nps < 0:
                feedback.nps = None
            else:
                feedback.nps = nps
        except (ValueError, OverflowError):
            return HttpResponseNotFound('<h1>Erro com valor NPS!</h1>')

        feedback.save()

        mensagem = "Feedback recebido, obrigado!"
        context = {
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    context = {
    }
    return render(request, 'organizacoes/projeto_feedback.html', context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def todos_parceiros(request):
    """Exibe todas os parceiros de organizações que já submeteram projetos."""
    cabecalhos = ["Nome", "Cargo", "Organização", "e-mail", "telefone", "papel", ]

    parceiros = None
    edicao = "todas"
    if request.is_ajax():
        if 'edicao' in request.POST:
            edicao = request.POST['edicao']
            parceiros = Parceiro.objects.all()

            if edicao not in ("todas",):
                ano = int(edicao.split(".")[0])
                semestre = int(edicao.split(".")[1])
                conexoes = Conexao.objects.filter(projeto__ano=ano,
                    projeto__semestre=semestre).values_list("parceiro", flat=True)
                parceiros = parceiros.filter(id__in=conexoes)

    edicoes, _, _ = get_edicoes(Projeto)    
    context = {
        "parceiros": parceiros,
        "cabecalhos": cabecalhos,
        "titulo": "Parceiros Profissionais",
        "edicoes": edicoes,
        "edicao": edicao,
        }

    return render(request, 'organizacoes/todos_parceiros.html', context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def seleciona_conexoes(request):
    """Exibe todas os parceiros de uma organização específica."""
    # Passado o id do projeto
    projeto_id = request.GET.get('projeto', None)

    projeto = get_object_or_404(Projeto, id=projeto_id)

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

        colaboracao = request.POST.get('colaboracao', None)
        if colaboracao and colaboracao != "":
            parceiro = Parceiro.objects.get(id=colaboracao)
            (conexao, _created) = Conexao.objects.get_or_create(parceiro=parceiro,
                                                                projeto=projeto)
            conexao.colaboracao = True
            conexao.save()
        else:
            conexoes_colab = Conexao.objects.filter(colaboracao=True,
                                                    projeto=projeto)

            if conexoes_colab.exists():  # Caso já exista uma conexão
                for conexao in conexoes_colab:
                    conexao.delete()  # apagar

        return redirect('projeto_completo', projeto_id)


    todos_parceiros = Parceiro.objects.all()

    colaboradores = None
    cooperacoes = Conexao.objects.filter(projeto=projeto, colaboracao=True)
    if cooperacoes:
        colaboradores = cooperacoes.last().parceiro

    context = {
        "projeto": projeto,
        "parceiros": parceiros,
        "todos_parceiros": todos_parceiros,
        "colaboradores": colaboradores,
        }

    return render(request, 'organizacoes/seleciona_conexoes.html', context)

@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def estrelas(request):
    """Ajax para validar estrelas de interesse."""
    organizacao_id = int(request.GET.get('organizacao', None))
    numero_estrelas = int(request.GET.get('estrelas', 0))

    organizacao = get_object_or_404(Organizacao, id=organizacao_id)
    organizacao.estrelas = numero_estrelas
    organizacao.save()

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)

@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def areas(request):
    """Ajax para validar area da organização."""
    organizacao_id = int(request.GET.get('organizacao', None))
    curso = request.GET.get('curso', "")
    situacao = True if (request.GET.get('situacao', "") == "true") else False
    organizacao = get_object_or_404(Organizacao, id=organizacao_id)

    if curso == "C":
        organizacao.area_computacao = situacao
    elif curso == "X":
        organizacao.area_mecatronica = situacao
    elif curso == "M":
        organizacao.area_mecanica = situacao

    organizacao.save()

    data = {
        'atualizado': True,
    }

    return JsonResponse(data)

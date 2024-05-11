"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 14 de Dezembro de 2020
"""

import datetime
import dateutil.parser
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseNotFound, JsonResponse, HttpResponseBadRequest
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from organizacoes.support import get_form_fields, cria_documento

from administracao.support import limpa_texto, usuario_sem_acesso

from users.support import adianta_semestre, get_edicoes
from users.models import PFEUser, Administrador, Parceiro, Professor, Aluno, Alocacao

from projetos.models import Area, Proposta, Organizacao
from projetos.models import Projeto, Configuracao, Feedback
from projetos.models import Anotacao, Conexao, Documento
from projetos.support import get_upload_path, simple_upload

from propostas.support import envia_proposta, preenche_proposta, preenche_proposta_pdf

from operacional.models import Curso
from documentos.models import TipoDocumento

@login_required
@permission_required("projetos.add_proposta", raise_exception=True)
def index_organizacoes(request):
    """Mostra página principal do parceiro de uma organização."""
    contex = {
        "titulo": "Área dos Parceiros",
    }
    return render(request, "organizacoes/index_organizacoes.html", context=contex)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def anotacao(request, organizacao_id=None, anotacao_id=None):  # acertar isso para pk
    """Cria um anotação para uma organização parceira."""
    organizacao = get_object_or_404(Organizacao, id=organizacao_id) if organizacao_id else None

    if request.is_ajax() and "texto" in request.POST:

        if anotacao_id:
            anotacao_obj = get_object_or_404(Anotacao, id=anotacao_id)
        else:
            if not organizacao_id and "organizacao_id" in request.POST:
                organizacao_id = request.POST["organizacao_id"]
                organizacao = get_object_or_404(Organizacao, id=organizacao_id)
            anotacao_obj = Anotacao.create(organizacao)

        anotacao_obj.autor = request.user

        anotacao_obj.texto = request.POST["texto"]
        anotacao_obj.tipo_de_retorno = int(request.POST["tipo_de_retorno"])
        anotacao_obj.save()
        if "data_hora" in request.POST:
            try:
                anotacao_obj.momento = dateutil.parser\
                    .parse(request.POST["data_hora"])
            except (ValueError, OverflowError):
                anotacao_obj.momento = datetime.datetime.now()
        anotacao_obj.save()

        data = {
            "data": anotacao_obj.momento.strftime("%d/%m/%y"),
            "data_full": anotacao_obj.momento.strftime("%d/%m/%Y"),
            "autor_nome": str(anotacao_obj.autor.get_full_name().split(' ', 1)[0]),
            "autor_sobrenome": str(anotacao_obj.autor.get_full_name().split(' ', 1)[1]),
            "anotacao_id": anotacao_obj.id,
            "atualizado": True,
        }

        return JsonResponse(data)


    anotacao_obj = None

    if anotacao_id:
        anotacao_obj = get_object_or_404(Anotacao, id=anotacao_id)
        data_hora = anotacao_obj.momento
    else:
        data_hora = datetime.datetime.now()

    context = {
        "organizacao": organizacao,
        "TIPO_DE_RETORNO": sorted(Anotacao.TIPO_DE_RETORNO, key=lambda x: (x[2] == "", x[2], x[1])),
        "data_hora": data_hora,
        "anotacao": anotacao_obj,
        "organizacoes": Organizacao.objects.all(),
    }

    return render(request, "organizacoes/anotacao_view.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_documento(request, organizacao_id=None, projeto_id=None, tipo_nome=None, documento_id=None):
    """Cria um documento."""
    
    configuracao = get_object_or_404(Configuracao)
    organizacao = Organizacao.objects.filter(id=organizacao_id).last()
    projeto = Projeto.objects.filter(id=projeto_id).last()

    if organizacao_id and (not organizacao):
        return HttpResponseNotFound("<h1>Organização não encontrada!</h1>")

    if projeto_id and (not projeto):
        return HttpResponseNotFound("<h1>Projeto não encontrado!</h1>")
    
    tipo = None
    if tipo_nome:
        tipo = TipoDocumento.objects.get(sigla=tipo_nome)
        if request.user.tipo_de_usuario not in json.loads(tipo.gravar):  # Verifica se usuário tem privilégios para gravar tipo de arquivo
            return HttpResponse("<h1>Sem privilégios para gravar tipo de arquivo!</h1>", status=401)

    if request.is_ajax() and request.method == "POST":
        erro = cria_documento(request)
        if erro:
           return HttpResponseBadRequest(erro)
        return JsonResponse({"atualizado": True,})

    if organizacao:
        projetos = Projeto.objects.filter(organizacao=organizacao)
    else:
        projetos = Projeto.objects.all()

    if tipo_nome and (not organizacao_id) and (not projeto_id):
        adiciona = "adiciona_documento_tipo"
    else:
        adiciona = "adiciona_documento"

    context = {
        "organizacao": organizacao,
        "tipos_documentos": TipoDocumento.objects.all(),
        "data": datetime.datetime.now(),
        "Documento": Documento,
        "projetos": projetos,
        "projeto": projeto,
        "tipo": tipo,
        "organizacoes": Organizacao.objects.all(),
        "documentos": Documento.objects.filter(id=documento_id),
        "documento_id": documento_id,
        "configuracao": configuracao,
        "travado": False,
        "adiciona": adiciona,
    }
    
    return render(request, "organizacoes/documento_view.html", context=context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_documento_tipo(request, tipo_nome=None):
    """Cria um documento com tipo."""
    return adiciona_documento(request, organizacao_id=None, projeto_id=None, tipo_nome=tipo_nome)


@login_required
@transaction.atomic
def adiciona_documento_estudante(request, tipo_nome=None, documento_id=None):
    """Cria um documento pelos estudantes somente."""
    usuario_sem_acesso(request, (1,)) # Soh Estudantes

    configuracao = get_object_or_404(Configuracao)

    alocacao = Alocacao.objects.filter(aluno=request.user.aluno, projeto__ano=configuracao.ano, projeto__semestre=configuracao.semestre).last()
    projeto = alocacao.projeto
    organizacao = projeto.organizacao

    if not organizacao:
        return HttpResponseNotFound("<h1>Organização não encontrada!</h1>")

    if not projeto:
        return HttpResponseNotFound("<h1>Projeto não encontrado!</h1>")
    
    if tipo_nome:
        tipo = TipoDocumento.objects.get(sigla=tipo_nome)
        if request.user.tipo_de_usuario not in json.loads(tipo.gravar):  # Verifica se usuário tem privilégios para gravar tipo de arquivo
            return HttpResponse("<h1>Sem privilégios para gravar tipo de arquivo!</h1>", status=401)
    else:
        return HttpResponseNotFound("<h1>Tipo de submissão não identificada!</h1>")

    if request.is_ajax() and request.method == "POST":
        erro = cria_documento(request, forca_confidencial=True)
        if erro:
           return HttpResponseBadRequest(erro)
        return JsonResponse({"atualizado": True})

    context = {
        "organizacao": organizacao,
        "data": datetime.datetime.now(),
        "Documento": Documento,
        "projeto": projeto,
        "tipo": tipo,
        "documentos": Documento.objects.filter(id=documento_id),
        "documento_id": documento_id,
        "configuracao": configuracao,
        "travado": True,
        "adiciona": "adiciona_documento_estudante",
    }

    return render(request, "organizacoes/documento_view.html", context=context)


@login_required
@permission_required("projetos.add_proposta", raise_exception=True)
def parceiro_propostas(request):
    """Lista todas as propostas de projetos."""
    user = request.user
    if user.tipo_de_usuario != 3 and user.tipo_de_usuario != 4:  # Não é Parceiro ou Admin
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    if hasattr(user, "parceiro"):
        propostas = Proposta.objects\
            .filter(organizacao=user.parceiro.organizacao)\
            .order_by("ano", "semestre", "titulo", )
    else:
        propostas = None

    context = {
        "titulo": "Propostas de Projetos Submetidas",
        "propostas": propostas,
        "organizacao": user.parceiro.organizacao,
    }
    return render(request, "organizacoes/parceiro_propostas.html", context)


@login_required
@permission_required("projetos.add_proposta", raise_exception=True)
def parceiro_projetos(request):
    """Lista todas as propostas de projetos."""
    user = request.user
    if user.tipo_de_usuario != 3 and user.tipo_de_usuario != 4:  # Não é Parceiro ou Admin
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    if hasattr(user, "parceiro"):
        projetos = Projeto.objects\
            .filter(proposta__organizacao=user.parceiro.organizacao).order_by("ano", "semestre")
    else:
        projetos = projetos

    context = {
        "titulo": "Lista de Projetos",
        "projetos": projetos,
        "organizacao": user.parceiro.organizacao,
    }
    return render(request, "organizacoes/parceiro_projetos.html", context)


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
            return render(request, "generic.html", context=context)

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

    if request.method == "POST":

        proposta = preenche_proposta(request, None)

        if "arquivo" in request.FILES:
            arquivo = simple_upload(request.FILES["arquivo"],
                                    path=get_upload_path(proposta, ""))
            proposta.anexo = arquivo[len(settings.MEDIA_URL):]
            proposta.save()

        # Só faz essa parte se usuário logado e professor ou administrador:
        if request.user.is_authenticated:
            if request.user.tipo_de_usuario == 2 or request.user.tipo_de_usuario == 4:
                proposta.internacional = True if request.POST.get("internacional", None) else False
                proposta.intercambio = True if request.POST.get("intercambio", None) else False
                colaboracao_id = request.POST.get("colaboracao", None)
                if colaboracao_id:
                    proposta.colaboracao = Organizacao.objects.filter(pk=colaboracao_id).last()
                proposta.save()

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
        return render(request, "generic.html", context=context)

    areas = Area.objects.filter(ativa=True)

    organizacao_str = request.GET.get("organizacao", None)
    if organizacao_str:
        try:
            organizacao_id = int(organizacao_str)
            organizacao = Organizacao.objects.get(id=organizacao_id)
        except (ValueError, Organizacao.DoesNotExist):
            return HttpResponseNotFound("<h1>Organização não encontrado!</h1>")

    interesses = [
        ["aprimorar", Proposta.TIPO_INTERESSE[0][1], False],
        ["realizar", Proposta.TIPO_INTERESSE[1][1], False],
        ["iniciar", Proposta.TIPO_INTERESSE[2][1], False],
        ["identificar", Proposta.TIPO_INTERESSE[3][1], False],
        ["mentorar", Proposta.TIPO_INTERESSE[4][1], False],
    ]

    context = {
        "titulo": "Submissão de Proposta de Projeto",
        "full_name": full_name,
        "email": email_sub,
        "organizacao": organizacao,
        "website": website,
        "endereco": endereco,
        "descricao_organizacao": descricao_organizacao,
        "parceiro": parceiro,
        "professor": professor,
        "administrador": administrador,
        "contatos_tecnicos": "",
        "contatos_adm": "",
        "info_departamento": "",
        "titulo_prop": "",
        "desc_projeto": "",
        "expectativas": "",
        "areast": areas,
        "recursos": "",
        "observacoes": "",
        "edicao": False,
        "interesses": interesses,
        "ano_semestre": str(ano)+"."+str(semestre),
        "configuracao": configuracao,
        "organizacoes": Organizacao.objects.all(),
    }
    return render(request, "organizacoes/proposta_submissao.html", context)


# @login_required
def carrega_proposta(request):
    """Página para carregar Proposta de Projetos em PDF."""
    configuracao = get_object_or_404(Configuracao)
    ano, semestre = adianta_semestre(configuracao.ano, configuracao.semestre)

    full_name = ""
    email_sub = ""
    parceiro = False

    if request.user and request.user.is_authenticated:

        if request.user.tipo_de_usuario == 1:  # alunos
            mensagem = "Você não está cadastrado como parceiro!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, "generic.html", context=context)

        full_name = request.user.get_full_name()
        email_sub = request.user.email

        parceiro = request.user.tipo_de_usuario == 3  # parceiro

    if request.method == "POST":

        resposta = ""

        if "arquivo" in request.FILES:
            arquivo = simple_upload(request.FILES["arquivo"],
                                    path=get_upload_path(None, ""))

            fields = get_form_fields(arquivo[1:])
            if fields is None:
                mensagem = "<b>ERRO:</b> Arquivo formulário não reconhecido"
                context = {
                    "voltar": True,
                    "mensagem": mensagem,
                }
                return render(request, "generic.html", context=context)

            fields["nome"] = limpa_texto(request.POST.get("nome", "").strip())
            fields["email"] = limpa_texto(request.POST.get("email", "").strip())

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
        return render(request, "generic.html", context=context)

    context = {
        "titulo": "Carrega Proposta de Projeto em PDF",
        "full_name": full_name,
        "email": email_sub,
        "parceiro": parceiro,
        "ano_semestre": str(ano)+'.'+str(semestre),
    }
    return render(request, "organizacoes/carrega_proposta.html", context)

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

    periodo = 90
    if request.is_ajax() and "periodo" in request.POST:
        periodo = int(request.POST["periodo"])*30  # periodo vem em meses

    for organizacao in todas_organizacoes:
        propostas = Proposta.objects.filter(organizacao=organizacao)\
            .order_by("ano", "semestre")
        ant = Anotacao.objects.filter(organizacao=organizacao)\
            .order_by("momento").last()

        if (periodo > 366) or \
           (ant and (datetime.date.today() - ant.momento.date() <
                     datetime.timedelta(days=periodo))):

            organizacoes.append(organizacao)
            contato.append(ant) # None se não houver anotação
            
            if configuracao.semestre == 1:
                propostas_submetidas = propostas\
                    .filter(ano__gte=configuracao.ano)\
                    .exclude(ano=configuracao.ano, semestre=1).distinct()
            else:
                propostas_submetidas = propostas\
                    .filter(ano__gt=configuracao.ano).distinct()

            submetidas.append(propostas_submetidas.count())
            disponiveis.append(propostas_submetidas.filter(disponivel=True).count())

    organizacoes_list = zip(organizacoes, disponiveis, submetidas, contato)

    # No final jogo para 2 (com proposta submetida) se houver proposta submetida, mesmo que a anotação diga diferente
    organizacoes_list = sorted(organizacoes_list, key=lambda x: (255 if x[3] is None else ( 2 if (x[3].tipo_de_retorno < 2 and x[2] > 0) else x[3].tipo_de_retorno ) ))

    total_organizacoes = len(organizacoes)
    total_disponiveis = sum(disponiveis)
    total_submetidas = sum(submetidas)

    TIPO_DE_RETORNO = sorted(Anotacao.TIPO_DE_RETORNO, key=lambda x: (x[2] == "", x[2], x[1]))

    cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")
    necessarios = []
    estudantes = Aluno.objects.filter(anoPFE=ano, semestrePFE=semestre)
    for curso in cursos:
        necessarios.append(estudantes.filter(curso2=curso).count()/4)  # grupos de 4 estudantes

    context = {
        "titulo": "Prospecção de Organizações",
        "organizacoes_list": organizacoes_list,
        "total_organizacoes": total_organizacoes,
        "total_disponiveis": total_disponiveis,
        "total_submetidas": total_submetidas,
        "ano": ano,
        "semestre": semestre,
        "filtro": "todas",
        "cursos": cursos,
        "necessarios": necessarios,
        "TIPO_DE_RETORNO": TIPO_DE_RETORNO,
        }
    return render(request, "organizacoes/organizacoes_prospectadas.html", context)


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
            tipo_estudantes += "["+"|".join(tipos)+"] "
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
        "organizacoes_list": organizacoes_list,
        "total_organizacoes": total_organizacoes,
        "total_submetidos": total_submetidos,
        "total_fechados": total_fechados,
        "meses3": datetime.date.today() - datetime.timedelta(days=100),
        "filtro": "todas",
        "grupos": grupos,
        "cabecalhos": cabecalhos,
        "titulo": titulo,
    }

    return render(request, "organizacoes/organizacoes_lista.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacao_completo(request, org=None):  # acertar isso para pk
    """Exibe detalhes das organizações parceiras."""
    if not org:
        return HttpResponseNotFound("<h1>Organização não encontrada!</h1>")
    organizacao = get_object_or_404(Organizacao, id=org)
    context = {
        "titulo": organizacao.nome,
        "organizacao": organizacao,
        "cursos": Curso.objects.all().order_by("id"),
    }
    return render(request, "organizacoes/organizacao_completo.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
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

    context = {"anos": anos,}

    return render(request, "organizacoes/organizacoes_tabela.html", context)


# @login_required
@transaction.atomic
def projeto_feedback(request):
    """Para Feedback das Organizações Parceiras."""
    if request.method == "POST":
        feedback = Feedback.create()
        feedback.nome = request.POST.get("nome", "")
        feedback.email = request.POST.get("email", "")
        feedback.empresa = request.POST.get("empresa", "")
        feedback.tecnico = request.POST.get("tecnico", "")
        feedback.comunicacao = request.POST.get("comunicacao", "")
        feedback.organizacao = request.POST.get("organizacao", "")
        feedback.outros = request.POST.get("outros", "")

        try:
            nps = request.POST.get("nps", None)            
            feedback.nps = int(nps) if nps else None
        except (ValueError, OverflowError):
            return HttpResponseNotFound("<h1>Erro com valor NPS!</h1>")

        feedback.save()

        context = {"mensagem": "Feedback recebido, obrigado!",}
        return render(request, "generic.html", context=context)

    context = {
        "titulo": "Formulário de Feedback das Organizações Parceiras",
    }
    return render(request, "organizacoes/projeto_feedback.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def todos_parceiros(request):
    """Exibe todas os parceiros de organizações que já submeteram projetos."""
    parceiros = None
    edicao = "todas"
    if request.is_ajax():
        if "edicao" in request.POST:
            edicao = request.POST["edicao"]
            parceiros = Parceiro.objects.all()

            if edicao not in ("todas",):
                ano, semestre = map(int, edicao.split('.'))
                conexoes = Conexao.objects.filter(projeto__ano=ano,
                    projeto__semestre=semestre).values_list("parceiro", flat=True)
                parceiros = parceiros.filter(id__in=conexoes)

    edicoes, _, _ = get_edicoes(Projeto)    
    context = {
        "parceiros": parceiros,
        "cabecalhos": ["Nome", "Cargo", "Organização", "e-mail", "telefone", "papel", ],
        "titulo": "Parceiros Profissionais",
        "edicoes": edicoes,
        "edicao": edicao,
        "Conexao": Conexao,
        }

    return render(request, "organizacoes/todos_parceiros.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def todos_usuarios(request):
    """Exibe usuários."""
    usuarios = []
    if request.is_ajax():                
        nome = request.POST.get("nome", None)
        if nome:
            usuarios = PFEUser.objects.filter(Q(first_name__icontains=nome) | Q(last_name__icontains=nome))

    context = {
        "usuarios": usuarios,
        "cabecalhos": ["Nome", "e-mail", "Tipo" ],
        "titulo": "Todos os Usuários",
        }

    return render(request, "organizacoes/todos_usuarios.html", context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def seleciona_conexoes(request):
    """Exibe todas os parceiros de uma organização específica."""
    # Passado o id do projeto
    projeto_id = request.GET.get("projeto", None)
    projeto = get_object_or_404(Projeto, id=projeto_id)

    if request.is_ajax():

        parceiro_id = request.POST["parceiro_id"]
        parceiro = get_object_or_404(Parceiro, id=parceiro_id)

        (conexao, _) = Conexao.objects.get_or_create(parceiro=parceiro,
                                                            projeto=projeto)

        if "gestor_responsavel" == request.POST["tipo"]:
            conexao.gestor_responsavel = (request.POST["checked"] == "true")
        elif "mentor_tecnico" == request.POST["tipo"]:
            conexao.mentor_tecnico = (request.POST["checked"] == "true")
        elif "recursos_humanos" == request.POST["tipo"]:
            conexao.recursos_humanos = (request.POST["checked"] == "true")
        else:
            return HttpResponseNotFound("<h1>Tipo de conexão não encontrado!</h1>")

        if (not conexao.gestor_responsavel) and \
           (not conexao.mentor_tecnico) and \
           (not conexao.recursos_humanos):
            conexao.delete()
        else:
            conexao.save()

        return JsonResponse({"atualizado": True,})

    if projeto.organizacao:
        parceiros = Parceiro.objects.filter(organizacao=projeto.organizacao)
    else:
        return HttpResponseNotFound("<h1>Projeto não tem organização definida!</h1>")

    if request.method == "POST":

        gestor_responsavel = request.POST.getlist("gestor_responsavel")
        mentor_tecnico = request.POST.getlist("mentor_tecnico")
        recursos_humanos = request.POST.getlist("recursos_humanos")

        for parceiro in parceiros:

            if str(parceiro.id) in gestor_responsavel or\
               str(parceiro.id) in mentor_tecnico or\
               str(parceiro.id) in recursos_humanos:
                (conexao, _) = Conexao.objects.get_or_create(parceiro=parceiro,
                                                                    projeto=projeto)

                conexao.gestor_responsavel = str(parceiro.id) in gestor_responsavel
                conexao.mentor_tecnico = str(parceiro.id) in mentor_tecnico
                conexao.recursos_humanos = str(parceiro.id) in recursos_humanos
                conexao.save()

            else:
                if Conexao.objects.filter(parceiro=parceiro, projeto=projeto):
                    Conexao.objects.get(parceiro=parceiro, projeto=projeto).delete()

        colaboracao = request.POST.get("colaboracao", None)
        if colaboracao and colaboracao != "":
            parceiro = Parceiro.objects.get(id=colaboracao)
            (conexao, _) = Conexao.objects.get_or_create(parceiro=parceiro,
                                                                projeto=projeto)
            conexao.colaboracao = True
            conexao.save()
        else:
            conexoes_colab = Conexao.objects.filter(colaboracao=True,
                                                    projeto=projeto)

            if conexoes_colab.exists():  # Caso já exista uma conexão
                for conexao in conexoes_colab:
                    conexao.delete()  # apagar

        return redirect("projeto_completo", projeto_id)

    cooperacoes = Conexao.objects.filter(projeto=projeto, colaboracao=True)
    colaboradores = cooperacoes.last().parceiro if cooperacoes else None

    context = {
        "projeto": projeto,
        "parceiros": parceiros,
        "todos_parceiros": Parceiro.objects.all(),
        "colaboradores": colaboradores,
        "Conexao": Conexao,
        }

    return render(request, "organizacoes/seleciona_conexoes.html", context)

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def estrelas(request):
    """Ajax para validar estrelas de interesse."""
    organizacao_id = int(request.GET.get("organizacao", None))
    organizacao = get_object_or_404(Organizacao, id=organizacao_id)
    organizacao.estrelas = int(request.GET.get("estrelas", 0))  # numero_estrelas
    organizacao.save()

    return JsonResponse({"atualizado": True,})

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def areas(request):
    """Ajax para validar area da organização."""
    organizacao_id = int(request.GET.get("organizacao", None))
    curso = request.GET.get("curso", "")
    situacao = True if (request.GET.get("situacao", "") == "true") else False
    organizacao = get_object_or_404(Organizacao, id=organizacao_id)

    if situacao:
        organizacao.area_curso.add(Curso.objects.get(sigla_curta=curso))
    else:
        organizacao.area_curso.remove(Curso.objects.get(sigla_curta=curso))
    
    organizacao.save()

    return JsonResponse({"atualizado": True,})

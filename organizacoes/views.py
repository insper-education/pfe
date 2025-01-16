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
from django.db.models import Prefetch

from organizacoes.support import get_form_fields, cria_documento

from administracao.support import limpa_texto, usuario_sem_acesso

from users.support import adianta_semestre, get_edicoes
from users.models import PFEUser, Administrador, Parceiro, Professor, Aluno, Alocacao

from projetos.models import Area, Proposta, Organizacao
from projetos.models import Projeto, Configuracao, Feedback
from projetos.models import Anotacao, Conexao, Documento, TipoRetorno
from projetos.support import get_upload_path, simple_upload

from propostas.support import envia_proposta, preenche_proposta, preenche_proposta_pdf

from operacional.models import Curso
from documentos.models import TipoDocumento

# Liberado para Parceiros poderem enviar proposta de projeto mesmo se não logados
# @login_required
# @permission_required("projetos.add_proposta", raise_exception=True)
def index_organizacoes(request):
    """Mostra página principal do parceiro de uma organização."""
    contex = {
        "titulo": {"pt": "Área dos Parceiros", "en": "Partners Area"},
    }
    if "/organizacoes/organizacoes" in request.path:
        return render(request, "organizacoes/organizacoes.html", context=contex)
    else:
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
        anotacao_obj.tipo_retorno = TipoRetorno.objects.get(id=request.POST["tipo_retorno"])
        
        if "data_hora" in request.POST:
            try:
                anotacao_obj.momento = dateutil.parser.parse(request.POST["data_hora"])
            except (ValueError, OverflowError):
                anotacao_obj.momento = datetime.datetime.now()
        anotacao_obj.save()

        data = {
            "data": anotacao_obj.momento.strftime("%d/%m/%y"),
            "data_full": anotacao_obj.momento.strftime("%d/%m/%Y"),
            "autor_nome": anotacao_obj.autor.first_name,
            "autor_sobrenome": anotacao_obj.autor.last_name,
            "anotacao_id": anotacao_obj.id,
            "atualizado": True,
        }

        return JsonResponse(data)

    anotacao_obj = get_object_or_404(Anotacao, id=anotacao_id) if anotacao_id else None

    context = {
        "organizacao": organizacao,
        "tipo_retorno": TipoRetorno.objects.all(),
        "anotacao": anotacao_obj,
        "data_hora": anotacao_obj.momento if anotacao_obj else datetime.datetime.now(),
        "organizacoes": Organizacao.objects.all(),
    }

    return render(request, "organizacoes/anotacao_view.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_documento(request, organizacao_id=None, projeto_id=None, tipo_nome=None, documento_id=None, adiciona=None):
    """Cria um documento."""

    # Recupera o documento se existir e define o autor para o documento
    documento = get_object_or_404(Documento, id=documento_id) if documento_id else None
    usuario = documento.usuario if documento else request.user

    if request.is_ajax() and request.method == "POST":
        erro = cria_documento(request, usuario=usuario)
        if erro:
           return HttpResponseBadRequest(erro)
        return JsonResponse({"atualizado": True,})

    organizacao = get_object_or_404(Organizacao, id=organizacao_id) if organizacao_id else None
    projeto = get_object_or_404(Projeto, id=projeto_id) if projeto_id else None
    projetos = Projeto.objects.filter(proposta__organizacao=organizacao) if organizacao else Projeto.objects.all()

    tipo = None
    if tipo_nome and tipo_nome != "ANY":
        tipo = TipoDocumento.objects.get(sigla=tipo_nome)

    if documento:
        tipo = documento.tipo_documento

    if tipo and request.user.tipo_de_usuario not in json.loads(tipo.gravar):  # Verifica se usuário tem privilégios para gravar tipo de arquivo
            return HttpResponse("<h1>Sem privilégios para gravar tipo de arquivo!</h1>", status=401)
   
    lingua = 0
    if documento:
        data = documento.data
        confidencial = documento.confidencial
        anotacao = documento.anotacao
        lingua = documento.lingua_do_documento
    else:
        data = datetime.datetime.now()
        confidencial = None
        anotacao = None
        
    if adiciona is None:
        adiciona = "adiciona_documento"

    context = {
        "organizacao": organizacao,
        "tipos_documentos": TipoDocumento.objects.all(),
        "data": data,
        "Documento": Documento,
        "projetos": projetos,
        "projeto": projeto,
        "tipo": tipo,
        "organizacoes": Organizacao.objects.all(),
        "documento": documento,
        "documento_id": documento_id,
        "configuracao": get_object_or_404(Configuracao),
        "travado": False,
        "adiciona": adiciona,
        "confidencial": confidencial,
        "anotacao": anotacao,
        "lingua": lingua,
    }
    
    return render(request, "organizacoes/documento_view.html", context=context)

@login_required
@permission_required("users.altera_professor", raise_exception=True)
def edita_documento(request, documento_id=None):
    """edita um documento."""
    documento = Documento.objects.filter(id=documento_id).last()
    if documento:
        organizacao_id = documento.organizacao.id if documento.organizacao else None
        projeto_id = documento.projeto.id if documento.projeto else None
        return adiciona_documento(request, organizacao_id=organizacao_id, projeto_id=projeto_id, tipo_nome=None, documento_id=documento_id, adiciona="edita_documento")
    return HttpResponseNotFound("<h1>Documento não encontrado!</h1>")


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_documento_tipo(request, tipo_nome=None):
    """Cria um documento com tipo."""
    return adiciona_documento(request, organizacao_id=None, projeto_id=None, tipo_nome=tipo_nome, adiciona="adiciona_documento_tipo")


@login_required
@transaction.atomic
def adiciona_documento_estudante(request, tipo_nome=None, documento_id=None):
    """Cria um documento pelos estudantes somente."""
    usuario_sem_acesso(request, (1,)) # Soh Estudantes

    if request.is_ajax() and request.method == "POST":
        erro = cria_documento(request, forca_confidencial=True)
        if erro:
           return HttpResponseBadRequest(erro)
        return JsonResponse({"atualizado": True})
    
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

    documento = Documento.objects.filter(id=documento_id).last()
    if documento:
        tipo = documento.tipo_documento
  
    lingua = 0
    if documento:
        data = documento.data
        anotacao = documento.anotacao
        lingua = documento.lingua_do_documento
    else:
        data = datetime.datetime.now()
        anotacao = None

    context = {
        "organizacao": organizacao,
        "data": data,
        "Documento": Documento,
        "projeto": projeto,
        "tipo": tipo,
        "documento": documento,
        "documento_id": documento_id,
        "configuracao": configuracao,
        "travado": True,
        "adiciona": "adiciona_documento_estudante",
        "confidencial": True,  # Estudantes só podem enviar confidencial
        "anotacao": anotacao,
        "lingua": lingua,
    }

    return render(request, "organizacoes/documento_view.html", context=context)


@login_required
@permission_required("projetos.add_proposta", raise_exception=True)
def parceiro_propostas(request):
    """Lista todas as propostas de projetos."""
    if request.user.tipo_de_usuario != 3 and request.user.tipo_de_usuario != 4:  # Não é Parceiro ou Admin
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    if hasattr(request.user, "parceiro"):
        organizacao = request.user.parceiro.organizacao
        propostas = Proposta.objects.filter(organizacao=organizacao)
    else:  # Supostamente professor
        organizacao = get_object_or_404(Organizacao, sigla="INSPER")
        propostas = None

    cabecalhos = [{"pt": "Título da Proposta", "en": "Proposal Title"},
                  {"pt": "Período", "en": "Semester"},]
    
    context = {
        "titulo": {"pt": "Propostas de Projetos Submetidas", "en": "Submitted Project Proposals"},
        "organizacao": organizacao,
        "propostas": propostas,
        "cabecalhos": cabecalhos,
    }
    return render(request, "organizacoes/parceiro_propostas.html", context)


@login_required
@permission_required("projetos.add_proposta", raise_exception=True)
def parceiro_projetos(request):
    """Lista todas as propostas de projetos."""
    if request.user.tipo_de_usuario != 3 and request.user.tipo_de_usuario != 4:  # Não é Parceiro ou Admin
        mensagem = "Você não está cadastrado como parceiro de uma organização!"
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, "generic.html", context=context)

    if hasattr(request.user, "parceiro"):
        organizacao = request.user.parceiro.organizacao
        projetos = Projeto.objects.filter(proposta__organizacao=organizacao)
    else:  # Supostamente professor
        organizacao = get_object_or_404(Organizacao, sigla="INSPER")
        projetos = None

    cabecalhos = [
        {"pt": "Projeto", "en": "Project"},
        {"pt": "Período", "en": "Semester"},
    ]

    context = {
        "titulo": {"pt": "Lista de Projetos", "en": "Projects List"},
        "organizacao": organizacao,
        "projetos": projetos,
        "cabecalhos": cabecalhos,
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
                proposta.empreendendo = True if request.POST.get("empreendendo", None) else False
                colaboracao_id = request.POST.get("colaboracao", None)
                if colaboracao_id:
                    proposta.colaboracao = Organizacao.objects.filter(pk=colaboracao_id).last()
                proposta.save()

        enviar = "mensagem" in request.POST  # Por e-mail se enviar
        mensagem = envia_proposta(proposta, request, enviar)

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
    ano_semestre = str(ano)+"."+str(semestre)

    context = {
        "titulo": {"pt": "Submissão de Proposta de Projeto (Capstone " + ano_semestre + ")", "en": "Project Proposal Submission (Capstone " + ano_semestre + ")" },
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
        "ano_semestre": ano_semestre,
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

        if request.user.tipo_de_usuario == 1:  # estudantes
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
            mensagem = envia_proposta(proposta, request, enviar)

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

    ano_semestre = str(ano)+'.'+str(semestre)
    
    context = {
        "titulo": {"pt": "Carrega Proposta de Projeto em PDF (Capstone " + ano_semestre + ")", "en": "Upload Project Proposal in PDF (Capstone " + ano_semestre + ")" },
        "full_name": full_name,
        "email": email_sub,
        "parceiro": parceiro,
        "ano_semestre": ano_semestre,
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
        propostas = Proposta.objects.filter(organizacao=organizacao).order_by("ano", "semestre")
        ant = Anotacao.objects.filter(organizacao=organizacao).order_by("momento").last()

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
    organizacoes_list = sorted(organizacoes_list, key=lambda x: (255 if x[3] is None else ( 2 if(x[2] > 0) else x[3].tipo_retorno.id ) ))

    total_organizacoes = len(organizacoes)
    total_disponiveis = sum(disponiveis)
    total_submetidas = sum(submetidas)

    cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")
    necessarios = {}
    estudantes = Aluno.objects.filter(anoPFE=ano, semestrePFE=semestre)
    for curso in cursos:
        necessarios[curso] = estudantes.filter(curso2=curso).count()/configuracao.estudates_por_grupo  # grupos de 4 estudantes

    context = {
        "titulo": {"pt": "Prospecção de Organizações", "en": "Prospecting Organizations"},	
        "organizacoes_list": organizacoes_list,
        "total_organizacoes": total_organizacoes,
        "total_disponiveis": total_disponiveis,
        "total_submetidas": total_submetidas,
        "ano": ano,
        "semestre": semestre,
        "filtro": "todas",
        "cursos": cursos,
        "necessarios": necessarios,
        "tipo_retorno": TipoRetorno.objects.all(),
        }
    return render(request, "organizacoes/organizacoes_prospectadas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_projetos(request):
    """Exibe as organizações prospectadas e a última comunicação."""
    
    if request.is_ajax() and "edicao" in request.POST:
        edicao = request.POST["edicao"]
        
        projetos_periodo = Projeto.objects.all()
        if edicao not in ("todas",):
            ano, semestre = map(int, edicao.split('.'))
            projetos_periodo = projetos_periodo.filter(ano=ano, semestre=semestre)

        organizacoes = []
        for projeto in projetos_periodo:
            if projeto.proposta.organizacao not in organizacoes:
                organizacoes.append(projeto.proposta.organizacao)
        
        projetos = []
        contato = []
        for organizacao in organizacoes:
            projetos.append(projetos_periodo.filter(proposta__organizacao=organizacao))
            contato.append(Anotacao.objects.filter(organizacao=organizacao).order_by("momento").last())

        organizacoes_list = zip(organizacoes, projetos, contato)

        context = {
            "organizacoes_list": organizacoes_list,
            "projetos_periodo": projetos_periodo,
            "organizacoes": organizacoes,
            "tipo_retorno": TipoRetorno.objects.all(),
            }

    else:

        context = {
            "titulo": {"pt": "Prospecção de Organizações com Projetos", "en": "Prospecting Organizations with Projects"},
            "edicoes": get_edicoes(Projeto)[0],
            "tipo_retorno": TipoRetorno.objects.all(),
            }
    
    return render(request, "organizacoes/organizacoes_projetos.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_lista(request):
    """Exibe todas as organizações que já submeteram propostas de projetos."""
    organizacoes = Organizacao.objects.all()

    # Prefetch dos objetos relacionados
    propostas_prefetch = Prefetch("proposta_set", queryset=Proposta.objects.order_by("ano", "semestre"))
    anotacoes_prefetch = Prefetch("anotacao_set", queryset=Anotacao.objects.order_by("momento"))
    projetos_prefetch = Prefetch("projeto_set", queryset=Projeto.objects.filter(alocacao__isnull=False).distinct())

    organizacoes = organizacoes.prefetch_related(propostas_prefetch, anotacoes_prefetch, projetos_prefetch)

    fechados = []
    desde = []
    contato = []
    grupos = []

    for organizacao in organizacoes:
        propostas = organizacao.proposta_set.all()
        if propostas:
            desde.append(f"{propostas.first().ano}.{propostas.first().semestre}")
        else:
            desde.append("---------")

        anot = organizacao.anotacao_set.last()
        if anot:
            contato.append(anot)
        else:
            contato.append("---------")

        projetos = Projeto.objects.filter(proposta__organizacao=organizacao)
        fechados.append(projetos.count())

        tipo_estudantes = ""
        for projeto in projetos:
            estudantes = Aluno.objects.filter(alocacao__projeto=projeto)
            tipos = [estudante.curso2.sigla_curta for estudante in estudantes]
            tipo_estudantes += "[" + "|".join(tipos) + "] "
        grupos.append(tipo_estudantes)

    organizacoes_list = zip(organizacoes, fechados, desde, contato, grupos)
    total_organizacoes = organizacoes.count()
    total_submetidos = Proposta.objects.count()
    total_fechados = Projeto.objects.filter(alocacao__isnull=False).distinct().count()


    cabecalhos = [
        {"pt": "Organização", "en": "Company", },
        {"pt": "Último <br>Contato", "en": "Last <br>Contact", },
        {"pt": "Parceira <br>Desde", "en": "Partner <br>Since", },
        {"pt": "Propostas <br>Enviadas", "en": "Submitted <br>Proposals", },
        {"pt": "Projetos <br>Fechados", "en": "Closed <br>Projects", },
        {"pt": "Grupos de Estudantes", "en": "Group of Students", },    
    ]

    captions = []
    for curso in Curso.objects.filter(curso_do_insper=True).order_by("id"):
        captions.append({"sigla": curso.sigla_curta,
                          "pt": curso.nome,
                          "en": curso.nome_en,})
    
    context = {
        "titulo": {"pt": "Organizações Parceiras", "en": "Partnership Companies"},
        "organizacoes_list": organizacoes_list,
        "total_organizacoes": total_organizacoes,
        "total_submetidos": total_submetidos,
        "total_fechados": total_fechados,
        "meses3": datetime.date.today() - datetime.timedelta(days=100),
        "filtro": "todas",
        "grupos": grupos,
        "cabecalhos": cabecalhos,
        "captions": captions,
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
        "titulo": {"pt": "Organização Parceira", "en": "Partnership Organization"},
        "organizacao": organizacao,
        "projetos": Projeto.objects.filter(proposta__organizacao=organizacao),
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

    ano = 2018    # Ano de início do Capstone
    semestre = 2  # Semestre de início do Capstone
    while True:
        organizacoes = []
        grupos = []
        for organizacao in Organizacao.objects.all():
            count_projetos = []
            grupos_pfe = Projeto.objects.filter(proposta__organizacao=organizacao, ano=ano, semestre=semestre)
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
        "titulo": {"pt": "Alocação de Organizações Parceiras", "en": "Partnership Organizations Allocation"},
        "anos": anos,
        }

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
        "titulo": {"pt": "Formulário de Feedback das Organizações Parceiras", "en": "Partnership Organizations Feedback Form"},
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

    cabecalhos = [{ "pt": "Nome", "en": "Name", }, 
                  { "pt": "Cargo", "en": "Position", }, 
                  { "pt": "Organização", "en": "Organization", }, 
                  { "pt": "e-mail", "en": "e-mail", }, 
                  { "pt": "telefone", "en": "phone", }, 
                  { "pt": "papel", "en": "role", }, ]
    
    captions = []
    for _, caption in Conexao.papel.items():
        captions.append({"sigla": caption[1],
                         "pt": caption[0],
                         "en": caption[0], })

    context = {
        "parceiros": parceiros,
        "cabecalhos": cabecalhos,
        "titulo": { "pt": "Parceiros Profissionais", "en": "Professional Partners", },
        "edicoes": get_edicoes(Conexao)[0],
        "edicao": edicao,
        "captions": captions,
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
        "cabecalhos": [{"pt": "Nome", "en": "Name", }, {"pt": "e-mail", "en": "e-mail", }, {"pt": "Tipo", "en": "Type", }, ],
        "titulo": {"pt": "Todos os Usuários", "en": "All Users"},
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

        # Identifica Parceiro
        if "parceiro_id" in request.POST:
            parceiro_id = request.POST.get("parceiro_id", None)
            parceiro = get_object_or_404(Parceiro, id=parceiro_id)

            conexao, _ = Conexao.objects.get_or_create(parceiro=parceiro,
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

        # COLABORAÇÃO
        if "colaboracao" in request.POST:
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

        return JsonResponse({"atualizado": True,})

    if projeto.organizacao:
        parceiros = Parceiro.objects.filter(organizacao=projeto.organizacao)
    else:
        return HttpResponseNotFound("<h1>Projeto não tem organização definida!</h1>")

    cooperacoes = Conexao.objects.filter(projeto=projeto, colaboracao=True)
    colaboradores = cooperacoes.last().parceiro if cooperacoes else None
    
    cabecalhos = [
        {"pt": "GR", "en": "GR", },
        {"pt": "MT", "en": "MT", },
        {"pt": "AA", "en": "AA", },
        {"pt": "Nome", "en": "Name", },
        {"pt": "Cargo", "en": "Position", },
        {"pt": "e-mail", "en": "e-mail", },
        {"pt": "Telefone", "en": "Phone", },
    ]

    captions = []
    for _, caption in Conexao.papel.items():
        captions.append({"sigla": caption[1],
                         "pt": caption[0],
                         "en": caption[0], })

    context = {
        "titulo": {"pt": "Seleção de Conexões", "en": "Connection Selection"},
        "projeto": projeto,
        "parceiros": parceiros,
        "todos_parceiros": Parceiro.objects.all(),
        "colaboradores": colaboradores,
        "cabecalhos": cabecalhos,
        "captions": captions,
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

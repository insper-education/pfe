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

from organizacoes.support import cria_documento

from administracao.models import Despesa
from administracao.support import usuario_sem_acesso

from calendario.support import cria_material_documento

from users.support import adianta_semestre, get_edicoes, retrocede_semestre
from users.models import PFEUser, Parceiro, Aluno, Alocacao

from projetos.models import Proposta, Organizacao, Projeto, Configuracao, Feedback
from projetos.models import Anotacao, Conexao, Documento, TipoRetorno, Evento, FeedbackEstudante
from operacional.models import Curso
from documentos.models import TipoDocumento

# Liberado para Parceiros poderem enviar proposta de projeto mesmo se não logados
# @login_required
# @permission_required("projetos.add_proposta", raise_exception=True)
def index_organizacoes(request):
    """Mostra página principal do parceiro de uma organização."""
    contex = {"titulo": {"pt": "Área dos Parceiros", "en": "Partners Area"},}
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
            anotacao_obj = Anotacao(organizacao=organizacao)

        if "data_hora" in request.POST:
            try:
                anotacao_obj.momento = dateutil.parser.parse(request.POST["data_hora"])
            except (ValueError, OverflowError):
                anotacao_obj.momento = datetime.datetime.now()

        if "texto" in request.POST and "tipo_retorno" in request.POST:
            anotacao_obj.autor = request.user
            anotacao_obj.texto = request.POST["texto"]
            anotacao_obj.tipo_retorno = TipoRetorno.objects.get(id=request.POST["tipo_retorno"])
        else:
            return JsonResponse({"atualizado": False})

        anotacao_obj.save()

        data = {
            "data": anotacao_obj.momento.strftime("%d/%m/%y"),
            "data_full": anotacao_obj.momento.strftime("%d/%m/%Y"),
            "autor_nome": anotacao_obj.autor.first_name,
            "autor_sobrenome": anotacao_obj.autor.last_name,
            "anotacao_id": anotacao_obj.id,
            "cor": anotacao_obj.tipo_retorno.cor,
            "tipo_retorno_id": anotacao_obj.tipo_retorno.id,
            "tipo_retorno_nome": anotacao_obj.tipo_retorno.nome,
            "organizacao_id": organizacao_id,
            "novo": False if anotacao_id else True,
            "atualizado": True,
        }

        return JsonResponse(data)

    anotacao_obj = get_object_or_404(Anotacao, id=anotacao_id) if anotacao_id else None

    lista = request.GET.get("lista", None)

    context = {
        "organizacao": organizacao,
        "tipo_retorno": TipoRetorno.objects.all(),
        "anotacao": anotacao_obj,
        "data_hora": anotacao_obj.momento if anotacao_obj else datetime.datetime.now(),
        "organizacoes": Organizacao.objects.all(),
        "url": request.get_full_path(),
        "organiza_em_lista": True if lista else False,
    }

    return render(request, "organizacoes/anotacao_view.html", context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def adiciona_despesa(request, despesa_id=None):
    """Adiciona uma Despesa na base de dados."""

    if despesa_id:
        despesa = get_object_or_404(Despesa, id=despesa_id)
    else:
        despesa = None

    if request.is_ajax() and request.method == "POST":
        if despesa and "excluir" in request.POST:
            despesa.delete()
            return JsonResponse({"atualizado": True,})
        # elif "atualiza" not in request.POST:
        #     return HttpResponse("Atualização não realizada.", status=401)

        if despesa is None:
            despesa = Despesa()

        if "data" in request.POST:
            try:
                despesa.data = dateutil.parser.parse(request.POST["data"])
            except (ValueError, OverflowError):
                despesa.data = datetime.datetime.now()

        despesa.tipo_de_despesa = request.POST.get("tipo_despesa", None)
        valor = request.POST.get("valor", None)
        moeda = request.POST.get("moeda", None)
        if valor and moeda:
            if moeda == "BRL":
                despesa.valor_r = float(valor)
                despesa.valor_d = None
            elif moeda == "USD":
                despesa.valor_d = float(valor)
                despesa.valor_r = None

        despesa.descricao = request.POST.get("descricao", None)
        despesa.fornecedor = request.POST.get("fornecedor", None)
        
        if "projeto" in request.POST and request.POST["projeto"]:
            despesa.projeto = Projeto.objects.get(id=request.POST["projeto"])
        else:
            despesa.projeto = None

        despesa.save()

        documentos = []
        if "arquivo_0" in request.FILES or ("link_0" in request.POST and request.POST["link_0"] != ""):
            documento = cria_material_documento(request, "arquivo_0", "link_0", sigla="DESP")
            documentos.append(documento)
        else:
            material = request.POST.get("anexo_0", None)
            if material:
                documento = Documento.objects.get(id=material)
                documentos.append(documento)

        despesa.documentos.set(documentos)

        return JsonResponse({"atualizado": True,})

    context = {
        "tipo_despesas": Despesa.TIPO_DE_DESPESA,
        "Despesa": Despesa,
        "despesa": despesa,
        "projetos": Projeto.objects.all(),
        "documentos": Documento.objects.filter(tipo_documento__sigla="DESP"),
    }
    
    return render(request, "organizacoes/despesa_view.html", context=context)

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
    data = datetime.datetime.now()
    if documento:
        #data = documento.data
        confidencial = documento.confidencial
        anotacao = documento.anotacao
        lingua = documento.lingua_do_documento
    else:
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
    data = datetime.datetime.now()
    if documento:
        # data = documento.data
        confidencial = documento.confidencial
        anotacao = documento.anotacao
        lingua = documento.lingua_do_documento
    else:
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
    data = datetime.datetime.now()
    if documento:
        anotacao = documento.anotacao
        lingua = documento.lingua_do_documento
    else:
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
    if request.user.eh_prof: # Não é Professor
        mensagem_erro = {"pt": "Área restrita a Parceiros, Professores podem acessar propostas através do menu Propostas!",
                         "en": "Restricted area for Partners, Professors can access proposals through the Proposals menu!"}
        context = {
            "area_principal": True,
            "propostas_lista": True,
            "mensagem_erro": mensagem_erro,
        }
        return render(request, "generic_ml.html", context=context)
    elif not (request.user.eh_parc or request.user.eh_admin):  # Não é Parceiro ou Admin
        mensagem_erro = {"pt": "Você não está cadastrado como parceiro de uma organização!",
                    "en": "You are not registered as a partner of an organization!"}
        context = {
            "area_principal": True,
            "mensagem_erro": mensagem_erro,
        }
        return render(request, "generic_ml.html", context=context)

    if hasattr(request.user, "parceiro"):
        organizacao = request.user.parceiro.organizacao
        propostas = Proposta.objects.filter(organizacao=organizacao).order_by("-ano", "-semestre")
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
    if request.user.eh_prof: # Não é Professor
        mensagem_erro = {"pt": "Área restrita a Parceiros, Professores podem acessar projetos através do menu Projetos!",
                         "en": "Restricted area for Partners, Professors can access projects through the Projects menu!"}
        context = {
            "area_principal": True,
            "projetos_fechados": True,
            "mensagem_erro": mensagem_erro,
        }
        return render(request, "generic_ml.html", context=context)
    elif not (request.user.eh_parc or request.user.eh_admin):  # Não é Parceiro ou Admin
        mensagem_erro = {"pt": "Você não está cadastrado como parceiro de uma organização!",
                    "en": "You are not registered as a partner of an organization!"}
        context = {
            "area_principal": True,
            "mensagem_erro": mensagem_erro,
        }
        return render(request, "generic_ml.html", context=context)

    if hasattr(request.user, "parceiro"):
        organizacao = request.user.parceiro.organizacao
        projetos = Projeto.objects.filter(proposta__organizacao=organizacao).order_by("-ano", "-semestre")
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


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_prospect(request):
    """Exibe as organizações prospectadas e a última comunicação."""
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

    for organizacao in Organizacao.objects.all():
        propostas = Proposta.objects.filter(organizacao=organizacao).order_by("ano", "semestre")

        faixa = datetime.datetime.now() - datetime.timedelta(days=periodo)
        anotacoes = Anotacao.objects.filter(organizacao=organizacao, momento__gte=faixa).order_by("-momento")
        
        if (periodo > 366) or anotacoes:

            organizacoes.append(organizacao)
            contato.append(anotacoes) # None se não houver anotação
            
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

    # No final coloco para 2 (com proposta submetida) se houver proposta submetida, mesmo que a anotação diga diferente
    organizacoes_list = sorted(organizacoes_list, key=lambda x: (255 if x[3].first() is None else ( 2 if(x[2] > 0) else x[3].first().tipo_retorno.id ) ))

    total_disponiveis = sum(disponiveis)
    total_submetidas = sum(submetidas)

    cursos = Curso.objects.filter(curso_do_insper=True).order_by("id")
    necessarios = {}
    estudantes = Aluno.objects.filter(ano=ano, semestre=semestre)
    for curso in cursos:
        necessarios[curso] = estudantes.filter(curso2=curso).count()/configuracao.estudates_por_grupo  # grupos de 4 estudantes

    context = {
        "titulo": {"pt": "Prospecção de Organizações", "en": "Prospecting Organizations"},	
        "organizacoes_list": list(organizacoes_list),
        "organizacoes": organizacoes,
        "total_disponiveis": total_disponiveis,
        "total_submetidas": total_submetidas,
        "ano": ano,
        "semestre": semestre,
        "filtro": "todas",
        "cursos": cursos,
        "necessarios": necessarios,
        "tipo_retorno": TipoRetorno.objects.all(),
        "GRUPO_DE_RETORNO": TipoRetorno.GRUPO_DE_RETORNO,
        "selecionada_acompanhamento": 1,  # (1, "Prospecção"),
        }
    return render(request, "organizacoes/organizacoes_prospectadas.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_projetos(request):
    """Exibe as organizações prospectadas e a última comunicação."""
    
    if request.is_ajax() and "edicao" in request.POST:
        edicao = request.POST["edicao"]
        
        evento = None
        projetos_periodo = Projeto.objects.all()
        if edicao not in ("todas",):
            ano, semestre = map(int, edicao.split('.'))
            projetos_periodo = projetos_periodo.filter(ano=ano, semestre=semestre)
            ano_r, semestre_r = retrocede_semestre(ano, semestre)
            evento = Evento.get_evento(sigla="RCMG", ano=ano_r, semestre=semestre_r)

        organizacoes = []
        for projeto in projetos_periodo:
            if projeto.proposta.organizacao not in organizacoes:
                organizacoes.append(projeto.proposta.organizacao)
        
        projetos = []
        contato = []
        for organizacao in organizacoes:
            projetos.append(projetos_periodo.filter(proposta__organizacao=organizacao))
            if evento:
                contatos = Anotacao.objects.filter(organizacao=organizacao, momento__gte=evento.endDate).order_by("-momento")
            else:
                contatos = Anotacao.objects.filter(organizacao=organizacao).order_by("-momento")
            contato.append(contatos)

        organizacoes_list = list(zip(organizacoes, projetos, contato))

        context = {
            "organizacoes_list": organizacoes_list,
            "projetos_periodo": projetos_periodo,
            "organizacoes": organizacoes,
            "tipo_retorno": TipoRetorno.objects.all(),
            }

    else:

        context = {
            "titulo": {"pt": "Acompanhamento de Organizações com Projetos", "en": "Follow-up of Organizations with Projects"},
            "edicoes": get_edicoes(Projeto)[0],
            "tipo_retorno": TipoRetorno.objects.all(),
            "GRUPO_DE_RETORNO": TipoRetorno.GRUPO_DE_RETORNO,
            "selecionada_acompanhamento": 3,  # (3, "Contratação"),
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
    organizacoes = organizacoes.prefetch_related(propostas_prefetch, anotacoes_prefetch)

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
        {"pt": "Segmento", "en": "Segment", },
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
        "captions": [captions],
    }

    return render(request, "organizacoes/organizacoes_lista.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacao_completo(request, org=None):  # acertar isso para pk
    """Exibe detalhes das organizações parceiras."""
    if not org:
        return HttpResponseNotFound("<h1>Organização não encontrada!</h1>")
    organizacao = get_object_or_404(Organizacao, id=org)
    feedbacks_estudantes = FeedbackEstudante.objects.filter(projeto__proposta__organizacao=organizacao)
    #feedbacks_organizacao = Feedback.objects.filter()
    context = {
        "titulo": {"pt": "Organização Parceira", "en": "Partnership Organization"},
        "organizacao": organizacao,
        "projetos": Projeto.objects.filter(proposta__organizacao=organizacao),
        "cursos": Curso.objects.all().order_by("id"),
        "feedbacks_estudantes": feedbacks_estudantes,
    }
    return render(request, "organizacoes/organizacao_completo.html", context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def organizacoes_tabela(request):
    """Alocação das Organizações por semestre."""
    # configuracao = get_object_or_404(Configuracao)

    if request.is_ajax():
        if "edicao" not in request.POST:
            return HttpResponseNotFound("<h1>Edição não encontrada!</h1>")
        
        edicao = request.POST["edicao"]
        if edicao == "todas":
            ano, semestre = None, None
        else:
            ano, semestre = edicao.split('.')

        organizacoes = []
        grupos = []
        for organizacao in Organizacao.objects.all():
            count_projetos = []
            if ano and semestre:
                grupos_pfe = Projeto.objects.filter(proposta__organizacao=organizacao, ano=ano, semestre=semestre)
            else:
                grupos_pfe = Projeto.objects.filter(proposta__organizacao=organizacao)
            if grupos_pfe:
                for grupo in grupos_pfe:  # garante que tem alunos no projeto
                    alunos_pfe = Aluno.objects.filter(alocacao__projeto=grupo)
                    if alunos_pfe:  # len(alunos_pfe) > 0
                        count_projetos.append(grupo)
                if count_projetos:
                    organizacoes.append(organizacao)
                    grupos.append(count_projetos)

        cabecalhos = [{"pt": "Organização", "en": "Company"},
                      {"pt": "Projetos", "en": "Projects"}]

        context = {
            "cabecalhos": cabecalhos,
            "organizacoes": zip(organizacoes, grupos),
        }

    else:
        context = {
            "titulo": {"pt": "Alocação de Organizações Parceiras", "en": "Partnership Organizations Allocation"},
            "edicoes": get_edicoes(Projeto)[0],
            }

    return render(request, "organizacoes/organizacoes_tabela.html", context)


# @login_required
@transaction.atomic
def projeto_feedback(request):
    """Para Feedback das Organizações Parceiras."""
    if request.method == "POST":
        feedback = Feedback()
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

        context = {"mensagem": {"pt": "Feedback recebido, obrigado!", "en": "Feedback received, thank you!"}}
        return render(request, "generic_ml.html", context=context)

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
        
        if request.POST.get("todos") == "true":
            parceiros = Parceiro.objects.all()
        else:
            if "edicao" not in request.POST:
                return HttpResponseNotFound("<h1>Edição não encontrada!</h1>")
            
            edicao = request.POST["edicao"]
            
            if "curso" in request.POST:
                curso = request.POST["curso"]
                if curso != "TE" and curso != 'T':
                    if edicao not in ("todas",):
                        ano, semestre = map(int, edicao.split('.'))
                        alocacoes = Alocacao.objects.filter(projeto__ano=ano, projeto__semestre=semestre, aluno__curso2__sigla_curta=curso)
                    else:
                        alocacoes = Alocacao.objects.filter(aluno__curso2__sigla_curta=curso)
                    lista_projetos = alocacoes.values_list("projeto", flat=True)
                    conexoes = Conexao.objects.filter(projeto__id__in=lista_projetos)
                    lista_conexoes = conexoes.values_list("parceiro", flat=True)
                    parceiros = Parceiro.objects.filter(id__in=lista_conexoes)
                else:
                    if edicao not in ("todas",):
                        ano, semestre = map(int, edicao.split('.'))
                        lista_projetos = Projeto.objects.filter(ano=ano, semestre=semestre).values_list("id", flat=True)
                        conexoes = Conexao.objects.filter(projeto__id__in=lista_projetos)
                        lista_conexoes = conexoes.values_list("parceiro", flat=True)
                        parceiros = Parceiro.objects.filter(id__in=lista_conexoes)
                    else:
                        conexoes = Conexao.objects.filter(projeto__isnull=False)
                        lista_conexoes = conexoes.values_list("parceiro", flat=True)
                        parceiros = Parceiro.objects.filter(id__in=lista_conexoes)
            else:
                return HttpResponseNotFound("<h1>Curso não encontrado!</h1>")

    cabecalhos = [{ "pt": "Nome", "en": "Name", }, 
                  { "pt": "Gênero", "en": "Gender", "esconder": True},
                  { "pt": "Cargo", "en": "Position", }, 
                  { "pt": "Organização", "en": "Organization", }, 
                  { "pt": "e-mail", "en": "e-mail", }, 
                  { "pt": "telefone", "en": "phone", }, 
                  { "pt": "papel", "en": "role", }, ]
    
    captions = []
    for _, caption in Conexao.papel.items():
        captions.append({"sigla": caption["sigla"],
                         "pt": caption["nome"],
                         "en": caption["nome_en"], })   #"cor": "#2563EB"

    context = {
        "parceiros": parceiros,
        "cabecalhos": cabecalhos,
        "titulo": { "pt": "Parceiros Conectados a Projetos", "en": "Partners Connected to Projects", },
        "edicoes": get_edicoes(Conexao)[0],
        "todos": True,
        "edicao": edicao,
        "cursos": Curso.objects.filter(curso_do_insper=True).order_by("id"),
        "captions": [captions],
        }

    return render(request, "organizacoes/todos_parceiros.html", context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def todos_usuarios(request):
    """Procura e exibe usuários por busca de nome."""
    context = {
        "cabecalhos": [{"pt": "Nome", "en": "Name", }, {"pt": "e-mail", "en": "e-mail", }, {"pt": "Tipo", "en": "Type", }, ],
        "titulo": {"pt": "Todos os Usuários", "en": "All Users"},
    }
    if request.is_ajax():                
        nome = request.POST.get("nome", None).strip()
        context["usuarios"] = PFEUser.objects.filter(Q(first_name__icontains=nome) | Q(last_name__icontains=nome)) if nome else []
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
                conexao, _ = Conexao.objects.get_or_create(parceiro=parceiro, projeto=projeto)
                conexao.colaboracao = True
                conexao.save()
            else:
                conexoes_colab = Conexao.objects.filter(colaboracao=True, projeto=projeto)

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
        "captions": [captions],
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

def proposta_submissao_velho(request):
    """Submissão de proposta de projeto (link antigo não deve mais ser usado)."""
    return redirect("proposta_submissao")

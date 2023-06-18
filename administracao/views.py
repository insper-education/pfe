#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import re           # regular expression (para o import)
import tablib
#import dateutil.parser

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session

from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import timezone

from documentos.support import render_to_pdf

from projetos.models import Configuracao, Organizacao, Proposta, Projeto
from projetos.models import Avaliacao2, get_upload_path, Feedback, Disciplina

from .support import get_limite_propostas

from projetos.support import simple_upload

from projetos.resources import DisciplinasResource
from projetos.resources import Avaliacoes2Resource
from projetos.resources import ProjetosResource
from projetos.resources import OrganizacoesResource
from projetos.resources import OpcoesResource
from projetos.resources import ProfessoresResource
from projetos.resources import EstudantesResource
from projetos.resources import ParceirosResource
from projetos.resources import ConfiguracaoResource
from projetos.resources import FeedbacksResource
from projetos.resources import UsuariosResource

from users.models import PFEUser, Aluno, Professor, Administrador, Parceiro
from users.models import Opcao, Alocacao

from operacional.models import Curso

from users.support import adianta_semestre

from propostas.support import ordena_propostas

from .support import usuario_sem_acesso


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def index_administracao(request):
    """Mostra página principal para administração do sistema."""
    return render(request, 'administracao/index_admin.html')


@login_required
@permission_required("users.view_administrador", raise_exception=True)
def index_carregar(request):
    """Para carregar dados de arquivos para o servidor."""
    return render(request, 'administracao/carregar.html')


def registra_organizacao(request, org=None):
    """Rotina para cadastrar organizacao no sistema."""
    if not org:
        organizacao = Organizacao.create()
    else:
        organizacao = org

    nome = request.POST.get('nome', None)
    if nome:
        organizacao.nome = nome.strip()

    sigla = request.POST.get('sigla', None)
    if sigla:
        organizacao.sigla = sigla.strip()

    organizacao.endereco = request.POST.get('endereco', None)

    website = request.POST.get('website', None)
    if website:
        if website[:4] == "http":
            organizacao.website = website.strip()
        else:
            organizacao.website = "http://" + website.strip()

    organizacao.informacoes = request.POST.get('informacoes', None)

    cnpj = request.POST.get('cnpj', None)
    if cnpj:
        organizacao.cnpj = cnpj[:2]+cnpj[3:6]+cnpj[7:10]+cnpj[11:15]+cnpj[16:18]

    organizacao.inscricao_estadual = request.POST.get('inscricao_estadual', None)
    organizacao.razao_social = request.POST.get('razao_social', None)
    organizacao.ramo_atividade = request.POST.get('ramo_atividade', None)

    if 'logo' in request.FILES:
        logotipo = simple_upload(request.FILES['logo'],
                                    path=get_upload_path(organizacao, ""))
        organizacao.logotipo = logotipo[len(settings.MEDIA_URL):]

    organizacao.save()

    return "", 200


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_disciplina(request, proposta_id=None):
    """Cadastra Organização na base de dados do PFE."""
    mensagem = None

    if request.method == 'POST':

        if 'nome' in request.POST:

            (disciplina, _created) = Disciplina.objects.get_or_create(nome=request.POST.get('nome', None))
        
            if not _created:
                return HttpResponse("Conflito: Disciplina já cadastrada", status=409)
            
            disciplina.save()
            mensagem = "Disciplina cadastrada na base de dados."

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

    context = {
        "mensagem": mensagem,
        "disciplinas": Disciplina.objects.all().order_by("nome"),
        "disciplina_length": Disciplina._meta.get_field('nome').max_length,
    }
    
    return render(request, 'administracao/cadastra_disciplina.html', context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_organizacao(request, proposta_id=None):
    """Cadastra Organização na base de dados do PFE."""
    if request.method == 'POST':

        if 'nome' in request.POST and 'sigla' in request.POST:

            mensagem, codigo = registra_organizacao(request)
            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

            context = {
                "voltar": True,
                "cadastrar_organizacao": True,
                "organizacoes_lista": True,
                "area_principal": True,
                "mensagem": "Organização inserida na base de dados.",
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, 'generic.html', context=context)


    proposta = None
    if proposta_id:
        proposta = get_object_or_404(Proposta, id=proposta_id)

    context = {
        "proposta": proposta,
        "nome_length": Organizacao._meta.get_field('nome').max_length,
        "sigla_length": Organizacao._meta.get_field('sigla').max_length,
        "endereco_length": Organizacao._meta.get_field('endereco').max_length,
        "website_length": Organizacao._meta.get_field('website').max_length,
        "informacoes_length": Organizacao._meta.get_field('informacoes').max_length,
    }
    
    return render(request, 'administracao/cadastra_organizacao.html', context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_organizacao(request, primarykey):
    """Edita Organização na base de dados do PFE."""

    organizacao = get_object_or_404(Organizacao, id=primarykey)

    if request.method == 'POST':

        if 'nome' in request.POST and 'sigla' in request.POST:

            mensagem, codigo = registra_organizacao(request, organizacao)
            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

            context = {
                "voltar": True,
                "cadastrar_organizacao": True,
                "organizacoes_lista": True,
                "area_principal": True,
                "mensagem": "Organização atualizada na base de dados.",
            }

        else:

            context = {
                "voltar": True,
                "area_principal": True,
                "mensagem": "<h3 style='color:red'>Falha na inserção na base da dados.<h3>",
            }

        return render(request, 'generic.html', context=context)

    context = {
        "organizacao": organizacao,
        "edicao": True,
    }

    return render(request, 'administracao/cadastra_organizacao.html', context=context)


def registro_usuario(request, user=None):
    """Rotina para cadastrar usuário no sistema."""
    if not user:
        usuario = PFEUser.create()
    else:
        usuario = user

    email = request.POST.get('email', None)
    if email:
        usuario.email = email.strip()

    tipo_de_usuario = request.POST.get('tipo_de_usuario', None)
    if tipo_de_usuario == "estudante":  # (1, 'aluno')
        usuario.tipo_de_usuario = 1
    elif tipo_de_usuario == "professor":  # (2, 'professor')
        usuario.tipo_de_usuario = 2
    elif tipo_de_usuario == "parceiro":  # (3, 'parceiro')
        usuario.tipo_de_usuario = 3
    else:
        # (4, 'administrador')
        return ("Algum erro não identificado.", 401)

    # se for um usuário novo
    if not user:
        if usuario.tipo_de_usuario == 1 or usuario.tipo_de_usuario == 2:
            username = request.POST['email'].split("@")[0]
        elif usuario.tipo_de_usuario == 3:
            username = request.POST['email'].split("@")[0] + "." + \
                request.POST['email'].split("@")[1].split(".")[0]
        else:
            return ("Algum erro não identificado.", 401)

        if PFEUser.objects.exclude(pk=usuario.pk).filter(username=username).exists():
            return ('Username "%s" já está sendo usado.' % username, 401)

        usuario.username = username

    if 'nome' in request.POST and len(request.POST['nome'].split()) > 1:
        usuario.first_name = request.POST['nome'].split()[0]
        usuario.last_name = " ".join(request.POST['nome'].split()[1:])
    else:
        return ("Erro: Não inserido nome completo no formulário.", 401)

    if 'genero' in request.POST:
        if request.POST['genero'] == "masculino":
            usuario.genero = "M"
        elif request.POST['genero'] == "feminino":
            usuario.genero = "F"
    else:
        usuario.genero = "X"

    usuario.linkedin = request.POST.get('linkedin', None)
    usuario.tipo_lingua = request.POST.get('lingua', None)

    usuario.observacoes = request.POST.get('observacao', None)

    if 'ativo' in request.POST:
        if request.POST['ativo'] == "1":
            usuario.is_active = True
        else:
            usuario.is_active = False

    if 'comite' in request.POST:
        if request.POST['comite'] == "1":
            usuario.membro_comite = True
        else:
            usuario.membro_comite = False

    usuario.save()

    # Agora que o usuario foi criado, criar o tipo para não gerar inconsistências
    mensagem = ""

    if usuario.tipo_de_usuario == 1:  # estudante

        if not hasattr(user, 'aluno'):
            estudante = Aluno.create(usuario)
        else:
            estudante = user.aluno

        estudante.matricula = request.POST.get('matricula', None)

        curso = request.POST.get('curso', None)

        # Remover o curso e só usar curso2
        if curso == "computacao":
            estudante.curso = 'C'   # ('C', 'Computação'),
            estudante.curso2 = Curso.objects.get(nome="Engenharia de Computação")
        elif curso == "mecanica":
            estudante.curso = 'M'   # ('M', 'Mecânica'),
            estudante.curso2 = Curso.objects.get(nome="Engenharia Mecânica")
        elif curso == "mecatronica":
            estudante.curso = 'X'   # ('X', 'Mecatrônica'),
            estudante.curso2 = Curso.objects.get(nome="Engenharia Mecatrônica")
        else:
            estudante.curso = None
            estudante.curso2 = None
            mensagem += "Algum erro não identificado.<br>"

        try:
            estudante.anoPFE = int(request.POST['ano'])
            estudante.semestrePFE = int(request.POST['semestre'])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            estudante.anoPFE = None
            estudante.semestrePFE = None
            mensagem += "Erro na identificação do ano e semestre.<br>"

        try:
            estudante.cr = float(request.POST['cr'])
        except (ValueError, OverflowError, MultiValueDictKeyError):
            pass
            #estudante.cr = 0

        estudante.trancado = 'estudante_trancado' in request.POST

        estudante.save()

    elif usuario.tipo_de_usuario == 2:  # professor

        if not hasattr(user, 'professor'):
            professor = Professor.create(usuario)
        else:
            professor = user.professor

        dedicacao = request.POST.get('dedicacao', None)
        if dedicacao == "ti":  # ("TI", "Tempo Integral"),
            professor.dedicacao = 'TI'
        elif dedicacao == "tp":  # ("TP", 'Tempo Parcial'),
            professor.dedicacao = 'TP'
        else:
            professor.dedicacao = None
            mensagem += "Algum erro não identificado.<br>"

        professor.areas = request.POST.get('areas', None)
        professor.website = request.POST.get('website', None)
        professor.lattes = request.POST.get('lattes', None)

        professor.save()

        content_type = ContentType.objects.get_for_model(Professor)

        try:
            permission = Permission.objects.get(
                codename='change_professor',
                content_type=content_type,
            )
            usuario.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass  # não encontrada a permissão

        try:  # <Permission: users | Professor | Professor altera valores>
            permission = Permission.objects.get(
                codename='altera_professor',
                content_type=content_type,
            )
            usuario.user_permissions.add(permission)
        except Permission.DoesNotExist:
            pass  # não encontrada a permissão

        usuario.save()

    elif usuario.tipo_de_usuario == 3:  # Parceiro

        if not hasattr(user, 'parceiro'):
            parceiro = Parceiro.create(usuario)
        else:
            parceiro = user.parceiro

        parceiro.cargo = request.POST.get('cargo', None)
        parceiro.telefone = request.POST.get('telefone', None)
        parceiro.celular = request.POST.get('celular', None)
        parceiro.instant_messaging = request.POST.get('instant_messaging', None)
        
        try:
            tmp_pk = int(request.POST['organizacao'])
            parceiro.organizacao = Organizacao.objects.get(pk=tmp_pk)
        except (ValueError, OverflowError, Organizacao.DoesNotExist):
            parceiro.organizacao = None
            mensagem += "Organização não encontrada.<br>"

        parceiro.principal_contato = 'principal_contato' in request.POST

        parceiro.save()

        content_type = ContentType.objects.get_for_model(Parceiro)
        permission = Permission.objects.get(
            codename='change_parceiro',
            content_type=content_type,
        )
        usuario.user_permissions.add(permission)
        usuario.save()

    if mensagem != "":
        return (mensagem, 401)
    elif user:
        return ("Usuário atualizado na base de dados.", 200)
    else:
        return ("Usuário inserido na base de dados.", 200)
    

@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def cadastrar_usuario(request):
    """Cadastra usuário na base de dados do PFE."""
    if request.method == 'POST':

        if 'email' in request.POST:
            mensagem, codigo = registro_usuario(request)
            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

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
        "organizacoes": Organizacao.objects.all().order_by("nome"),
        "linkedin_length": PFEUser._meta.get_field('linkedin').max_length,
        "email_length": PFEUser._meta.get_field('email').max_length,
    }

    # Passado o nome da organização do parceiro a ser cadastrado
    tipo = request.GET.get('tipo', None)
    if tipo:
        if tipo == "parceiro":
            organizacao_str = request.GET.get('organizacao', None)
            if organizacao_str:
                try:
                    organizacao_id = int(organizacao_str)
                    organizacao_selecionada = Organizacao.objects.get(id=organizacao_id)
                except (ValueError, Organizacao.DoesNotExist):
                    return HttpResponseNotFound('<h1>Organização não encontrado!</h1>')
                context["organizacao_selecionada"] = organizacao_selecionada

        elif tipo == "professor":
            pass
        elif tipo == "estudante":
            pass
        else:
            return HttpResponseNotFound('<h1>Tipo não reconhecido!</h1>')
        context["tipo"] = tipo

    return render(request, 'administracao/cadastra_usuario.html', context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def edita_usuario(request, primarykey):
    """Edita cadastro de usuário na base de dados do PFE."""
    user = get_object_or_404(PFEUser, id=primarykey)

    if request.method == 'POST':

        if 'email' in request.POST:
            mensagem, codigo = registro_usuario(request, user)
            if codigo != 200:
                return HttpResponse(mensagem, status=codigo)

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
        "usuario": user,
        "organizacoes": Organizacao.objects.all(),
        "linkedin_length": PFEUser._meta.get_field('linkedin').max_length,
        "email_length": PFEUser._meta.get_field('email').max_length,
    }

    if user.tipo_de_usuario == 1:
        context["tipo"] = "estudante"
    elif user.tipo_de_usuario == 2:
        context["tipo"] = "professor"
    elif user.tipo_de_usuario == 3:
        context["tipo"] = "parceiro"
        if user.parceiro.organizacao:
            context["organizacao_selecionada"] = user.parceiro.organizacao
    else:
        return HttpResponse("Erro com tipo de usuário", status=401)

    return render(request, 'administracao/cadastra_usuario.html', context)

@login_required
@permission_required('users.altera_professor', raise_exception=True)
def carrega_arquivo(request, dado):
    """Faz o upload de arquivos CSV para o servidor."""
    if dado == "disciplinas":
        resource = DisciplinasResource()
    elif dado == "estudantes":
        resource = EstudantesResource()
    elif dado == "avaliacoes":
        resource = Avaliacoes2Resource()
    else:
        return HttpResponseNotFound('<h1>Tipo de dado não reconhecido!</h1>')

    # https://simpleisbetterthancomplex.com/packages/2016/08/11/django-import-export.html
    if request.method == 'POST':

        dataset = tablib.Dataset()

        if 'arquivo' in request.FILES:
            new_data = request.FILES['arquivo'].readlines()
            if ';' in str(new_data)[:32]:
                return HttpResponseNotFound('<h1>Arquivo de dados possui ponto e vírgula (;) !</h1>')
        else:
            return HttpResponseNotFound('<h1>Arquivo não reconhecido!</h1>')

        entradas = ""
        for i in new_data:
            texto = i.decode("utf-8")
            entradas += re.sub('[^A-Za-z0-9À-ÿ, \r\n@._]+', '', texto)  # Limpa caracteres especiais

        # imported_data = dataset.load(entradas, format='csv')
        dataset.load(entradas, format='csv')
        dataset.insert_col(0, col=lambda row: None, header="id")

        result = resource.import_data(dataset, dry_run=True, raise_errors=True)

        if result.has_errors():
            mensagem = "Erro ao carregar arquivo." + str(result)

            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }

            return render(request, 'generic.html', context=context)

        resource.import_data(dataset, dry_run=False)  # Actually import now
        string_html = "Importado ({0} registros): <br>".format(len(dataset))
        for row_values in dataset:
            string_html += str(row_values) + "<br>"

        context = {
            "area_principal": True,
            "mensagem": string_html,
        }

        return render(request, 'generic.html', context=context)

    context = {
        'campos_permitidos': resource.campos,
    }

    return render(request, 'administracao/import.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def configurar(request):
    """Definir datas do PFE."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == 'POST':

        if "periodo_ano" and "periodo_semestre" in request.POST:
            try:
                
                configuracao.ano = int(request.POST['periodo_ano'])
                configuracao.semestre = int(request.POST['periodo_semestre'])

                configuracao.liberadas_propostas = 'liberadas_propostas' in request.POST
                configuracao.min_props = int(request.POST['min_props'])

                configuracao.prazo_preencher_banca = int(request.POST['prazo_preencher_banca'])

                configuracao.coordenacao = get_object_or_404(Administrador,
                                                             pk=int(request.POST['coordenacao']))

                configuracao.coordenador = request.POST['coordenador']
                if 'assinatura' in request.FILES:
                    assinatura = simple_upload(request.FILES['assinatura'],
                                                path=get_upload_path(configuracao, ""))
                    configuracao.assinatura = assinatura[len(settings.MEDIA_URL):]

                configuracao.save()
                context = {
                    "area_principal": True,
                    "mensagem": "Dados atualizados.",
                }
                return render(request, 'generic.html', context=context)
            except (ValueError, OverflowError, MultiValueDictKeyError):
                return HttpResponse("Algum erro não identificado.", status=401)
        else:
            return HttpResponse("Algum erro ao passar parâmetros.", status=401)
    
    context = {
        "configuracao": configuracao,
        "limite_propostas": get_limite_propostas(configuracao),
        "coord_length": Configuracao._meta.get_field('coordenador').max_length,
        "administradores": Administrador.objects.all(),
    }

    return render(request, 'administracao/configurar.html', context)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def exportar(request):
    """Exporta dados."""
    return render(request, 'administracao/exportar.html')


@login_required
@permission_required('users.altera_professor', raise_exception=True)
def propor(request):
    """Monta grupos de PFE."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre
    ano, semestre = adianta_semestre(ano, semestre)

    otimizar = False
    if request.method == 'POST':
        otimizar = True

    lista_propostas = list(zip(*ordena_propostas(otimizar, ano, semestre)))
    if lista_propostas:
        propostas = lista_propostas[0]
    else:
        propostas = []

    alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
        filter(anoPFE=ano).\
        filter(semestrePFE=semestre).\
        filter(trancado=False).\
        order_by(Lower("user__first_name"), Lower("user__last_name"))
    
    # Calcula média dos CRs
    media_cr = 0
    for aluno in alunos:
        media_cr += aluno.cr
    media_cr /= len(alunos)

    # checa para empresas repetidas, para colocar um número para cada uma
    repetidas = {}
    for proposta in propostas:
        if proposta.organizacao:
            if proposta.organizacao.sigla in repetidas:
                repetidas[proposta.organizacao.sigla] += 1
            else:
                repetidas[proposta.organizacao.sigla] = 0
        else:
            if proposta.nome_organizacao in repetidas:
                repetidas[proposta.nome_organizacao] += 1
            else:
                repetidas[proposta.nome_organizacao] = 0
    repetidas_limpa = {}
    for repetida in repetidas:
        if repetidas[repetida] != 0:  # tira zerados
            repetidas_limpa[repetida] = repetidas[repetida]
    proposta_indice = {}
    for proposta in reversed(propostas):
        if proposta.organizacao:
            if proposta.organizacao.sigla in repetidas_limpa:
                proposta_indice[proposta.id] = \
                    repetidas_limpa[proposta.organizacao.sigla] + 1
                repetidas_limpa[proposta.organizacao.sigla] -= 1
        else:
            if proposta.nome_organizacao in repetidas_limpa:
                proposta_indice[proposta.id] = \
                    repetidas_limpa[proposta.nome_organizacao] + 1
                repetidas_limpa[proposta.nome_organizacao] -= 1

    def pega_opcoes(alunos, propostas):
        opcoes = []
        for aluno in alunos:
            opcoes_aluno = []
            for proposta in propostas:
                opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                if opcao:
                    opcoes_aluno.append(opcao)
                else:
                    opcoes_aluno.append(None)
            opcoes.append(opcoes_aluno)
        return opcoes

    opcoes = pega_opcoes(alunos, propostas)

    def calcula_qtd(opcoes, propostas, alunos):
        finish = True
        qtd = []
        for count, proposta in enumerate(propostas):
            tmp = 0
            for linha in range(len(alunos)):
                pre = alunos[linha].pre_alocacao
                if pre:
                    if pre == proposta:
                        tmp += 1
                else:
                    optmp = Opcao.objects.filter(aluno=alunos[linha], prioridade=1).last()
                    if optmp and optmp.proposta == proposta:
                        tmp += 1
            # Somente grupos de 3 ou 4 ou proposta sem ninguem
            if tmp != 4 or tmp != 3 or tmp != 0:
                finish = False
            qtd.append(tmp)
        return qtd, finish

    qtd, finish = calcula_qtd(opcoes, propostas, alunos)

    user = get_object_or_404(PFEUser, pk=request.user.pk)
    if otimizar:  # Quer dizer que é um POST
        if user.tipo_de_usuario != 4:  # admin
            return HttpResponse("Usuário sem privilégios de administrador.", status=401)

        ordem_propostas = {}
        contador = 0
        for proposta in propostas:
            ordem_propostas[proposta.id] = contador
            contador += 1

        # Removendo propostas com menos de 3 estudantes (prioridade <= 5)
        soma = []
        for count, proposta in enumerate(propostas):
            tmp = 0
            for linha in range(len(alunos)):
                opcao = opcoes[linha][count] 
                if opcao and opcao.prioridade <= 5:
                    tmp += 1
            soma.append(tmp)
        idx = None
        for count, proposta in enumerate(propostas):
            if soma[count] < 3:
                idx = count
                break
        propostas = propostas[:idx]
        for linha in range(len(alunos)):
            opcoes[linha] = opcoes[linha][:idx] 
        soma = soma[:idx]
    
        # Se estudante foi e voltou em um grupo, não mudar mais
        pula_estudante = {}

        # Pre alocando todos nas suas primeiras opções
        for aluno in alunos:
            tmp_prioridade = 9999
            tmp_proposta = None
            for proposta in propostas:
                opcao = Opcao.objects.filter(aluno=aluno, proposta=proposta).last()
                if opcao and opcao.prioridade < tmp_prioridade:
                    tmp_proposta = proposta
                    tmp_prioridade = opcao.prioridade
            if tmp_prioridade < 9999:
                aluno.pre_alocacao = tmp_proposta
                aluno.save()
            else:
                pula_estudante[aluno]=0  # Todas as opções de {aluno} são inviáveis.

        reduz = 1
        contador = 0
        while not finish:
            
            trocou = False

            for count, proposta in enumerate(propostas):
                if qtd[count] == reduz:
                    troca = None
                    for linha in range(len(alunos)):
                        opcao = opcoes[linha][count]
                        if opcao and (opcao.prioridade <= 10) and (opcao.aluno.pre_alocacao != proposta):
                            op_qtd = qtd[ordem_propostas[opcao.aluno.pre_alocacao.id]]
                            if (opcao.aluno not in pula_estudante) or (opcao.prioridade < pula_estudante[opcao.aluno]):
                                if (3 > op_qtd) or (4 < op_qtd):
                                    if (not troca):
                                        troca = opcao
                                    elif (opcao.prioridade < troca.prioridade):
                                        troca = opcao
                                    elif (opcao.prioridade == troca.prioridade) and (opcao.aluno.cr < troca.aluno.cr):
                                        troca = opcao
                    if troca:
                        trocou = True
                        aluno = Aluno.objects.get(pk=troca.aluno.pk)
                        antiga_opcao = Opcao.objects.filter(aluno=aluno, proposta=aluno.pre_alocacao).last()
                        if troca.prioridade < antiga_opcao.prioridade:
                            pula_estudante[aluno]=troca.prioridade
                        Aluno.objects.filter(pk=troca.aluno.pk).update(pre_alocacao=troca.proposta)
                        reduz = 1 # Volta a busca do começo sempre que há alguma troca
                        break

            alunos = Aluno.objects.filter(user__tipo_de_usuario=1).\
                filter(anoPFE=ano).\
                filter(semestrePFE=semestre).\
                filter(trancado=False).\
                order_by(Lower("user__first_name"), Lower("user__last_name"))

            opcoes = pega_opcoes(alunos, propostas)
            qtd, finish = calcula_qtd(opcoes, propostas, alunos)

            if not trocou:
                reduz += 1
                if reduz == 4:
                    break

            # Para evitar travar totalmente
            contador += 1
            if contador > 50:
                #"ESTOUROU"
                break

    estudantes = zip(alunos, opcoes)
    context = {
        'estudantes': estudantes,
        'propostas': propostas,
        'configuracao': configuracao,
        'ano': ano,
        'semestre': semestre,
        'loop_anos': range(2018, configuracao.ano+1),
        'proposta_indice': proposta_indice,
        "qtd": qtd,
        "media_cr": media_cr,
    }

    return render(request,
                  'administracao/propor.html',
                  context)




@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def montar_grupos(request):
    """Montar grupos para projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    ano, semestre = adianta_semestre(ano, semestre)

    propostas = Proposta.objects.filter(ano=ano, semestre=semestre, disponivel=True)

    estudantes = Aluno.objects.filter(trancado=False).\
        filter(anoPFE=ano, semestrePFE=semestre).\
        order_by(Lower("user__first_name"), Lower("user__last_name"))

    opcoes = []
    for estudante in estudantes:
        opcao = Opcao.objects.filter(aluno=estudante).\
                              filter(proposta__ano=ano, proposta__semestre=semestre).\
                              order_by("prioridade")
        opcoes.append(opcao)

        # Caso haja um pré-alocação de anos anteriores, limpar a pré-alocação
        if estudante.pre_alocacao and estudante.pre_alocacao not in propostas:
            estudante.pre_alocacao = None

    estudantes_opcoes = zip(estudantes, opcoes)

    # Checa se usuário é administrador ou professor
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    mensagem = ""

    if request.method == 'POST' and user and user.tipo_de_usuario == 4:  # admin

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
                if alocados:  # pelo menos um estudante no projeto
                    try:
                        projeto = Projeto.objects.get(proposta=proposta, avancado=None)
                    except Projeto.DoesNotExist:
                        projeto = Projeto.create(proposta)

                    if not projeto.titulo:
                        projeto.titulo = proposta.titulo

                    if not projeto.descricao:
                        projeto.descricao = proposta.descricao

                    if not projeto.organizacao:
                        projeto.organizacao = proposta.organizacao

                    # projeto.avancado = None

                    projeto.ano = proposta.ano
                    projeto.semestre = proposta.semestre

                    projeto.save()

                    alocacoes = Alocacao.objects.filter(projeto=projeto)
                    for alocacao in alocacoes:  # Apaga todas alocacoes que não tiverem nota
                        avals = list(Avaliacao2.objects.filter(alocacao=alocacao))
                        if not avals:
                            alocacao.delete()
                        else:
                            mensagem += "- "+str(alocacao.aluno)+"\n"

                    for alocado in alocados:  # alocando estudantes no projeto
                        alocacao = Alocacao.create(alocado, projeto)
                        alocacao.save()

                else:
                    projetos = Projeto.objects.filter(proposta=proposta, avancado=None)
                    if not projetos:
                        continue

                    for projeto in projetos:
                        alocacoes = Alocacao.objects.filter(projeto=projeto)
                        for alocacao in alocacoes:  # Apaga todas alocacoes que não tiverem nota
                            alocacao.delete()

                        projeto.delete()

            if mensagem:
                request.session['mensagem'] = 'Estudantes possuiam alocações com notas:\n'
                request.session['mensagem'] += mensagem

            return redirect('/administracao/selecionar_orientadores/')

    if user and user.tipo_de_usuario != 4:  # admin
        mensagem = "Sua conta não é de administrador, "
        mensagem += "você pode mexer na tela, contudo suas modificações não serão salvas."

    context = {
        'mensagem': mensagem,
        'configuracao': configuracao,
        'propostas': propostas,
        'estudantes_opcoes': estudantes_opcoes,
    }

    return render(request, 'administracao/montar_grupos.html', context=context)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def selecionar_orientadores(request):
    """Selecionar Orientadores para os Projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre

    mensagem = ""

    # Bloqueando visualização de projetos para estudantes
    mensagem += "A visualização de projetos pelos novos alunos está bloqueada.<br>"
    mensagem += "Para desbloquear mova para o próximo semestre na área de Configuração do PFE.<br>"
    mensagem += "[Área Administrativa > Configurar.]<br>"

    if 'mensagem' in request.session:
        mensagem += request.session['mensagem']

    # Vai para próximo semestre
    ano, semestre = adianta_semestre(ano, semestre)

    projetos = Projeto.objects.filter(ano=ano, semestre=semestre)

    professores = PFEUser.objects.filter(tipo_de_usuario=2)  # (2, 'professor')
    administradores = PFEUser.objects.filter(tipo_de_usuario=4)  # (4, 'administrador')
    orientadores = (professores | administradores).order_by(Lower("first_name"), Lower("last_name"))

    # Checa se usuário é administrador ou professor
    user = get_object_or_404(PFEUser, pk=request.user.pk)
    # try:
    #     user = PFEUser.objects.get(pk=request.user.pk)
    # except PFEUser.DoesNotExist:
    #     return HttpResponse("Usuário não encontrado.", status=401)

    if user and user.tipo_de_usuario != 4:  # admin
        mensagem = "Sua conta não é de administrador, "
        mensagem += "você pode mexer na tela, contudo suas modificações não serão salvas."

    context = {
        'mensagem': mensagem,
        'projetos': projetos,
        'orientadores': orientadores,
    }

    return render(request, 'administracao/selecionar_orientadores.html', context=context)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def servico(request):
    """Caso servidor esteja em manutenção."""
    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        if 'manutencao' in check_values:
            settings.MAINTENANCE_MODE = 1
        else:
            settings.MAINTENANCE_MODE = 0
        return redirect('/administracao')

    context = {'manutencao': settings.MAINTENANCE_MODE, }
    return render(request, 'administracao/servico.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def pre_alocar_estudante(request):
    """Ajax para pre-alocar estudates em propostas."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    if user.tipo_de_usuario == 4:  # admin

        # Código a seguir não estritamente necessário mas pode deixar mais seguro
        administrador = get_object_or_404(Administrador, pk=request.user.administrador.pk)

        if not administrador:
            return HttpResponse("Administrador não encontrado.", status=401)

        estudante = request.GET.get('estudante', None)
        estudante_id = int(estudante[len("estudante"):])

        proposta = request.GET.get('proposta', None)
        proposta_id = int(proposta[len("proposta"):])

        configuracao = get_object_or_404(Configuracao)
        ano = configuracao.ano
        semestre = configuracao.semestre

        # Vai para próximo semestre
        ano, semestre = adianta_semestre(ano, semestre)

        proposta = get_object_or_404(Proposta, id=proposta_id)

        estudante = get_object_or_404(Aluno, id=estudante_id)
        estudante.pre_alocacao = proposta
        estudante.save()

        data = {
            'atualizado': True,
        }

    elif user.tipo_de_usuario == 2:  # professor

        # atualizações não serão salvas

        data = {
            'atualizado': False,
        }

    else:
        return HttpResponseNotFound('<h1>Usuário sem privilérios!</h1>')

    return JsonResponse(data)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', raise_exception=True)
def definir_orientador(request):
    """Ajax para definir orientadores de projetos."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)
    # try:
    #     user = PFEUser.objects.get(pk=request.user.pk)
    # except PFEUser.DoesNotExist:
    #     return HttpResponse("Usuário não encontrado.", status=401)

    if user.tipo_de_usuario == 4:  # admin

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
            orientador = get_object_or_404(Professor, user_id=orientador_id)
            # try:
            #     orientador = Professor.objects.get(user_id=orientador_id)
            # except Professor.DoesNotExist:
            #     return HttpResponseNotFound('<h1>Orientador não encontrado!</h1>')
        else:
            orientador = None

        projeto = get_object_or_404(Projeto, id=projeto_id)
        projeto.orientador = orientador
        projeto.save()

        data = {
            'atualizado': True,
        }

    elif user.tipo_de_usuario == 2:  # professor

        # atualizações não serão salvas
        data = {
            'atualizado': False,
        }

    else:
        return HttpResponseNotFound('<h1>Usuário sem privilérios!</h1>')

    return JsonResponse(data)



@login_required
@transaction.atomic
@permission_required("users.altera_professor", raise_exception=True)
def excluir_disciplina(request):
    """Remove Disciplina Recomendada."""
    
    if request.is_ajax() and 'disciplina_id' in request.POST:

        disciplina_id = int(request.POST['disciplina_id'])

        instance = Disciplina.objects.get(id=disciplina_id)
        instance.delete()

        data = {
            'atualizado': True,
        }

        return JsonResponse(data)

    return HttpResponseNotFound('Requisição errada')


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def export(request, modelo, formato):
    """Exporta dados direto para o navegador nos formatos CSV, XLS e JSON."""
    if modelo == "projetos":
        resource = ProjetosResource()
    elif modelo == "organizacoes":
        resource = OrganizacoesResource()
    elif modelo == "opcoes":
        resource = OpcoesResource()
    elif modelo == "avaliacoes":
        resource = Avaliacoes2Resource()
    elif modelo == "usuarios":
        resource = UsuariosResource()
    elif modelo == "estudantes":
        resource = EstudantesResource()
    elif modelo == "professores":
        resource = ProfessoresResource()
    elif modelo == "parceiros":
        resource = ParceirosResource()
    elif modelo == "configuracao":
        resource = ConfiguracaoResource()
    elif modelo == "feedbacks":
        resource = FeedbacksResource()
    # elif modelo == "comite":
    #     resource = ComiteResource()
    else:
        mensagem = "Chamada irregular : Base de dados desconhecida = " + modelo
        context = {
            "area_principal": True,
            "mensagem": mensagem,
        }
        return render(request, 'generic.html', context=context)

    dataset = resource.export()

    databook = tablib.Databook()

    databook.add_sheet(dataset)

    if formato in ("xls", "xlsx"):
        response = HttpResponse(databook.xlsx, content_type='application/ms-excel')
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
    databook = tablib.Databook()

    data_projetos = ProjetosResource().export()
    data_projetos.title = "Projetos"
    databook.add_sheet(data_projetos)

    data_organizacoes = OrganizacoesResource().export()
    data_organizacoes.title = "Organizacoes"
    databook.add_sheet(data_organizacoes)

    data_opcoes = OpcoesResource().export()
    data_opcoes.title = "Opcoes"
    databook.add_sheet(data_opcoes)

    data_avaliacoes = Avaliacoes2Resource().export()
    data_avaliacoes.title = "Avaliações"
    databook.add_sheet(data_avaliacoes)

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
@permission_required("users.altera_professor", raise_exception=True)
def backup(request, formato):
    """Gera um backup de tudo."""
    databook = create_backup()
    if formato in ("xls", "xlsx"):
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
@permission_required("users.altera_professor", raise_exception=True)
def email_backup(request):
    """Envia um e-mail com os backups."""
    subject = 'BACKUP PFE'
    message = "Backup PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com', 'lpsoares@gmail.com', ]
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
@permission_required("users.altera_professor", raise_exception=True)
def relatorio(request, modelo, formato):
    """Gera relatorios em html e PDF."""
    configuracao = get_object_or_404(Configuracao)
    context = {'configuracao': configuracao}

    if modelo == "propostas":
        context['propostas'] = Proposta.objects.all()
        arquivo = "administracao/relatorio_propostas.html"

    elif modelo == "projetos":
        context['projetos'] = Projeto.objects.all()
        arquivo = "administracao/relatorio_projetos.html"

    elif modelo == "alunos":
        context['alunos'] = Aluno.objects.all().filter(user__tipo_de_usuario=1).\
                                                filter(anoPFE=configuracao.ano).\
                                                filter(semestrePFE=configuracao.semestre)
        arquivo = "administracao/relatorio_alunos.html"

    elif modelo == "feedbacks":
        context['feedbacks'] = Feedback.objects.all()
        arquivo = "administracao/relatorio_feedbacks.html"

    else:
        context = {
            "area_principal": True,
            "mensagem": "Chamada irregular : Base de dados desconhecida = " + modelo,
        }
        return render(request, 'generic.html', context=context)

    if formato in ("html", "HTML"):
        return render(request, arquivo, context)

    if formato in ("pdf", "PDF"):
        pdf = render_to_pdf(arquivo, context)
        return HttpResponse(pdf.getvalue(), content_type='application/pdf')

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", raise_exception=True)
def relatorio_backup(request):
    """Gera um relatório de backup de segurança."""
    subject = 'RELATÓRIOS PFE'
    message = "Relatórios PFE"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['pfeinsper@gmail.com', 'lpsoares@gmail.com', ]
    mail = EmailMessage(subject, message, email_from, recipient_list)

    configuracao = get_object_or_404(Configuracao)

    context = {
        'projetos': Projeto.objects.all(),
        'alunos': Aluno.objects.filter(user__tipo_de_usuario=1).\
          filter(anoPFE=configuracao.ano).\
          filter(semestrePFE=configuracao.semestre),
        'configuracao': configuracao,
    }

    pdf_proj = render_to_pdf('administracao/relatorio_projetos.html', context)
    pdf_alun = render_to_pdf('administracao/relatorio_alunos.html', context)
    mail.attach("projetos.pdf", pdf_proj.getvalue(), 'application/pdf')
    mail.attach("alunos.pdf", pdf_alun.getvalue(), 'application/pdf')
    mail.send()

    context = {
        "area_principal": True,
        "mensagem": "E-mail enviado.",
    }

    return render(request, 'generic.html', context=context)



@login_required
@permission_required('users.altera_professor', raise_exception=True)
def logs(request):
    """Alguns logs de Admin."""
    v = usuario_sem_acesso(request, (4,)) # Soh Adm
    if v: return v  # Prof, Adm

    message = ""
    for log in LogEntry.objects.all():
        message += str(log)+"<br>\n"
    return HttpResponse(message)


@login_required
@permission_required('users.altera_professor', raise_exception=True)
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

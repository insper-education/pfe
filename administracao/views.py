#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia.

Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import re           # regular expression (para o import)
import tablib
import dateutil.parser

from django.conf import settings
# from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models.functions import Lower
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError

from documentos.support import render_to_pdf

from projetos.models import Configuracao, Organizacao, Proposta, Projeto, Banca
from projetos.models import Avaliacao2, get_upload_path, Feedback

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

from users.support import get_edicoes
from users.support import adianta_semestre


@login_required
@permission_required("users.altera_professor", login_url='/')
def index_administracao(request):
    """Mostra página principal para administração do sistema."""
    return render(request, 'administracao/index_admin.html')


@login_required
@permission_required('users.altera_professor', login_url='/')
def index_carregar(request):
    """Para carregar dados de arquivos para o servidor."""
    user = get_object_or_404(PFEUser, pk=request.user.pk)

    if user:
        if user.tipo_de_usuario != 4:  # não é admin
            mensagem = "Você não tem privilégios de administrador!"
            context = {
                "area_principal": True,
                "mensagem": mensagem,
            }
            return render(request, 'generic.html', context=context)

    return render(request, 'administracao/carregar.html')


@login_required
@permission_required("users.altera_professor", login_url='/')
def emails(request):
    """Gera listas de emails, com alunos, professores, parceiros, etc."""
    membros_comite = PFEUser.objects.filter(membro_comite=True)
    lista_todos_alunos = Aluno.objects.filter(trancado=False).\
        filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
    lista_todos_professores = Professor.objects.all()
    lista_todos_parceiros = Parceiro.objects.all()
 
    edicoes, _, _ = get_edicoes(Aluno)

    configuracao = get_object_or_404(Configuracao)
    atual = str(configuracao.ano)+"."+str(configuracao.semestre)

    coordenacao = configuracao.coordenacao

    context = {
        "membros_comite": membros_comite,
        "todos_alunos": lista_todos_alunos,
        "todos_professores": lista_todos_professores,
        "todos_parceiros": lista_todos_parceiros,
        "edicoes": edicoes,
        "atual": atual,
        "coordenacao": coordenacao,
    }

    return render(request, 'administracao/emails.html', context=context)



@login_required
@permission_required("users.altera_professor", login_url='/')
def emails_semestre(request):
    """Gera listas de emails por semestre."""
    if request.is_ajax():
        if 'edicao' in request.POST:
            ano, semestre = request.POST['edicao'].split('.')

            estudantes = []  # Alunos do semestre
            orientadores = []  # Orientadores por semestre
            organizacoes = []  # Controla as organizações participantes p/semestre
            parceiros = []
            membros_bancas = []  # Membros das bancas

            for projeto in Projeto.objects.filter(ano=ano).filter(semestre=semestre):
                if Aluno.objects.filter(alocacao__projeto=projeto):  # checa se há alunos
                    estudantes += Aluno.objects.filter(trancado=False).\
                        filter(alocacao__projeto=projeto).\
                        filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

                if projeto.orientador and (projeto.orientador not in orientadores):
                    orientadores.append(projeto.orientador)  # Junta orientadores do semestre

                if projeto.organizacao not in organizacoes:
                    organizacoes.append(projeto.organizacao)  # Junta organizações do semestre

                # Parceiros de todas as organizações parceiras
                parceiros = Parceiro.objects.filter(organizacao__in=organizacoes,
                                                    user__is_active=True)
                # IDEAL = conexoes = Conexao.objects.filter(projeto=projeto)

                bancas = Banca.objects.filter(projeto=projeto)
                for banca in bancas:
                    if banca.membro1 and (banca.membro1 not in membros_bancas):
                        membros_bancas.append(banca.membro1)
                    if banca.membro2 and (banca.membro2 not in membros_bancas):
                        membros_bancas.append(banca.membro2)
                    if banca.membro3 and (banca.membro3 not in membros_bancas):
                        membros_bancas.append(banca.membro3)

            # Cria listas para estudantes que ainda não estão em projetos
            estudantes_sem_projeto = Aluno.objects.filter(trancado=False).\
                filter(anoPFE=ano).\
                filter(semestrePFE=semestre).\
                filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
            for estudante in estudantes_sem_projeto:
                if estudante not in estudantes:
                    estudantes.append(estudante)


            data = {}  # Dicionario com as pessoas do projeto
            data["Estudantes"] = []
            for i in estudantes:
                data["Estudantes"].append([i.user.first_name, i.user.last_name, i.user.email])

            data["Orientadores"] = []
            for i in orientadores:
                data["Orientadores"].append([i.user.first_name, i.user.last_name, i.user.email])

            data["Parceiros"] = []
            for i in parceiros:
                data["Parceiros"].append([i.user.first_name, i.user.last_name, i.user.email])

            data["Bancas"] = []
            for i in membros_bancas:
                data["Bancas"].append([i.first_name, i.last_name, i.email])

            return JsonResponse(data)

    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@permission_required("users.altera_professor", login_url='/')
def emails_projetos(request):
    """Gera listas de emails, com alunos, professores, parceiros, etc."""
    if request.is_ajax():
        if 'edicao' in request.POST:
            ano, semestre = request.POST['edicao'].split('.')
            projetos = Projeto.objects.filter(ano=ano).filter(semestre=semestre)
            context = {
                'projetos': projetos,
            }
            return render(request, 'administracao/emails_projetos.html', context=context)
    return HttpResponse("Algum erro não identificado.", status=401)


@login_required
@transaction.atomic
@permission_required("users.altera_professor", login_url='/')
def cadastrar_organizacao(request):
    """Cadastra Organização na base de dados do PFE."""
    if request.method == 'POST':

        if 'nome' in request.POST and 'sigla' in request.POST:

            organizacao = Organizacao.create()

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

    return render(request, 'administracao/cadastra_organizacao.html')



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
        if curso == "computacao":
            estudante.curso = 'C'   # ('C', 'Computação'),
        elif curso == "mecanica":
            estudante.curso = 'M'   # ('M', 'Mecânica'),
        elif curso == "mecatronica":
            estudante.curso = 'X'   # ('X', 'Mecatrônica'),
        else:
            estudante.curso = None
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
            estudante.cr = 0
            mensagem += "Erro na inclusão do CR.<br>"

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
@permission_required("users.altera_professor", login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
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
@permission_required('users.altera_professor', login_url='/')
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
@permission_required('users.altera_professor', login_url='/')
def configurar(request):
    """Definir datas do PFE."""
    configuracao = get_object_or_404(Configuracao)

    if request.method == 'POST':

        if "limite_propostas" and "periodo_ano" and "periodo_semestre" in request.POST:
            try:
                configuracao.prazo = dateutil.parser.parse(request.POST['limite_propostas'])
                configuracao.ano = int(request.POST['periodo_ano'])
                configuracao.semestre = int(request.POST['periodo_semestre'])

                configuracao.liberados_projetos = 'liberados_projetos' in request.POST
                configuracao.liberadas_propostas = 'liberadas_propostas' in request.POST

                configuracao.save()
                context = {
                    "area_principal": True,
                    "mensagem": "Datas atualizadas.",
                }
                return render(request, 'generic.html', context=context)
            except (ValueError, OverflowError, MultiValueDictKeyError):
                return HttpResponse("Algum erro não identificado.", status=401)
        else:
            return HttpResponse("Algum erro não identificado.", status=401)

    context = {
        'configuracao': configuracao,
    }

    return render(request, 'administracao/configurar.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def exportar(request):
    """Exporta dados."""
    return render(request, 'administracao/exportar.html')


@login_required
@permission_required('users.altera_professor', login_url='/')
def propor(request):
    """Monta grupos de PFE."""
    # Deprecated
    return HttpResponseNotFound('<h1>Sistema de propor projetos está obsoleto.</h1>')


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
def selecionar_orientadores(request):
    """Selecionar Orientadores para os Projetos."""
    configuracao = get_object_or_404(Configuracao)
    ano = configuracao.ano
    semestre = configuracao.semestre
    # try:
    #     configuracao = Configuracao.objects.get()
    #     ano = configuracao.ano
    #     semestre = configuracao.semestre
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

    mensagem = ""

    if 'mensagem' in request.session:
        mensagem = request.session['mensagem']

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
@permission_required("users.altera_professor", login_url='/')
def servico(request):
    """Caso servidor esteja em manutenção."""
    configuracao = get_object_or_404(Configuracao)
    # try:
    #     configuracao = Configuracao.objects.get()
    # except Configuracao.DoesNotExist:
    #     return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        configuracao.manutencao = 'manutencao' in check_values
        configuracao.save()
        return redirect('/administracao')

    context = {'manutencao': configuracao.manutencao, }

    return render(request, 'administracao/servico.html', context)


@login_required
@transaction.atomic
@permission_required('users.altera_professor', login_url='/')
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
@permission_required('users.altera_professor', login_url='/')
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
        # try:
        #     projeto = Projeto.objects.get(id=projeto_id)
        #     projeto.orientador = orientador
        #     projeto.save()
        # except Projeto.DoesNotExist:
        #     return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

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
@permission_required("users.altera_professor", login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
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
@permission_required("users.altera_professor", login_url='/')
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

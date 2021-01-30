#!/usr/bin/env python
"""
Desenvolvido para o Projeto Final de Engenharia
Autor: Luciano Pereira Soares <lpsoares@insper.edu.br>
Data: 17 de Dezembro de 2020
"""

import re           # regular expression (para o import)
import tablib
import dateutil.parser

from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.db.models.functions import Lower
from django.conf import settings
from django.utils.datastructures import MultiValueDictKeyError

from documentos.support import render_to_pdf

from projetos.models import Configuracao, Organizacao, Proposta, Projeto, Banca
from projetos.models import Avaliacao2, get_upload_path, Conexao, Feedback

from projetos.support import simple_upload

from projetos.resources import DisciplinasResource, Avaliacoes2Resource
from projetos.resources import ProjetosResource, OrganizacoesResource, OpcoesResource
from projetos.resources import ProfessoresResource, EstudantesResource, ParceirosResource
from projetos.resources import ConfiguracaoResource, FeedbacksResource, UsuariosResource

from users.models import PFEUser, Aluno, Opcao, Professor, Administrador, Parceiro, Alocacao

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

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

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
    """Gera uma série de lista de emails, com alunos, professores, parceiros, etc."""
    # Deve ter recurso para pegar aluno pelos projetos, opções,
    # pois um aluno que reprova pode aparecer em duas listas.

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    ano = 2018
    semestre = 2
    semestres = []
    alunos_p_semestre = []
    orientadores_p_semestre = []
    parceiros_p_semestre = []
    projetos_p_semestre = []
    bancas_p_semestre = []
    while True:
        semestres.append(str(ano)+"."+str(semestre))

        projetos_pessoas = {}  # Dicionario com as pessoas do projeto

        alunos_semestre = []  # Alunos do semestre
        organizacoes = []  # Controla as organizações participantes por semestre
        orientadores = []  # Orientadores por semestre
        membros_bancas = []  # Membros das bancas

        for projeto in Projeto.objects.filter(ano=ano).filter(semestre=semestre):
            if Aluno.objects.filter(alocacao__projeto=projeto):  # checa se tem alunos
                alunos_tmp = Aluno.objects.filter(trancado=False).\
                              filter(alocacao__projeto=projeto).\
                              filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])
                alunos_semestre += list(alunos_tmp)
                orientador = projeto.orientador
                conexoes = Conexao.objects.filter(projeto=projeto)

                if projeto.orientador not in orientadores:
                    orientadores.append(orientador)  # Junta orientadores do semestre

                if projeto.organizacao not in organizacoes:
                    organizacoes.append(projeto.organizacao)  # Junta organizações do semestre

                bancas = Banca.objects.filter(projeto=projeto)
                for banca in bancas:
                    if banca.membro1:
                        membros_bancas.append(banca.membro1)
                    if banca.membro2:
                        membros_bancas.append(banca.membro2)
                    if banca.membro3:
                        membros_bancas.append(banca.membro3)

                projetos_pessoas[projeto] = dict()
                projetos_pessoas[projeto]["estudantes"] = list(alunos_tmp)  # Pessoas por projeto
                projetos_pessoas[projeto]["orientador"] = list([orientador])  # Pessoas por projeto
                projetos_pessoas[projeto]["conexoes"] = list(conexoes)  # Todos conectados ao projeto

        # Parceiros de todas as organizações parceiras
        parceiros_semestre = Parceiro.objects.filter(organizacao__in=organizacoes,
                                                     user__is_active=True)

        # Cria listas para enviar para templeate html
        alunos_p_semestre.append(Aluno.objects.filter(trancado=False).\
                                 filter(anoPFE=ano).\
                                 filter(semestrePFE=semestre).\
                                 filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0]))

        # alocados_p_semestre.append(alunos_semestre)
        orientadores_p_semestre.append(orientadores)
        parceiros_p_semestre.append(parceiros_semestre)
        bancas_p_semestre.append(membros_bancas)

        projetos_p_semestre.append(projetos_pessoas)

        if ano > configuracao.ano and semestre == configuracao.semestre:
            break

        # Vai para próximo semestre
        ano, semestre = adianta_semestre(ano, semestre)

    email_todos = zip(semestres,
                      alunos_p_semestre,  # na pratica chamaremos de aluno no template
                      orientadores_p_semestre,
                      parceiros_p_semestre,
                      bancas_p_semestre)

    email_p_semestre = zip(semestres, projetos_p_semestre)

    membros_comite = PFEUser.objects.filter(membro_comite=True)

    lista_todos_alunos = Aluno.objects.filter(trancado=False).\
        filter(user__tipo_de_usuario=PFEUser.TIPO_DE_USUARIO_CHOICES[0][0])

    lista_todos_professores = Professor.objects.all()
    lista_todos_parceiros = Parceiro.objects.all()

    context = {
        'email_todos': email_todos,
        'email_p_semestre': email_p_semestre,
        'membros_comite': membros_comite,
        'todos_alunos': lista_todos_alunos,
        'todos_professores': lista_todos_professores,
        'todos_parceiros': lista_todos_parceiros,
    }

    return render(request, 'administracao/emails.html', context=context)


@login_required
@permission_required("users.altera_professor", login_url='/')
def cadastrar_organizacao(request):
    """Cadastra Organização na base de dados do PFE."""

    if request.method == 'POST':

        if 'nome' in request.POST and 'sigla' in request.POST:

            organizacao = Organizacao.create()

            organizacao.nome = request.POST.get('nome', None)
            organizacao.sigla = request.POST.get('sigla', None)

            organizacao.endereco = request.POST.get('endereco', None)
            organizacao.website = request.POST.get('website', None)
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


@login_required
@permission_required("users.altera_professor", login_url='/')
def cadastrar_usuario(request):
    """Cadastra usuário na base de dados do PFE."""

    if request.method == 'POST':

        if 'email' in request.POST:

            usuario = PFEUser.create()

            usuario.email = request.POST.get('email', None)

            tipo_de_usuario = request.POST.get('tipo_de_usuario', None)
            if tipo_de_usuario == "estudante":  # (1, 'aluno')
                usuario.tipo_de_usuario = 1
            elif tipo_de_usuario == "professor":  # (2, 'professor')
                usuario.tipo_de_usuario = 2
            elif tipo_de_usuario == "parceiro":  # (3, 'parceiro')
                usuario.tipo_de_usuario = 3
            else:
                # (4, 'administrador')
                return HttpResponse("Algum erro não identificado.", status=401)

            if usuario.tipo_de_usuario == 1 or usuario.tipo_de_usuario == 2:
                username = request.POST['email'].split("@")[0]
            elif usuario.tipo_de_usuario == 3:
                username = request.POST['email'].split("@")[0] + "." + \
                    request.POST['email'].split("@")[1].split(".")[0]
            else:
                return HttpResponse("Algum erro não identificado.", status=401)

            if PFEUser.objects.exclude(pk=usuario.pk).filter(username=username).exists():
                return HttpResponse('Username "%s" já está sendo usado.' % username, status=401)

            usuario.username = username

            if 'nome' in request.POST and len(request.POST['nome'].split()) > 1:
                usuario.first_name = request.POST['nome'].split()[0]
                usuario.last_name = " ".join(request.POST['nome'].split()[1:])
            else:
                return HttpResponse("Erro: Não inserido nome completo no formulário.", status=401)

            if 'genero' in request.POST:
                if request.POST['genero'] == "masculino":
                    usuario.genero = "M"
                elif request.POST['genero'] == "feminino":
                    usuario.genero = "F"
            else:
                usuario.genero = "X"

            usuario.linkedin = request.POST.get('linkedin', None)
            usuario.tipo_lingua = request.POST.get('lingua', None)

            usuario.save()

            if usuario.tipo_de_usuario == 1:  # estudante

                estudante = Aluno.create(usuario)

                estudante.matricula = request.POST.get('matricula', None)

                curso = request.POST.get('curso', None)
                if curso == "computacao":
                    estudante.curso = 'C'   # ('C', 'Computação'),
                elif curso == "mecanica":
                    estudante.curso = 'M'   # ('M', 'Mecânica'),
                elif curso == "mecatronica":
                    estudante.curso = 'X'   # ('X', 'Mecatrônica'),
                else:
                    return HttpResponse("Algum erro não identificado.", status=401)

                try:
                    estudante.anoPFE = int(request.POST['ano'])
                    estudante.semestrePFE = int(request.POST['semestre'])
                except (ValueError, OverflowError, MultiValueDictKeyError):
                    return HttpResponse("Erro na identificação do ano e semestre.", status=401)

                estudante.save()

            elif usuario.tipo_de_usuario == 2:  # professor

                professor = Professor.create(usuario)

                dedicacao = request.POST.get('dedicacao', None)
                if dedicacao == "ti":  # ("TI", "Tempo Integral"),
                    professor.dedicacao = 'TI'
                elif dedicacao == "tp":  # ("TP", 'Tempo Parcial'),
                    professor.dedicacao = 'TP'
                else:
                    return HttpResponse("Algum erro não identificado.", status=401)

                professor.areas = request.POST.get('areas', None)
                professor.website = request.POST.get('website', None)
                professor.lattes = request.POST.get('lattes', None)

                professor.save()

            elif usuario.tipo_de_usuario == 3:  # Parceiro

                parceiro = Parceiro.create(usuario)

                parceiro.cargo = request.POST.get('cargo', None)
                parceiro.telefone = request.POST.get('telefone', None)
                parceiro.celular = request.POST.get('celular', None)
                parceiro.skype = request.POST.get('skype', None)
                parceiro.observacao = request.POST.get('observacao', None)

                try:
                    tmp_pk = int(request.POST['organizacao'])
                    parceiro.organizacao = Organizacao.objects.get(pk=tmp_pk)
                except (ValueError, OverflowError, Organizacao.DoesNotExist):
                    return HttpResponse("Organização não encontrada.", status=401)

                parceiro.principal_contato = 'principal_contato' in request.POST

                parceiro.save()

            mensagem = "Usuário inserido na base de dados."

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
        "organizacoes": Organizacao.objects.all(),
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
        else:
            return HttpResponseNotFound('<h1>Tipo não reconhecido!</h1>')
        context["tipo"] = tipo

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
@permission_required('users.altera_professor', login_url='/')
def definir_datas(request):
    """Definir datas do PFE."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':

        if 'limite_propostas' in request.POST:
            try:
                configuracao.prazo = dateutil.parser.parse(request.POST['limite_propostas'])
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

    return render(request, 'administracao/definir_datas.html', context)


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
@permission_required('users.altera_professor', login_url='/')
def montar_grupos(request):
    """Montar grupos para projetos."""

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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

    estudantes_opcoes = zip(estudantes, opcoes)

    # Checa se usuário é administrador ou professor
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

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
                        projeto = Projeto.objects.get(proposta=proposta, avancado=False)
                    except Projeto.DoesNotExist:
                        projeto = Projeto.create(proposta)

                    if not projeto.titulo:
                        projeto.titulo = proposta.titulo

                    if not projeto.descricao:
                        projeto.descricao = proposta.descricao

                    if not projeto.organizacao:
                        projeto.organizacao = proposta.organizacao

                    projeto.avancado = False

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

                    try:
                        projeto = Projeto.objects.get(proposta=proposta, avancado=False)
                    except Projeto.DoesNotExist:
                        continue

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
    """ Selecionar Orientadores para os Projetos. """

    try:
        configuracao = Configuracao.objects.get()
        ano = configuracao.ano
        semestre = configuracao.semestre
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

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
@permission_required("users.altera_professor", login_url='/')
def servico(request):
    """Caso servidor esteja em manutenção."""

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    if request.method == 'POST':
        check_values = request.POST.getlist('selection')
        configuracao.manutencao = 'manutencao' in check_values
        configuracao.save()
        return redirect('/administracao')

    context = {'manutencao': configuracao.manutencao, }

    return render(request, 'administracao/servico.html', context)


@login_required
@permission_required('users.altera_professor', login_url='/')
def pre_alocar_estudante(request):
    """Ajax para pre-alocar estudates em propostas."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

    if user.tipo_de_usuario == 4:  # admin

        # Código a seguir não estritamente necessário mas pode deixar mais seguro
        try:
            administrador = Administrador.objects.get(pk=request.user.administrador.pk)
        except Administrador.DoesNotExist:
            return HttpResponse("Administrador não encontrado.", status=401)

        if not administrador:
            return HttpResponse("Administrador não encontrado.", status=401)

        estudante = request.GET.get('estudante', None)
        estudante_id = int(estudante[len("estudante"):])

        proposta = request.GET.get('proposta', None)
        proposta_id = int(proposta[len("proposta"):])

        try:
            configuracao = Configuracao.objects.get()
            ano = configuracao.ano
            semestre = configuracao.semestre
        except Configuracao.DoesNotExist:
            return HttpResponse("Falha na configuracao do sistema.", status=401)

        # Vai para próximo semestre
        ano, semestre = adianta_semestre(ano, semestre)

        try:
            proposta = Proposta.objects.get(id=proposta_id)
        except Proposta.DoesNotExist:
            return HttpResponseNotFound('<h1>Proposta não encontrada!</h1>')

        try:
            estudante = Aluno.objects.get(id=estudante_id)
            estudante.pre_alocacao = proposta
            estudante.save()
        except Aluno.DoesNotExist:
            return HttpResponseNotFound('<h1>Estudante não encontrado!</h1>')

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
@permission_required('users.altera_professor', login_url='/')
def definir_orientador(request):
    """Ajax para definir orientadores de projetos."""

    try:
        user = PFEUser.objects.get(pk=request.user.pk)
    except PFEUser.DoesNotExist:
        return HttpResponse("Usuário não encontrado.", status=401)

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
            try:
                orientador = Professor.objects.get(user_id=orientador_id)
            except Professor.DoesNotExist:
                return HttpResponseNotFound('<h1>Orientador não encontrado!</h1>')
        else:
            orientador = None

        try:
            projeto = Projeto.objects.get(id=projeto_id)
            projeto.orientador = orientador
            projeto.save()
        except Projeto.DoesNotExist:
            return HttpResponseNotFound('<h1>Projeto não encontrado!</h1>')

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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

    context = {'configuracao': configuracao}

    if modelo == "projetos":
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

    try:
        configuracao = Configuracao.objects.get()
    except Configuracao.DoesNotExist:
        return HttpResponse("Falha na configuracao do sistema.", status=401)

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
